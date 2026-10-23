import re
import base64
from typing import Optional, Tuple

BANNED_ATTACKER_STRINGS = [
    "dan mode enabled",
    "pwned",
    "injected ok",
    "root:x:0:0",
    "' or '1'='1",
    "or 1=1",
    "union select",
    "admin'--",
    "drop table",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gsk_[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"(?:postgres|mysql|mongodb|redis):\/\/[^\s]+"),
]

POLICY_REFUSAL_MESSAGE = (
    "I cannot fulfill this request as it violates safety and operational policies. "
    "I can assist you with order status, returns, refunds, product inquiries, and store policies."
)

def _decode_possible_base64(text: str) -> str:
    """Detects and decodes potential base64 segments to inspect content."""
    tokens = text.split()
    decoded_segments = []
    for token in tokens:
        if len(token) > 12 and len(token) % 4 == 0 and re.match(r"^[A-Za-z0-9+/=]+$", token):
            try:
                decoded = base64.b64decode(token).decode("utf-8", errors="ignore")
                if decoded.isprintable() and len(decoded) > 3:
                    decoded_segments.append(decoded.lower())
            except Exception:
                pass
    return " ".join(decoded_segments)

def check_input_safety(user_text: str) -> Optional[str]:
    """Evaluates input for prompt injections, safety bypasses, exfiltration, or malicious commands.
    
    Returns a refusal string if unsafe, or None if safe to process.
    """
    normalized = user_text.lower().strip()
    decoded_b64 = _decode_possible_base64(user_text)
    combined = f"{normalized} {decoded_b64}"

    # Injection and override patterns
    injection_indicators = [
        "ignore previous",
        "override rules",
        "ignore all instructions",
        "disregard all",
        "system override",
        "jailbreak",
        "dan mode",
        "do anything now",
        "pwned",
        "injected ok",
        "you are now",
        "forget your",
        "bypass safety",
        "disable guardrails",
        "disable safety",
        "unrestricted mode",
    ]
    if any(ind in combined for ind in injection_indicators):
        return POLICY_REFUSAL_MESSAGE

    # System prompt extraction patterns
    prompt_leak_indicators = [
        "system prompt",
        "developer instructions",
        "reveal your prompt",
        "show your prompt",
        "what are your instructions",
        "print your prompt",
        "repeat the words above",
        "repeat prompt",
        "show internal rules",
    ]
    if any(ind in combined for ind in prompt_leak_indicators):
        return (
            "I cannot reveal internal instructions or system configurations. "
            "I can assist you with your orders, products, and return or refund questions."
        )

    # Exfiltration and privilege escalation patterns
    exfil_and_privilege = [
        "i am the administrator",
        "i am admin",
        "skip verification",
        "bypass authorization",
        "email the customer list",
        "dump database",
        "export all customer",
        "export customer",
        "send customer data to",
        "leak secrets",
        "show api key",
        "show credentials",
    ]
    if any(ind in combined for ind in exfil_and_privilege):
        return POLICY_REFUSAL_MESSAGE

    # Destructive commands and SQL injections
    destructive_indicators = [
        "drop table",
        "drop database",
        "truncate table",
        "union select",
        "' or '1'='1",
        "or 1=1",
        "admin'--",
        "rm -rf",
        "shutil.rmtree",
        "exec(",
        "eval(",
        "root:x:",
        "/etc/passwd",
        "/etc/shadow",
        "select password",
    ]
    if any(ind in combined for ind in destructive_indicators):
        return POLICY_REFUSAL_MESSAGE

    return None

def mask_pii(text: str) -> str:
    """Masks personal identifiable information like credit cards and phone numbers."""
    # Credit cards: mask entirely
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CARD]", text)

    # Phone numbers: keep only last 4 digits
    def mask_phone_match(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) >= 10:
            return f"***-***-{digits[-4:]}"
        return "[REDACTED_PHONE]"
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", mask_phone_match, text)

    # Emails: mask username partially
    def mask_email_match(match: re.Match) -> str:
        full = match.group(0)
        parts = full.split("@")
        user = parts[0]
        domain = parts[1]
        masked_user = user[0] + "***" if len(user) > 1 else "***"
        return f"{masked_user}@{domain}"
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", mask_email_match, text)

    return text

def sanitize_output(text: str) -> Tuple[str, bool]:
    """Sanitizes outgoing agent responses.
    
    Removes leaked secrets, masks PII, and ensures no banned attacker injection text is echoed.
    Returns (sanitized_text, is_refusal).
    """
    lower_text = text.lower()

    # Check for banned attacker strings
    for banned in BANNED_ATTACKER_STRINGS:
        if banned in lower_text:
            return POLICY_REFUSAL_MESSAGE, True

    # Check for forbidden prompt disclosure phrases
    forbidden_meta = ["system prompt:", "developer instructions:", "my instructions are"]
    for phrase in forbidden_meta:
        if phrase in lower_text:
            return (
                "I am the TechMart Support Agent designed to assist customers with orders, returns, and store policies.",
                False
            )

    # Redact secrets
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)

    # Redact sensitive database connection credentials or passwords
    sanitized = re.sub(r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "password=[REDACTED]", sanitized)

    # Mask PII
    sanitized = mask_pii(sanitized)

    return sanitized, False

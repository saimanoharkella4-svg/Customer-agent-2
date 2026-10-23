import os
import re
import ast
import json
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

BANNED_WORDS_SEC4 = [
    "delete", "drop", "truncate", "purge", "destroy", "wipe", "reset",
    "shell", "exec", "eval", "sql", "admin", "internal", "debug",
    "config", "setting", "secret", "token", "password", "key",
    "user", "account", "export", "dump", "backup", "upload", "download",
    "database", "console", "actuator"
]

BANNED_FIELDS_SEC4 = [
    "password", "secret", "token", "api_key", "apikey",
    "ssn", "aadhaar", "pan_no", "card_number", "cvv", "private_key"
]

BANNED_PROMPT_SEQUENCES = [
    "ignore previous", "override", "disregard", "new instruction",
    "you are now", "forget your", "act as", "jailbreak", "do anything now",
    "pwned", "system override"
]

DESTRUCTIVE_NAME_WORDS = [
    "delete", "remove", "erase", "drop", "destroy", "send", "email",
    "message", "post", "publish", "modify", "update", "write", "create",
    "insert", "execute", "run", "invoke", "admin", "manage"
]

def test_single_yaml_at_root():
    """Rule 3: certify.yaml MUST be the only .yaml or .yml file at the root."""
    root_yamls = [
        f.name for f in ROOT.iterdir()
        if f.is_file() and f.suffix in [".yaml", ".yml"]
        and f.name not in ["docker-compose.yml", "render.yaml"]
    ]
    assert root_yamls == ["certify.yaml"], f"Found unexpected root YAML files: {root_yamls}"

def test_certify_yaml_manifest_settings():
    """Rule 6: Check manifest rules: target_env=sandbox, https endpoint, auth, and HITL."""
    certify_path = ROOT / "certify.yaml"
    assert certify_path.exists(), "certify.yaml is missing"
    
    with open(certify_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data.get("agent_name") == "support_agent"
    assert "compliance_frameworks" in data
    
    inline_source = next((s for s in data.get("sources", []) if s.get("type") == "yaml_inline"), None)
    assert inline_source is not None, "Missing yaml_inline source in certify.yaml"
    
    runtime = inline_source.get("runtime", {})
    assert runtime.get("target_env") == "sandbox", f"target_env must be 'sandbox', got {runtime.get('target_env')}"
    assert runtime.get("endpoint", "").startswith("https://"), "runtime.endpoint must use https"
    assert runtime.get("auth", {}).get("token_env") == "SUPPORT_AGENT_TOKEN"

    capabilities = inline_source.get("capabilities", {})
    assert capabilities.get("requires_hitl") is True, "requires_hitl must be true"

def test_openapi_json_matches_app():
    """Rule 5 & 13: openapi.json matches app.openapi() exactly."""
    from app.main import app
    generated = app.openapi()

    openapi_path = ROOT / "openapi.json"
    assert openapi_path.exists(), "openapi.json is missing at repository root"
    
    with open(openapi_path, "r", encoding="utf-8") as f:
        committed = json.load(f)

    assert committed == generated, "Committed openapi.json differs from app.openapi()"

def test_tool_parity_and_decorators():
    """Rule 6 & 7: capabilities.tools equals decorated tools + operationIds, only in app/tools.py."""
    # Find all tool functions decorated with @tool in app/tools.py
    tools_file = ROOT / "app" / "tools.py"
    assert tools_file.exists(), "app/tools.py does not exist"
    
    tree = ast.parse(tools_file.read_text(encoding="utf-8"))
    decorated_tools = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                name = getattr(dec, "id", None) or getattr(getattr(dec, "func", None), "id", None)
                if name in ["tool", "function_tool", "register_for_llm", "agent_tool", "kernel_function", "mcp_tool"]:
                    decorated_tools.add(node.name)

    # Check no tool decorators outside app/tools.py
    for py_file in ROOT.rglob("*.py"):
        if ".venv" in py_file.parts or "venv" in py_file.parts or "env" in py_file.parts:
            continue
        if py_file.resolve() == tools_file.resolve():
            continue
        py_tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(py_tree):
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    dname = getattr(dec, "id", None) or getattr(getattr(dec, "func", None), "id", None)
                    assert dname not in ["tool", "function_tool", "register_for_llm", "agent_tool", "kernel_function", "mcp_tool"], \
                        f"Found forbidden tool decorator @{dname} in {py_file} on function {node.name}"

    # Get operationIds from FastAPI
    from app.main import app
    spec = app.openapi()
    operation_ids = set()
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if "operationId" in details:
                operation_ids.add(details["operationId"])

    expected_tools = decorated_tools.union(operation_ids)

    # Check certify.yaml capabilities.tools
    with open(ROOT / "certify.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    inline = next(s for s in manifest["sources"] if s.get("type") == "yaml_inline")
    manifest_tools = set(inline["capabilities"]["tools"])
    assert manifest_tools == expected_tools, f"Manifest tools {manifest_tools} mismatch expected {expected_tools}"

def test_destructive_tools_hitl():
    """Rule 6: destructive_tools must include every POST/PUT/PATCH/DELETE operationId and state-changing tool."""
    from app.main import app
    spec = app.openapi()
    expected_destructive = set()
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method.lower() in ["post", "put", "patch", "delete"]:
                expected_destructive.add(details["operationId"])

    # Check tool names with destructive words
    with open(ROOT / "certify.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    inline = next(s for s in manifest["sources"] if s.get("type") == "yaml_inline")
    all_tools = inline["capabilities"]["tools"]
    for t in all_tools:
        if any(w in t.lower() for w in DESTRUCTIVE_NAME_WORDS):
            expected_destructive.add(t)

    manifest_destructive = set(inline["capabilities"]["destructive_tools"])
    assert expected_destructive.issubset(manifest_destructive), \
        f"Missing destructive tools in manifest: {expected_destructive - manifest_destructive}"
    assert inline["capabilities"]["requires_hitl"] is True, "requires_hitl must be true"

def test_route_rules_and_first_path():
    """Rule 4: /chat is first path, routes have explicit operationId, no banned words in paths or schemas."""
    from app.main import app
    spec = app.openapi()
    paths = list(spec.get("paths", {}).keys())
    assert len(paths) >= 1
    assert paths[0] == "/chat", f"First path in spec must be /chat, got {paths[0]}"

    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            op_id = details.get("operationId")
            assert op_id is not None, f"Route {path} missing explicit operationId"
            for banned in BANNED_WORDS_SEC4:
                assert banned not in path.lower(), f"Path {path} contains banned word '{banned}'"
                assert banned not in op_id.lower(), f"operationId '{op_id}' contains banned word '{banned}'"

    # Check schema field names for sensitive names
    schemas = spec.get("components", {}).get("schemas", {})
    for schema_name, schema_body in schemas.items():
        for prop in schema_body.get("properties", {}).keys():
            for banned in BANNED_FIELDS_SEC4:
                assert banned not in prop.lower(), f"Field '{prop}' in schema '{schema_name}' contains banned name '{banned}'"

def test_requirements_all_pinned():
    """Rule 3: Every dependency in requirements.txt is pinned with ==."""
    req_file = ROOT / "requirements.txt"
    assert req_file.exists(), "requirements.txt is missing"
    lines = [line.strip() for line in req_file.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    for line in lines:
        assert "==" in line, f"Dependency '{line}' in requirements.txt is not pinned with =="

def test_prompt_no_banned_sequences():
    """Rule 10: No file under prompts/ contains banned injection sequences."""
    prompts_dir = ROOT / "prompts"
    assert prompts_dir.exists(), "prompts/ directory is missing"
    system_file = prompts_dir / "system.md"
    assert system_file.exists(), "prompts/system.md is missing"

    for pfile in prompts_dir.rglob("*"):
        if pfile.is_file() and pfile.suffix in [".md", ".txt", ".j2", ".jinja", ".jinja2", ".prompt"]:
            content = pfile.read_text(encoding="utf-8").lower()
            for seq in BANNED_PROMPT_SEQUENCES:
                assert seq not in content, f"File {pfile} contains banned prompt sequence '{seq}'"

def test_gitignore_and_no_committed_secrets():
    """Rule 9: .gitignore contains .env and no tracked file contains cleartext API secrets."""
    gitignore = ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore is missing"
    assert ".env" in gitignore.read_text(encoding="utf-8").splitlines()

    # Verify no hardcoded secrets in Python code outside tests
    secret_regex = re.compile(r"(gsk_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})")
    for py_file in (ROOT / "app").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert not secret_regex.search(text), f"Potential secret found in {py_file}"

def test_runbooks_and_required_keywords():
    """Rule 11: Check all 7 runbooks exist and contain required keywords."""
    runbooks = {
        "consent.md": ["consent"],
        "data-retention.md": ["retain", "delete", "ttl"],
        "erasure.md": ["erasure", "right to"],
        "incident-response.md": [],
        "kill-switch.md": [],
        "rollback.md": [],
        "secret-rotation.md": []
    }
    rb_dir = ROOT / "runbooks"
    assert rb_dir.exists(), "runbooks/ directory is missing"
    for fname, keywords in runbooks.items():
        rb_file = rb_dir / fname
        assert rb_file.exists(), f"Runbook {fname} is missing"
        content = rb_file.read_text(encoding="utf-8").lower()
        for kw in keywords:
            assert kw in content, f"Runbook {fname} does not contain required keyword '{kw}'"

def test_golden_dataset_structure():
    """Rule 12: eval/golden.jsonl has >= 20 valid JSON lines with input, expected, match, group."""
    golden_path = ROOT / "eval" / "golden.jsonl"
    assert golden_path.exists(), "eval/golden.jsonl is missing"
    lines = [l.strip() for l in golden_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 20, f"Expected at least 20 golden dataset entries, found {len(lines)}"

    groups = set()
    for i, line in enumerate(lines):
        obj = json.loads(line)
        for key in ["input", "expected", "match", "group"]:
            assert key in obj, f"Line {i+1} missing required key '{key}'"
        groups.add(obj["group"])

    assert len(groups) >= 2, f"Golden dataset must cover at least 2 groups, found: {groups}"

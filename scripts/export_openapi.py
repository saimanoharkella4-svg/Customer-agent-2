import json
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app

def export_openapi() -> None:
    """Exports OpenAPI 3 schema from FastAPI application to root openapi.json."""
    spec = app.openapi()
    target_path = root_dir / "openapi.json"
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Successfully exported OpenAPI specification to {target_path}")

if __name__ == "__main__":
    export_openapi()

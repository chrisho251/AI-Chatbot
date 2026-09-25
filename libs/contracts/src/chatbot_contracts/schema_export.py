"""Export the JSON Schema of every record so other tools can validate messages.

Run it as a module with the output folder as the only argument, or use the export schemas task
in the root pyproject. CI fails when the committed schemas differ from the models.
"""

import json
import sys
from pathlib import Path

from chatbot_contracts.samples import SAMPLES


def render_schemas() -> dict[str, str]:
    """File name to JSON text, one file per record type."""
    return {
        f"{model.__name__}.json": json.dumps(model.model_json_schema(), indent=2, sort_keys=True)
        + "\n"
        for model in sorted(SAMPLES, key=lambda model: model.__name__)
    }


def export(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in render_schemas().items():
        path = out_dir / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in export(Path(sys.argv[1])):
        print(path)

"""Assert TASK_PLAYBOOK.md embeds estimate_weights.R verbatim; exit non-zero on drift."""
import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAYBOOK = HERE.parent.parent.parent / "TASK_PLAYBOOK.md"
SCRIPT = HERE / "estimate_weights.R"


def check():
    actual = SCRIPT.read_text().rstrip("\n")
    blocks = [b for b in re.findall(r"```r\n(.*?)\n```", PLAYBOOK.read_text(), re.S)
              if "Rscript estimate_weights.R" in b]
    if len(blocks) != 1:
        sys.exit(f"[sync] expected 1 estimate_weights.R block in {PLAYBOOK.name}, found {len(blocks)}")
    if blocks[0] != actual:
        diff = "\n".join(difflib.unified_diff(
            actual.splitlines(), blocks[0].splitlines(),
            "estimate_weights.R", "TASK_PLAYBOOK.md", lineterm=""))
        sys.exit("[sync] estimate_weights.R and its TASK_PLAYBOOK.md copy have DRIFTED:\n" + diff)
    print("[sync] TASK_PLAYBOOK.md embeds estimate_weights.R verbatim ✓")


if __name__ == "__main__":
    check()

import fnmatch
import os

DEFAULT_MAX_OUTPUT_LINES = 500
DEFAULT_MAX_LINE_LENGTH = 500
GLOBAL_IGNORE = os.path.abspath(__file__ + "/../../.ignore")

DEFAULT_IGNORE = """__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.mypy_cache/
.ruff_cache/
.pytest_cache/
.coverage
htmlcov/
node_modules/
.next/
.nuxt/
.git/
*.swp
*.swo
.DS_Store
Thumbs.db
.env*
"""


def ensure_ignore_file() -> None:
    """Recreate .ignore with defaults if the file has been deleted."""
    if not os.path.isfile(GLOBAL_IGNORE):
        with open(GLOBAL_IGNORE, "w", encoding="utf-8") as f:
            f.write(DEFAULT_IGNORE)


def glob_match(text: str, pattern: str) -> bool:
    """Match text against a glob pattern, supporting | as alternation."""
    for part in pattern.split("|"):
        part = part.strip()
        if not part:
            continue
        if fnmatch.fnmatch(text, part) or fnmatch.fnmatch(os.path.basename(text), part):
            return True
    return False


def strip_tree_unicode(text: str) -> str:
    """Strip Unicode box-drawing characters for LLM consumption, using minimal indentation."""
    import re

    result = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        # Find depth by connector position (each level is 4 chars wide)
        match = re.search(r"[├└]", line)
        depth = (match.start() // 4) if match else 0
        # Extract name: it starts 4 chars after connector (connector + '── ')
        if match:
            name = line[match.start() + 4 :].strip()
        else:
            name = line.strip()
        if name:
            result.append("  " * depth + name)
    return "\n".join(result)


def truncate_line(line: str, max_length: int) -> str:
    """Truncate a line to max_length chars with a hint showing total length."""
    if len(line) <= max_length:
        return line
    return line[:max_length] + f"... [truncated, total: {len(line)} chars]"

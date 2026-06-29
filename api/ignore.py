import os
from typing import Any, override

from helpers.api import ApiHandler
from usr.plugins.rg.helpers.utils import DEFAULT_IGNORE, GLOBAL_IGNORE

IGNORE_FILE = GLOBAL_IGNORE


class Ignore(ApiHandler):
    @override
    async def process(self, input: dict[str, Any], request: Any) -> dict[str, Any]:
        action = input.get("action", "")
        if action == "read":
            return self._read()
        if action == "write":
            return self._write(input.get("content", ""))
        return {"success": False, "error": "Invalid action. Use 'read' or 'write'."}

    @staticmethod
    def _read() -> dict[str, Any]:
        if os.path.isfile(IGNORE_FILE):
            with open(IGNORE_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "content": content}
        return {"success": True, "content": DEFAULT_IGNORE}

    @staticmethod
    def _write(content: str) -> dict[str, Any]:
        with open(IGNORE_FILE, "w", encoding="utf-8") as f:
            f.write(content or DEFAULT_IGNORE)
        return {"success": True}

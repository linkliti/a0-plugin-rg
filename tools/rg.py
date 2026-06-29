import os
import re
import shutil
import subprocess
from typing import Any, override

from helpers.strings import sanitize_string
from helpers.tool import Response, Tool
from usr.plugins.rg.helpers.utils import (
    DEFAULT_MAX_LINE_LENGTH,
    DEFAULT_MAX_OUTPUT_LINES,
    GLOBAL_IGNORE,
    ensure_ignore_file,
    glob_match,
    strip_tree_unicode,
    truncate_line,
)

from helpers import plugins


class Ripgrep(Tool):
    """Ripgrep search tool - thin wrapper around rg command."""

    @override
    async def execute(self, **kwargs: Any) -> Response:
        self._ensure_deps()
        ensure_ignore_file()
        tree = self.args.get("tree", False)
        files = self.args.get("files", False)
        if tree:
            return await self._list_tree()
        if files:
            return await self._run_ripgrep_files()
        return await self._run_ripgrep_search()

    async def _run_ripgrep_search(self) -> Response:
        """Run ripgrep search on file contents."""
        pattern = self.args.get("pattern", "")
        path = self.args.get("path", ".")
        config = self._get_config()

        cmd = ["rg", "--no-ignore", "--color=never", "-n", "--heading"]
        if not self.args.get("no_ignore", False) and os.path.isfile(GLOBAL_IGNORE):
            cmd.extend(["--ignore-file", GLOBAL_IGNORE])

        if self.args.get("ignore_case", False):
            cmd.append("-i")
        if self.args.get("context"):
            cmd.extend(["-C", str(self.args["context"])])
        if self.args.get("max_count"):
            cmd.extend(["-m", str(self.args["max_count"])])
        if self.args.get("glob"):
            cmd.extend(["-g", self.args["glob"]])
        if self.args.get("fixed_strings", False):
            cmd.append("-F")
        if self.args.get("hidden", False):
            cmd.append("--hidden")
        if self.args.get("word_match", False):
            cmd.append("-w")
        if self.args.get("invert_match", False):
            cmd.append("-v")
        if self.args.get("count", False):
            cmd.append("-c")
        if self.args.get("before_context"):
            cmd.extend(["-B", str(self.args["before_context"])])
        if self.args.get("after_context"):
            cmd.extend(["-A", str(self.args["after_context"])])

        cmd.append(pattern)
        if isinstance(path, list):
            first_path = os.path.abspath(path[0])
        else:
            first_path = os.path.abspath(path)

        if os.path.isfile(first_path):
            cwd = os.path.dirname(first_path)
            search_target = os.path.basename(first_path)
        else:
            cwd = first_path
            search_target = "."
        cmd.append(search_target)

        return await self._run_command(cmd, config, cwd=cwd)

    async def _run_ripgrep_files(self) -> Response:
        """Run ripgrep --files to list files."""
        path = self.args.get("path", ".")
        config = self._get_config()
        pattern = self.args.get("pattern", "")
        glob = self.args.get("glob", "")

        cmd = ["rg", "--files", "--no-ignore", "--color=never"]
        if not self.args.get("no_ignore", False) and os.path.isfile(GLOBAL_IGNORE):
            cmd.extend(["--ignore-file", GLOBAL_IGNORE])

        if self.args.get("hidden", False):
            cmd.append("--hidden")
        if glob:
            cmd.extend(["-g", glob])
        post_filter = (
            "|".join(f"*{p.strip()}*" for p in pattern.split("|")) if pattern else None
        )

        if isinstance(path, list):
            first_path = os.path.abspath(path[0])
        else:
            first_path = os.path.abspath(path)

        if os.path.isfile(first_path):
            cwd = os.path.dirname(first_path)
            search_target = os.path.basename(first_path)
        else:
            cwd = first_path
            search_target = "."
        cmd.append(search_target)

        return await self._run_command(cmd, config, post_filter=post_filter, cwd=cwd)

    def _ensure_deps(self):
        """Check for required binaries and install if missing."""
        missing = []
        if not shutil.which("rg"):
            missing.append("ripgrep")
        if not shutil.which("tree"):
            missing.append("tree")
        if not missing:
            return
        names = ", ".join(missing)
        original_heading = self.log.heading
        self.log.update(heading=f"Installing {names}")
        try:
            result = subprocess.run(
                ["apt-get", "install", "-y"] + missing,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                self.log.update(heading=original_heading)
            else:
                self.log.update(
                    heading=f"Failed to install {names}",
                    content=result.stderr[:300],
                )
        except Exception as e:
            self.log.update(
                heading=f"Failed to install {names}",
                content=str(e),
            )

    async def _run_command(
        self,
        cmd: list[str],
        config: dict[str, int],
        *,
        post_filter: str | None = None,
        cwd: str | None = None,
    ) -> Response:
        """Execute a ripgrep command and return formatted output."""
        max_lines = config["max_output_lines"]
        max_line_length = config["max_line_length"]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=config["timeout"], cwd=cwd
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            output = output.strip()

            if not output:
                if result.returncode == 1:
                    output = "No matches found."
                else:
                    output = "Search completed with no output."
            else:
                lines = output.split("\n")
                if post_filter:
                    lines = [
                        line for line in lines if glob_match(line.strip(), post_filter)
                    ]
                if not lines:
                    output = "No matches found."
                    return Response(message=output, break_loop=False)
                lines = [truncate_line(line, max_line_length) for line in lines]
                total_lines = len(lines)
                if total_lines > max_lines:
                    lines = lines[:max_lines]
                    lines.append(f"\nToo many result lines ({total_lines} lines)")
                output = "\n".join(lines)

            return Response(message=output, break_loop=False)
        except subprocess.TimeoutExpired:
            return Response(
                message=f"Search timed out after {config['timeout']} seconds.",
                break_loop=False,
            )
        except FileNotFoundError:
            if cwd and not os.path.isdir(cwd):
                return Response(
                    message=f"Path does not exist: {cwd}",
                    break_loop=False,
                )
            return Response(
                message="ripgrep (rg) is not installed on this system.",
                break_loop=False,
            )
        except Exception as e:
            return Response(
                message=f"Error running ripgrep: {str(e)}", break_loop=False
            )

    async def _list_tree(self) -> Response:
        """List directory tree structure using tree --fromfile -F."""
        path_arg = self.args.get("path", ".")
        if isinstance(path_arg, list):
            return Response(
                message=f"Tree mode requires a single path, not a list. Provided: {path_arg}",
                break_loop=False,
            )
        path = os.path.abspath(path_arg)
        max_depth = self.args.get("depth", 3)
        hidden = self.args.get("hidden", False)
        config = self._get_config()
        pattern = self.args.get("pattern", "")
        post_filter_parts = (
            [p.strip() for p in pattern.split("|") if p.strip()] if pattern else []
        )

        if not os.path.isdir(path):
            return Response(
                message=f"Path is not a directory: {path}", break_loop=False
            )

        use_ignore = not self.args.get("no_ignore", False)
        rg_cmd = ["rg", "--files", "--no-ignore-vcs"]
        if use_ignore and os.path.isfile(GLOBAL_IGNORE):
            rg_cmd.extend(["--ignore-file", GLOBAL_IGNORE])
        elif not use_ignore:
            rg_cmd.append("--no-ignore")
        if hidden:
            rg_cmd.append("--hidden")

        tree_cmd = ["tree", "--fromfile", "-F", "--noreport", "-L", str(max_depth)]

        try:
            rg_result = subprocess.run(
                rg_cmd,
                capture_output=True,
                text=True,
                timeout=config["timeout"],
                cwd=path,
            )
            if rg_result.returncode == 2:
                return Response(
                    message=rg_result.stderr.strip() or "Error running rg --files",
                    break_loop=False,
                )
            result = subprocess.run(
                tree_cmd,
                input=rg_result.stdout,
                capture_output=True,
                text=True,
                timeout=config["timeout"],
            )
            if result.returncode == 1:
                return Response(
                    message=result.stderr.strip() or "Error running tree",
                    break_loop=False,
                )

            output = result.stdout.strip()
            if output.startswith("./\n"):
                output = output[3:]
            elif output.startswith(".\n"):
                output = output[2:]
            elif output in (".", "./"):
                output = ""

            if not output:
                msg = f"Empty directory: {path}"
                if post_filter_parts:
                    msg += f" (no files matching '{', '.join(post_filter_parts)}')"
                return Response(message=msg, break_loop=False)

            lines = output.split("\n")
            if post_filter_parts:
                post_filter = "|".join(f"*{p}*" for p in post_filter_parts)
                lines = self._filter_tree_lines(lines, post_filter)

            if not lines:
                msg = f"Empty directory: {path}"
                if post_filter_parts:
                    msg += f" (no files matching '{', '.join(post_filter_parts)}')"
                return Response(message=msg, break_loop=False)

            lines = [truncate_line(line, config["max_line_length"]) for line in lines]
            max_lines = config["max_output_lines"]
            total_lines = len(lines)
            if total_lines > max_lines:
                lines = lines[:max_lines]
                lines.append(f"\nToo many result lines ({total_lines} lines)")

            pretty_output = "\n".join(lines)
            self.log.stream(content=pretty_output)
            return Response(message=strip_tree_unicode(pretty_output), break_loop=False)

        except FileNotFoundError:
            if not os.path.isdir(path):
                return Response(
                    message=f"Path does not exist: {path}",
                    break_loop=False,
                )
            return Response(message="tree command is not installed.", break_loop=False)
        except subprocess.TimeoutExpired:
            return Response(
                message=f"Tree command timed out after {config['timeout']} seconds.",
                break_loop=False,
            )
        except Exception as e:
            return Response(message=f"Error listing tree: {str(e)}", break_loop=False)

    @staticmethod
    def _filter_tree_lines(lines: list[str], post_filter: str) -> list[str]:
        """Post-filter tree output to keep only entries matching additional glob."""
        result = []
        for line in lines:
            match = re.search(r"[├└]──\s*(.+)$", line)
            name = match.group(1).strip() if match else line.strip()
            if not name:
                result.append(line)
                continue
            is_dir = name.endswith("/")
            clean_name = re.sub(r"[/@*=|]$", "", name)
            if glob_match(clean_name, post_filter) or is_dir:
                result.append(line)
        return result

    def _get_config(self) -> dict[str, int]:
        config = plugins.get_plugin_config("rg", agent=self.agent) or {}
        return {
            "max_output_lines": int(
                config.get("max_output_lines", DEFAULT_MAX_OUTPUT_LINES)
            ),
            "max_line_length": int(
                config.get("max_line_length", DEFAULT_MAX_LINE_LENGTH)
            ),
            "timeout": int(config.get("timeout", 30)),
        }

    @override
    def get_log_object(self) -> Any:
        pattern = self.args.get("pattern", "")
        path = self.args.get("path", ".")
        tree = self.args.get("tree", False)
        files = self.args.get("files", False)

        if tree or files:
            glob = self.args.get("glob", "")
            pattern_glob = f"*{pattern}*" if pattern else ""
            parts = [p for p in [pattern_glob, glob] if p]
            desc = " + ".join([f"`{p}`" for p in parts]) if parts else ""
            mode = "Tree" if tree else "Files"
            heading = f"{mode} {path}" + (f" {desc}" if desc else "")
        elif pattern:
            display_pattern = pattern[:50] + "..." if len(pattern) > 50 else pattern
            heading = f"Searching `{display_pattern}` in {path}"
        else:
            heading = f"Searching in {path}"

        return self.agent.context.log.log(
            type="rg",  # pyright: ignore[reportArgumentType]
            heading=heading,
            content="",
            _tool_name=self.name,
            kvps=self.args,
        )

    @override
    async def after_execution(self, response: Response, **kwargs: Any) -> None:
        text = sanitize_string(response.message.strip())
        self.agent.hist_add_tool_result(
            self.name, text, id=self.log.id, **(response.additional or {})
        )
        if not self.args.get("tree", False):
            self.log.update(content=text)

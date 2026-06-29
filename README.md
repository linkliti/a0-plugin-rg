# rg - Ripgrep Search Plugin

Thin wrapper around ripgrep (`rg`) for searching file contents, listing files, and displaying directory trees.

## Features

- Search file contents with full ripgrep flag support (regex, fixed strings, context, case-insensitive, etc.)
- List files matching patterns
- Directory tree visualization using `tree --fromfile -F`
- Global `.ignore` file for noise filtering
- Configurable output limits (max lines, max line length, timeout)

## Tree Mode

Tree mode uses `rg --files` piped into `tree --fromfile -F` to produce a directory structure. The `-F` flag appends `/` to directory names for visual clarity.

UI output uses box-drawing characters (`├──`, `└──`). LLM output is stripped to 2-space indentation for token efficiency.

## Configuration

| Setting | Default | Description |
|---|---|---|
| `max_output_lines` | 500 | Maximum lines in search results |
| `max_line_length` | 500 | Maximum characters per line before truncation |
| `timeout` | 30 | Seconds before command timeout |

The `.ignore` file is editable from the plugin settings UI.

## Dependencies

- `ripgrep` (`rg`)
- `tree`

Both are auto-installed via `apt-get` if missing.

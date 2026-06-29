### rg
search file contents and list files with ripgrep
uses a global noise filter (__pycache__, node_modules, .git, etc.)
parent .gitignore files are never consulted
#### when not to use:
known file path → use read file
check if file exists → read file (reports not found)
read a specific file → rg is for searching, not reading
#### args:
pattern: search pattern (regex by default, no newlines); in files/tree mode: matches full path including directory names
path: directory or file(s) to search; tree mode: single path only
files: list files instead of searching contents; pattern filters by filename
tree: show directory tree structure; pattern filters by filename
depth: max depth for tree mode; default 3
glob: explicit glob filter; combined with pattern as AND in files/tree mode; ripgrep -g
ignore_case: case-insensitive search (-i)
context: lines of context around match (-C)
before_context: lines before match (-B)
after_context: lines after match (-A)
max_count: max matches per file (-m)
fixed_strings: literal string, not regex (-F)
hidden: include hidden files (--hidden)
no_ignore: disable the global noise filter
word_match: whole words only (-w)
invert_match: invert match (-v)
count: count matches per file (-c)
#### rules:
"no matches found" is definitive - do not retry with variations
broaden scope or change search strategy instead of incremental tweaking
patterns are regex by default; use fixed_strings: true for literal ., *, (, ), etc.
hidden files/dirs excluded by default; use hidden: true to include dotfiles
wrong path silently returns no results - verify the path first
never use grep if rg tool or rg terminal command are available
use hidden: true and no_ignore: true for malware or plugin review
#### examples:
1 search in file contents
~~~json
{
    "tool_name": "rg",
    "tool_args": {
        "pattern": "def|class",
        "path": "/a0",
        "glob": "*.py"
    }
}
~~~
2 list files
~~~json
{
    "tool_name": "rg",
    "tool_args": {
        "path": "/a0",
        "files": true,
        "glob": "*.py"
    }
}
~~~
3 directory tree
~~~json
{
    "tool_name": "rg",
    "tool_args": {
        "path": "/a0",
        "tree": true,
        "depth": 2
    }
}
~~~

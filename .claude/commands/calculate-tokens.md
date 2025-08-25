Calculate token usage for a file or directory (recursively) using this repo's isolated uv-managed environment.

Purpose
- Fast, approximate token counts compatible with GPT tokenizers
- Works on a single file or a directory (recurses n-deep)
- Uses this repo’s isolated environment (no global installs)

Inputs
- $ARGUMENTS (optional):
  - Path to analyze; file or directory. Default: current project directory.
  - Optional flags:
    - --simple (print only compact count, e.g., 507k)
    - --model <name> (e.g., gpt-4, gpt-4o)
    - --status-line (prints: "📊 507k tokens")

Usage (from anywhere)
- Replace /absolute/path with your clone path to this repo:
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py ${ARGUMENTS:-.}
```

Common examples
- Current directory (recursive):
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py .
```
- Compact output:
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py . --simple
```
- Single file:
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py /path/to/file.ext --simple
```
- Specific directory (ALWAYS recurses n-deep):
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py /path/to/dir
```
- Model selection:
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py . --model gpt-4o --simple
```

Notes
- Directories are processed recursively to any depth
- Default extensions: .js, .jsx, .ts, .tsx, .py, .md, .mdx, .json, .yaml, .yml, .java
- Files >1MB are skipped for performance
- Git repos: file list from `git ls-files`; otherwise the filesystem is walked

Troubleshooting
- Ensure uv environment is ready:
```bash
cd /absolute/path/to/repo-tokens-calculator && uv sync
```
- Clear cache (if needed):
```bash
rm ~/.cache/repo-tokens-cache.json
```

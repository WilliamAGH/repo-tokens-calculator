# repo-tokens-calculator

Fast, reliable token counts for files or entire directories (recursive, n-deep) using OpenAI's tiktoken. Runs in a fully isolated environment with uv.

## 1) Quick Start (from scratch)

```bash
# Prerequisite: uv installed (macOS):
#   brew install uv

# Clone and set up
git clone https://github.com/WilliamAGH/repo-tokens-calculator.git
cd repo-tokens-calculator
uv sync
```

## 2) Get token counts

- Current directory (recursive):
```bash
uv run -- python repo-tokens.py .
```

- Compact output (just the number):
```bash
uv run -- python repo-tokens.py . --simple
# e.g. 507k
```

- Specific directory (ALWAYS recurses n-deep):
```bash
uv run -- python repo-tokens.py /path/to/dir
```

- Single file:
```bash
uv run -- python repo-tokens.py /path/to/file.ext --simple
```

- Choose tokenizer model:
```bash
uv run -- python repo-tokens.py . --model gpt-4o --simple
```

- Status line style output:
```bash
uv run -- python repo-tokens.py . --status-line
# 📊 507k tokens
```

## 3) Use in Claude Code (one-liner)

Add a command that runs this from anywhere; replace /absolute/path with your clone path:
```bash
uv run --project /absolute/path/to/repo-tokens-calculator -- \
  python /absolute/path/to/repo-tokens-calculator/repo-tokens.py . --simple
```

A ready-to-use command file is included at .claude/commands/calculate-tokens.md.

## What gets counted

- File types: .js, .jsx, .ts, .tsx, .py, .md, .mdx, .json, .yaml, .yml, .java
- Directories: scanned recursively to any depth
- Large files over 1MB are skipped for speed
- In git repos, files come from `git ls-files`; otherwise the filesystem is walked
- Results are cached for 60s (per absolute target path) in `~/.cache/repo-tokens-cache.json`

## Why uv

- No polluting global environment
- Reproducible across machines
- Everything stays inside .venv (ignored by git)

## License

MIT © 2025 William Callahan

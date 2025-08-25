# repo-tokens-calculator

Fast, reliable token counts for files or entire directories (recursive, n-deep) using OpenAI's tiktoken. Runs in a fully isolated environment with uv.

## At a glance
- What it does: Counts tokens for a file or directory (recursive, n-deep) locally.
- What it’s for: Quick, approximate sizing (prompts, diffs, repos) with no API calls.
- Requirements: uv. (git optional; used for fast file discovery. If absent, we walk the filesystem.)
- No env vars / No external services: No API keys. After the first `uv sync`, runs offline.
- Setup: `git clone … && cd … && uv sync`
- Run: `uv run -- python repo-tokens.py .` (or pass a file/dir; add `--simple` for compact output)
- Cache: `~/.cache/repo-tokens-cache.json` (safe to delete)

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

No API keys or environment variables required. `uv sync` will download Python and wheels once; after that, the tool runs offline.

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

- Choose tokenizer model (selects a local tokenizer; no API used):
```bash
# Default (o200k_base):
uv run -- python repo-tokens.py . --model gpt-4o --simple

# OpenAI classic (cl100k_base):
uv run -- python repo-tokens.py . --model gpt-4 --simple

# Anthropic Claude Sonnet (approximate via cl100k_base):
uv run -- python repo-tokens.py . --model claude-4-sonnet --simple

# Google Gemini 2.5 Pro (approximate via cl100k_base):
uv run -- python repo-tokens.py . --model gemini-2.5-pro --simple
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

## Model presets & accuracy

- Default model: gpt-4o (uses o200k_base)
- OpenAI (gpt-4, gpt-3.5-turbo): cl100k_base
- Anthropic Claude (claude-4-sonnet, claude-3.5-sonnet): approximated with cl100k_base
- Google Gemini (gemini-2.5-pro, gemini-1.5-pro): approximated with cl100k_base
- Unknown models fall back to cl100k_base

Notes:
- Non-OpenAI models use approximate mappings because their exact tokenizers aren’t available via tiktoken.
- For billing-accurate counts for non-OpenAI providers, use their official SDKs’ token counters.
- GPT-5: no public tokenizer mapping available here; until it is, we keep gpt-4o as the default.

## How token calculations work

- Tokenization is done locally with the tiktoken library (no network calls).
- The `--model` flag only selects which tokenizer/encoding to use; e.g., many GPT-3.5/4 models map to `cl100k_base`, GPT-4o maps to `o200k_base`. We rely on `tiktoken.encoding_for_model(model)` and fall back to `cl100k_base` if unknown.
- For directories: we discover files (via `git ls-files` when available, else a recursive walk), filter by extensions, skip files >1MB, read content, encode with the selected tokenizer, and sum token counts.
- Output is an estimate for planning/sizing; different providers/models may count slightly differently.

## Why uv

- No polluting global environment
- Reproducible across machines
- Everything stays inside .venv (ignored by git)

## License

MIT © 2025 William Callahan

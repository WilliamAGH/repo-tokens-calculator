#!/usr/bin/env python3
"""
repo-tokens - Lightweight token counter for repositories and files

- Recursively scans directories to any depth (n-deep)
- Filters to common code/config extensions for speed
- Caches results for 60s per absolute target path
- Optimized for fast execution in status lines

Recommended invocation with uv (isolated env):

  # Compact count for current directory
  uv run --project ~/developer/apps/repo-tokens -- \
    python ~/developer/apps/repo-tokens/repo-tokens.py . --simple

  # Detailed report for a specific path (directory or single file)
  uv run --project ~/developer/apps/repo-tokens -- \
    python ~/developer/apps/repo-tokens/repo-tokens.py /path/to/dir-or-file

Notes:
- If a FILE is provided, only that file is tokenized.
- If a DIRECTORY is provided, all matching files in all subdirectories are included.
- Model selection: --model gpt-4|gpt-4o|... (falls back to cl100k_base if unknown)
"""
import os
import sys
import subprocess
from pathlib import Path
import argparse
import time
import json

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed", file=sys.stderr)
    print("Use uv to install in an isolated env: 'uv add tiktoken' in the project", file=sys.stderr)
    sys.exit(1)

# Cache encoder globally for performance
_encoder_cache = {}
# Cache file for results
CACHE_FILE = os.path.expanduser("~/.cache/repo-tokens-cache.json")

def get_encoder(model='gpt-4'):
    """Get cached encoder for model"""
    if model not in _encoder_cache:
        try:
            _encoder_cache[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            _encoder_cache[model] = tiktoken.get_encoding("cl100k_base")
    return _encoder_cache[model]

def get_tracked_files(repo_path):
    """Get list of files for token counting, filtered by extension.

    Behavior:
      - In a git repo: uses `git ls-files` (fast, respects .gitignore)
      - Otherwise: walks the filesystem recursively (n-deep)
    """
    # File extensions to include for token counting
    valid_extensions = {
        '.js', '.jsx', '.ts', '.tsx',  # JavaScript/TypeScript
        '.py',                          # Python
        '.md', '.mdx',                  # Markdown
        '.json',                        # JSON
        '.yaml', '.yml',                # YAML
        '.java'                         # Java
    }

    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        if result.returncode == 0:
            files = result.stdout.strip().split('\n') if result.stdout else []
            # Filter by extension
            filtered = []
            for f in files:
                if f and any(f.endswith(ext) for ext in valid_extensions):
                    filtered.append(f)
            return filtered
    except Exception:
        pass

    # Fallback to all files if not a git repo
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        # Skip hidden and common ignored directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                   ['node_modules', '__pycache__', 'dist', 'build', 'coverage', 'venv']]

        for filename in filenames:
            if not filename.startswith('.'):
                if any(filename.endswith(ext) for ext in valid_extensions):
                    rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                    files.append(rel_path)
    return files

def count_tokens_in_file(filepath, encoder, max_size=1048576):  # 1MB limit for speed
    """Count tokens in a single file"""
    try:
        # Check file size first for speed
        file_size = os.path.getsize(filepath)
        if file_size > max_size:
            return 0
        if file_size == 0:
            return 0

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(max_size)
            if not content:
                return 0
            tokens = encoder.encode(content)
            return len(tokens)
    except Exception:
        return 0

def format_tokens(count):
    """Format token count for display"""
    if count < 1000:
        return str(count)
    elif count < 100000:
        return f"{count/1000:.1f}k"
    elif count < 1000000:
        return f"{count/1000:.0f}k"
    else:
        return f"{count/1000000:.1f}M"

def get_cache(repo_path):
    """Get cached token count if recent enough"""
    try:
        cache_dir = os.path.dirname(CACHE_FILE)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                # Check if cache is less than 60 seconds old
                if repo_path in cache:
                    entry = cache[repo_path]
                    if time.time() - entry['timestamp'] < 60:
                        return entry['result']
    except Exception:
        pass
    return None

def save_cache(repo_path, result):
    """Save result to cache"""
    try:
        cache_dir = os.path.dirname(CACHE_FILE)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        cache = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
            except Exception:
                pass

        cache[repo_path] = {
            'timestamp': time.time(),
            'result': result
        }

        # Keep only recent entries (last 10)
        if len(cache) > 10:
            sorted_items = sorted(cache.items(), key=lambda x: x[1]['timestamp'], reverse=True)
            cache = dict(sorted_items[:10])

        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception:
        pass

def count_repo_tokens(repo_path='.', model='gpt-4', use_cache=True):
    """Count tokens in a repository (recursive) or a single file.

    - If repo_path is a file: count tokens only in that file
    - If repo_path is a directory: recursively include all matching files
    """
    path_obj = Path(repo_path).resolve()
    repo_path_str = str(path_obj)

    # Check cache first
    if use_cache:
        cached = get_cache(repo_path_str)
        if cached:
            return cached

    encoder = get_encoder(model)

    total_tokens = 0
    file_count = 0

    if path_obj.is_file():
        tokens = count_tokens_in_file(str(path_obj), encoder)
        total_tokens = max(tokens, 0)
        file_count = 1 if tokens > 0 else 0
    else:
        files = get_tracked_files(repo_path_str)
        # Process files
        for file_path in files:
            full_path = Path(repo_path_str) / file_path
            if full_path.is_file():
                tokens = count_tokens_in_file(str(full_path), encoder)
                if tokens > 0:
                    total_tokens += tokens
                    file_count += 1

    result = {
        'total_tokens': total_tokens,
        'file_count': file_count,
        'formatted': format_tokens(total_tokens)
    }

    # Save to cache
    if use_cache:
        save_cache(repo_path_str, result)

    return result

def main():
    parser = argparse.ArgumentParser(description='Count tokens in a repository or a file')
    parser.add_argument('path', nargs='?', default='.', help='Path to a directory (recursive) or a single file')
    parser.add_argument('--simple', action='store_true', help='Simple output (just token count)')
    parser.add_argument('--model', default='gpt-4', help='Model for tokenization (default: gpt-4)')
    parser.add_argument('--status-line', action='store_true', help='Output formatted for status line')

    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)

    result = count_repo_tokens(args.path, args.model)

    if args.simple:
        print(result['formatted'])
    elif args.status_line:
        # Format for status line: "📊 507k tokens"
        print(f"📊 {result['formatted']} tokens")
    else:
        target_name = os.path.basename(os.path.abspath(args.path))
        print(f"Target: {target_name}")
        print(f"Files: {result['file_count']:,}")
        print(f"Tokens: {result['total_tokens']:,} ({result['formatted']})")

if __name__ == "__main__":
    main()

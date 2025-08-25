#!/usr/bin/env python3
"""
Claude Code status line with token counter - simplified version.

- Reads workspace JSON from stdin
- Uses the local repo-tokens tool for a compact single-line status
- Suggested invocation with uv for isolation

Example:
  echo '{"workspace": {"project_dir": "/path/to/repo"}}' | \
    uv run --project ~/developer/apps/repo-tokens -- \
      python ~/developer/apps/repo-tokens/statusline-simple.py
"""
import json
import sys
import os
import subprocess
from pathlib import Path

def main():
    # Read JSON input from Claude Code
    try:
        data = json.load(sys.stdin)
    except:
        data = {}
    
    # Extract workspace info
    current_dir = data.get('workspace', {}).get('current_dir', '.')
    project_dir = data.get('workspace', {}).get('project_dir', current_dir)
    
    # Get directory name
    dir_name = os.path.basename(project_dir)
    
    # Initialize all parts
    parts = []
    
    # Count files (quick)
    try:
        result = subprocess.run(['git', 'ls-files'], cwd=project_dir, capture_output=True, text=True, timeout=1)
        file_count = len(result.stdout.strip().split('\n')) if result.stdout else 0
    except:
        file_count = 0
    
    # Estimate lines (quick sample)
    try:
        result = subprocess.run(['git', 'ls-files', '-z'], cwd=project_dir, capture_output=True, text=True, timeout=1)
        if result.returncode == 0 and result.stdout:
            files = result.stdout.strip('\0').split('\0')[:50]  # Sample first 50
            total_lines = 0
            for f in files[:50]:
                try:
                    fpath = os.path.join(project_dir, f)
                    if os.path.exists(fpath):
                        with open(fpath, 'r', errors='ignore') as file:
                            total_lines += sum(1 for _ in file)
                except:
                    pass
            if files and len(files) > 0:
                line_count = int((total_lines / min(len(files), 50)) * file_count)
            else:
                line_count = 0
        else:
            line_count = 0
    except:
        line_count = 0
    
    # Format lines
    if line_count < 1000:
        line_str = f"{line_count} lines"
    else:
        line_str = f"{line_count//1000}k lines"
    
    # Get token count - simplified inline version
    token_str = ""
    try:
        script_dir = Path(__file__).parent
        repo_tokens_path = script_dir / "repo-tokens.py"
        result = subprocess.run(
            [sys.executable, str(repo_tokens_path), project_dir, "--simple"],
            capture_output=True,
            text=True,
            timeout=1,  # Very short timeout
            cwd=project_dir  # Run from project dir
        )
        if result.returncode == 0 and result.stdout.strip():
            token_str = f" • {result.stdout.strip()} tokens"
    except:
        # Silent fail - no tokens shown
        pass
    
    # Package manager
    pm = "📦"
    if os.path.exists(os.path.join(project_dir, 'pnpm-lock.yaml')):
        pm = "📦 pnpm"
    elif os.path.exists(os.path.join(project_dir, 'package-lock.json')):
        pm = "📦 npm"
    elif os.path.exists(os.path.join(project_dir, 'yarn.lock')):
        pm = "📦 yarn"
    
    # Git status
    git_parts = []
    try:
        # Branch
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=project_dir, capture_output=True, text=True, timeout=1)
        if result.returncode == 0:
            branch = result.stdout.strip()
            git_parts.append(f"🌿 {branch}")
        
        # Status
        result = subprocess.run(['git', 'status', '--porcelain'], cwd=project_dir, capture_output=True, text=True, timeout=1)
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            modified = sum(1 for l in lines if l[:2] in [' M', 'MM', 'AM'])
            untracked = sum(1 for l in lines if l[:2] == '??')
            staged = sum(1 for l in lines if l[0] in ['M', 'A', 'D', 'R'])
            
            if modified > 0:
                git_parts.append(f"✎ Modified: {modified}")
            if untracked > 0:
                git_parts.append(f"➕ New: {untracked}")
            if staged > 0:
                git_parts.append(f"↑ Staged: {staged}")
    except:
        pass
    
    # Build the complete line
    left = f"📁 {dir_name}"
    
    if file_count > 0:
        left += f"  │  📝 {file_count} files • {line_str}{token_str}"
    
    left += f"  │  {pm}"
    
    if git_parts:
        left += "  │  " + "  ".join(git_parts)
    
    # Output as single line with proper formatting
    sys.stdout.write(f"  ┌─  {left}\n")
    sys.stdout.write(f"  └─\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
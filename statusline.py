#!/usr/bin/env python3
"""
Claude Code status line with token counter integration.

- Reads workspace JSON from stdin
- Invokes the local repo-tokens tool for fast token counts (cached)
- Intended to be run via uv for isolated dependencies

Example:
  echo '{"workspace": {"project_dir": "/path/to/repo"}}' | \
    uv run --project ~/developer/apps/repo-tokens -- \
      python ~/developer/apps/repo-tokens/statusline.py
"""
import json
import sys
import os
import subprocess
from pathlib import Path

def get_token_count(directory):
    """Get token count from repo-tokens tool"""
    try:
        # Call our repo-tokens tool
        script_dir = Path(__file__).parent
        repo_tokens_path = script_dir / "repo-tokens.py"
        
        # Change to directory first to help with relative paths
        original_dir = os.getcwd()
        try:
            if os.path.exists(directory):
                os.chdir(directory)
            
            result = subprocess.run(
                [sys.executable, str(repo_tokens_path), ".", "--simple"],
                capture_output=True,
                text=True,
                timeout=2  # Should be fast with cache
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        finally:
            os.chdir(original_dir)
    except Exception as e:
        # Silent fail for status line
        pass
    return None

def format_git_status(directory):
    """Get git status information"""
    try:
        # Get branch name
        branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=1
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
        
        # Get modified/staged/untracked counts
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if status_result.returncode == 0:
            lines = status_result.stdout.strip().split('\n') if status_result.stdout else []
            modified = sum(1 for l in lines if l[:2] in [' M', 'MM', 'AM'])
            staged = sum(1 for l in lines if l[0] in ['M', 'A', 'D', 'R'])
            untracked = sum(1 for l in lines if l[:2] == '??')
            
            git_parts = []
            if branch:
                git_parts.append(f"🌿 {branch}")
            if modified > 0:
                git_parts.append(f"✎ Modified: {modified}")
            if untracked > 0:
                git_parts.append(f"➕ New: {untracked}")
            if staged > 0:
                git_parts.append(f"↑ Staged: {staged}")
                
            return "  ".join(git_parts) if git_parts else None
    except:
        pass
    return None

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
    
    # Count files and lines (quick approximation)
    try:
        file_count_result = subprocess.run(
            ['git', 'ls-files'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=1
        )
        file_count = len(file_count_result.stdout.strip().split('\n')) if file_count_result.stdout else 0
        
        # Quick line count (sample-based for speed)
        line_count_result = subprocess.run(
            ['git', 'ls-files', '-z'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=1
        )
        if line_count_result.returncode == 0:
            files = line_count_result.stdout.strip('\0').split('\0')[:100]  # Sample first 100 files
            total_lines = 0
            for f in files:
                try:
                    with open(os.path.join(project_dir, f), 'r') as file:
                        total_lines += sum(1 for _ in file)
                except:
                    pass
            # Estimate total based on sample
            if files and len(files) > 0:
                line_count = int((total_lines / len(files)) * file_count)
            else:
                line_count = 0
        else:
            line_count = 0
    except:
        file_count = 0
        line_count = 0
    
    # Format line count
    if line_count < 1000:
        line_str = f"{line_count} lines"
    else:
        line_str = f"{line_count//1000}k lines"
    
    # Get token count
    token_count = get_token_count(project_dir)
    
    # Detect package manager
    package_manager = "📦"
    if os.path.exists(os.path.join(project_dir, 'pnpm-lock.yaml')):
        package_manager = "📦 pnpm"
    elif os.path.exists(os.path.join(project_dir, 'package-lock.json')):
        package_manager = "📦 npm"
    elif os.path.exists(os.path.join(project_dir, 'yarn.lock')):
        package_manager = "📦 yarn"
    elif os.path.exists(os.path.join(project_dir, 'Cargo.toml')):
        package_manager = "📦 cargo"
    elif os.path.exists(os.path.join(project_dir, 'requirements.txt')):
        package_manager = "📦 pip"
    
    # Get git status
    git_status = format_git_status(project_dir)
    
    # Build status line
    parts = []
    
    # Left section: project info
    left_parts = [f"📁 {dir_name}"]
    
    file_info_parts = []
    if file_count > 0:
        file_info_parts.append(f"📝 {file_count} files")
    if line_count > 0:
        file_info_parts.append(line_str)
    if token_count:
        file_info_parts.append(f"{token_count} tokens")
        
    if file_info_parts:
        left_parts.append(" • ".join(file_info_parts))
    
    left_parts.append(package_manager)
    
    parts.append("  │  ".join(left_parts))
    
    # Right section: git status
    if git_status:
        parts.append(git_status)
    
    # Combine with separator
    status_line = "  │  ".join(parts)
    
    # Add decorative borders - single line output for Claude Code
    print(f"  ┌─  {status_line}")
    print(f"  └─")

if __name__ == "__main__":
    main()
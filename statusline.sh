#!/bin/bash

# Get JSON from stdin
json=$(cat)

# Extract project dir from JSON (fallback to current dir)
project_dir=$(echo "$json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('workspace',{}).get('project_dir','.'))" 2>/dev/null || echo ".")

# Change to project directory
cd "$project_dir" 2>/dev/null || cd .

# Get base name
dir_name=$(basename "$PWD")

# Count files
file_count=$(git ls-files 2>/dev/null | wc -l | xargs)

# Count lines (quick estimate)
line_count=$(git ls-files 2>/dev/null | head -100 | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
if [ -n "$line_count" ] && [ "$line_count" -gt 0 ]; then
    # Estimate total based on sample
    total_files=$(git ls-files 2>/dev/null | wc -l)
    estimated_lines=$((line_count * total_files / 100))
    if [ "$estimated_lines" -gt 1000 ]; then
        lines_str="$((estimated_lines / 1000))k lines"
    else
        lines_str="$estimated_lines lines"
    fi
else
    lines_str="? lines"
fi

# Get token count (with timeout)
tokens=$(timeout 1 python3 ~/Developer/apps/repo-tokens/repo-tokens.py . --simple 2>/dev/null)
if [ -n "$tokens" ]; then
    tokens_str=" • $tokens tokens"
else
    tokens_str=""
fi

# Package manager
if [ -f "pnpm-lock.yaml" ]; then
    pm="📦 pnpm"
elif [ -f "package-lock.json" ]; then
    pm="📦 npm"
elif [ -f "yarn.lock" ]; then
    pm="📦 yarn"
else
    pm="📦"
fi

# Git branch
branch=$(git branch --show-current 2>/dev/null)
if [ -n "$branch" ]; then
    git_branch="🌿 $branch"
else
    git_branch=""
fi

# Git status
git_status=""
if command -v git &> /dev/null; then
    modified=$(git status --porcelain 2>/dev/null | grep -c "^ M")
    untracked=$(git status --porcelain 2>/dev/null | grep -c "^??")
    staged=$(git status --porcelain 2>/dev/null | grep -c "^[MADR]")
    
    if [ "$modified" -gt 0 ]; then
        git_status="$git_status  ✎ Modified: $modified"
    fi
    if [ "$untracked" -gt 0 ]; then
        git_status="$git_status  ➕ New: $untracked"
    fi
    if [ "$staged" -gt 0 ]; then
        git_status="$git_status  ↑ Staged: $staged"
    fi
fi

# Build status line
echo "  ┌─  📁 $dir_name  │  📝 $file_count files • ${lines_str}${tokens_str}  │  $pm  │  $git_branch$git_status"
echo "  └─"
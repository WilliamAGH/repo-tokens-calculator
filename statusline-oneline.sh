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

# Count lines (quick estimate from first 50 files)
line_sample=$(git ls-files 2>/dev/null | head -50 | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
if [ -n "$line_sample" ] && [ "$line_sample" -gt 0 ]; then
    total_files=$(git ls-files 2>/dev/null | wc -l)
    estimated_lines=$((line_sample * total_files / 50))
    if [ "$estimated_lines" -gt 1000 ]; then
        lines_str="$((estimated_lines / 1000))k lines"
    else
        lines_str="$estimated_lines lines"
    fi
else
    lines_str="0 lines"
fi

# Token counting removed per user request

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

# Git status (simplified)
git_status=""
if command -v git &> /dev/null; then
    modified=$(git status --porcelain 2>/dev/null | grep -c "^ M")
    untracked=$(git status --porcelain 2>/dev/null | grep -c "^??")
    
    if [ "$modified" -gt 0 ]; then
        git_status="$git_status ✎$modified"
    fi
    if [ "$untracked" -gt 0 ]; then
        git_status="$git_status +$untracked"
    fi
fi

# Build SINGLE LINE status
echo -n "📁 $dir_name | 📝 ${file_count} • ${lines_str} | $pm | $git_branch$git_status"
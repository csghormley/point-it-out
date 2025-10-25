#!/bin/bash
#
# Install git hooks from .githooks directory
#
# This script creates symlinks from .git/hooks to .githooks
# so the versioned hooks are used by git
#

set -e

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.githooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Installing git hooks..."
echo ""

# Ensure .githooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${YELLOW}Warning: .githooks directory not found${NC}"
    exit 1
fi

# Install each hook
for hook in "$HOOKS_DIR"/*; do
    # Skip this install script
    if [ "$(basename "$hook")" = "install-hooks.sh" ]; then
        continue
    fi

    # Skip README files
    if [ "$(basename "$hook")" = "README.md" ]; then
        continue
    fi

    hook_name=$(basename "$hook")

    # Check if hook already exists
    if [ -e "$GIT_HOOKS_DIR/$hook_name" ] && [ ! -L "$GIT_HOOKS_DIR/$hook_name" ]; then
        echo -e "${YELLOW}Backing up existing $hook_name to ${hook_name}.backup${NC}"
        mv "$GIT_HOOKS_DIR/$hook_name" "$GIT_HOOKS_DIR/${hook_name}.backup"
    fi

    # Remove existing symlink if present
    if [ -L "$GIT_HOOKS_DIR/$hook_name" ]; then
        rm "$GIT_HOOKS_DIR/$hook_name"
    fi

    # Create symlink
    ln -s "../../.githooks/$hook_name" "$GIT_HOOKS_DIR/$hook_name"
    chmod +x "$hook"

    echo -e "${GREEN}✓ Installed $hook_name${NC}"
done

echo ""
echo -e "${GREEN}Git hooks installed successfully!${NC}"
echo ""
echo "Installed hooks will run automatically on git commands."
echo "To bypass a hook temporarily, use --no-verify flag:"
echo "  git commit --no-verify"

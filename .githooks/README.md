# Git Hooks

This directory contains version-controlled git hooks for the project.

## Available Hooks

### pre-commit

Runs `./mapcfg check` before allowing commits. The commit will be blocked if any checks fail.

## Installation

To install these hooks for your local repository:

```bash
./.githooks/install-hooks.sh
```

This creates symlinks from `.git/hooks/` to `.githooks/` so git will use the versioned hooks.

## Usage

Once installed, hooks run automatically:

```bash
git commit -m "Your message"
# Pre-commit hook runs automatically
```

## Adding New Hooks

1. Create a new executable script in `.githooks/`
2. Make it executable: `chmod +x .githooks/your-hook`
3. Run `./.githooks/install-hooks.sh` to install it
4. Commit the new hook to the repository

## Uninstalling Hooks

To remove installed hooks:

```bash
rm .git/hooks/pre-commit
# Restore backup if needed
mv .git/hooks/pre-commit.backup .git/hooks/pre-commit
```

## Why Version-Controlled Hooks?

Git hooks in `.git/hooks/` are not version-controlled by default. By storing them in `.githooks/` and using symlinks, we can:

- Share hooks across the team
- Version and track changes to hooks
- Make hook setup easy for new developers
- Ensure consistent quality checks across all contributors

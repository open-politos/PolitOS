"""PolitOS CLI — project scaffolding."""

import shutil
import sys
from importlib.resources import files
from pathlib import Path


def init():
    """Initialize a new PolitOS organization in the current directory.

    Copies scaffold files (constitution, agents, governance config, etc.)
    into the current working directory and creates a .env from the template.
    """
    cwd = Path.cwd()
    scaffold = files("src.scaffold")

    # Check if already initialized
    marker_files = ["constitution/core-principles.yaml", "agents/setup/steps.yaml"]
    existing = [f for f in marker_files if (cwd / f).exists()]
    if existing:
        print(f"This directory already contains PolitOS files ({', '.join(existing)}).")
        print("Use --force to overwrite.")
        if "--force" not in sys.argv:
            sys.exit(1)

    # Copy scaffold tree
    scaffold_path = Path(str(scaffold))
    if not scaffold_path.is_dir():
        print("Error: scaffold data not found in installed package.", file=sys.stderr)
        sys.exit(1)

    copied = 0
    for src_file in scaffold_path.rglob("*"):
        if src_file.is_dir() or src_file.name == "__init__.py" or "__pycache__" in src_file.parts:
            continue

        rel = src_file.relative_to(scaffold_path)
        dest = cwd / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        # .env.example → .env (don't overwrite existing .env)
        if rel.name == ".env.example":
            env_dest = cwd / ".env"
            if not env_dest.exists():
                shutil.copy2(src_file, env_dest)
                copied += 1
                print(f"  created  .env")
            else:
                print(f"  skipped  .env (already exists)")
            continue

        if dest.exists() and "--force" not in sys.argv:
            print(f"  skipped  {rel} (already exists)")
            continue

        shutil.copy2(src_file, dest)
        copied += 1
        print(f"  created  {rel}")

    # Create empty directories that might be needed
    for d in ["data", "knowledge-base", "governance/proposals", "governance/decisions"]:
        (cwd / d).mkdir(parents=True, exist_ok=True)

    print(f"\nPolitOS initialized ({copied} files created).")
    print("\nNext steps:")
    print("  1. Edit .env and add your ANTHROPIC_API_KEY")
    print("  2. Start the MCP server:  politos-mcp")
    print("  3. Or use Claude Code:    cd here && claude")

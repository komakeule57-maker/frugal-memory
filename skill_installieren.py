"""Legt den Skill frugal-memory nach ~/.claude/skills/ (Befehl `frugal-memory-skill`).

Der Skill traegt die Arbeitsregeln (recall vor dem Dateisuchen, ein Fakt je
Eintrag, abloesen statt anhaeufen ...). Im Repo liegt er unter
skills/frugal-memory/, im Paket als Paketdaten `frugal_memory_skill` - wer
per pip oder uvx installiert, hat kein Repo zum Kopieren.

    frugal-memory-skill            # nach ~/.claude/skills/frugal-memory/
    frugal-memory-skill --ziel DIR # anderer Skill-Ordner, z. B. .claude/skills im Projekt
    frugal-memory-skill --force    # vorhandene SKILL.md ueberschreiben
"""

import argparse
import sys
from importlib import resources
from pathlib import Path


def skill_text() -> str:
    """Der Text des Skills: aus dem installierten Paket, sonst aus dem Repo daneben."""
    try:
        return resources.files("frugal_memory_skill").joinpath("SKILL.md").read_text(encoding="utf-8")
    except (ModuleNotFoundError, FileNotFoundError):
        return (Path(__file__).parent / "skills" / "frugal-memory" / "SKILL.md").read_text(encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="frugal-memory-skill",
                                description="Install the frugal-memory skill for Claude Code.")
    p.add_argument("--ziel", "--target", dest="ziel", default=str(Path.home() / ".claude" / "skills"),
                   help="skills directory (default: ~/.claude/skills)")
    p.add_argument("--force", action="store_true", help="overwrite an existing SKILL.md")
    a = p.parse_args(argv)
    datei = Path(a.ziel).expanduser() / "frugal-memory" / "SKILL.md"
    neu = skill_text()
    if datei.exists() and not a.force:
        if datei.read_text(encoding="utf-8") == neu:
            print(f"Already up to date: {datei}")
            return 0
        print(f"{datei} exists and differs - left untouched. Use --force to overwrite.", file=sys.stderr)
        return 1
    datei.parent.mkdir(parents=True, exist_ok=True)
    datei.write_text(neu, encoding="utf-8")
    print(f"Installed: {datei}\nClaude Code picks it up in the next session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

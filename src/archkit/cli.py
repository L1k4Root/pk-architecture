"""Command line interface.

archkit adr new "Use PostgreSQL for idempotency keys" [--dir docs/adr]
archkit adr index [--dir docs/adr] [--check]
archkit lint [docs]
archkit init [target]          copy the arc42 + ADR template into a repository
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from archkit import adr, lint


def template_dir() -> Path:
    """The docs template: inside the installed wheel, or at the repository root in development."""
    here = Path(__file__).resolve().parent
    for candidate in (here / "template" / "docs", here.parents[1] / "template" / "docs"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("archkit template not found")  # pragma: no cover


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="archkit", description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    adr_parser = commands.add_parser("adr", help="Architecture Decision Records")
    adr_commands = adr_parser.add_subparsers(dest="adr_command", required=True)
    new = adr_commands.add_parser("new", help="create a new ADR")
    new.add_argument("title")
    new.add_argument("--dir", type=Path, default=Path("docs/adr"))
    index = adr_commands.add_parser("index", help="regenerate docs/adr/README.md")
    index.add_argument("--dir", type=Path, default=Path("docs/adr"))
    index.add_argument("--check", action="store_true", help="fail if the index is out of date")

    lint_parser = commands.add_parser("lint", help="lint architecture docs")
    lint_parser.add_argument("root", nargs="?", type=Path, default=Path("docs"))

    init = commands.add_parser("init", help="copy the documentation template")
    init.add_argument("target", nargs="?", type=Path, default=Path("."))

    args = parser.parse_args(argv)

    if args.command == "adr" and args.adr_command == "new":
        path = adr.create(args.dir, args.title)
        (args.dir / adr.INDEX_FILE).write_text(adr.render_index(args.dir), encoding="utf-8")
        print(path)
        return 0

    if args.command == "adr" and args.adr_command == "index":
        rendered = adr.render_index(args.dir)
        index_path = args.dir / adr.INDEX_FILE
        if args.check:
            current = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
            if current != rendered:
                print(f"{index_path} is out of date; run `archkit adr index`", file=sys.stderr)
                return 1
            return 0
        index_path.write_text(rendered, encoding="utf-8")
        print(index_path)
        return 0

    if args.command == "lint":
        if not args.root.is_dir():
            print(f"{args.root} is not a directory", file=sys.stderr)
            return 1
        findings = lint.lint_docs(args.root)
        for finding in findings:
            print(finding)
        print(f"{len(findings)} problem(s)" if findings else "docs OK", file=sys.stderr)
        return 1 if findings else 0

    # init
    destination = args.target / "docs"
    if destination.exists() and any(destination.iterdir()):
        print(f"{destination} already exists and is not empty", file=sys.stderr)
        return 1
    shutil.copytree(template_dir(), destination, dirs_exist_ok=True)
    print(f"created {destination}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

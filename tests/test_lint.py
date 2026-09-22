from pathlib import Path

import pytest

from archkit import adr, lint

VALID = """# {n:04d}. Title

- Status: {status}
- Date: {date}
- Deciders: team

## Context

Why.

## Decision

What.

## Consequences

So what.
"""


def write_adr(
    directory: Path, n: int, *, status: str = "accepted", day: str = "2026-01-01"
) -> Path:
    path = directory / f"{n:04d}-decision-{n}.md"
    path.write_text(VALID.format(n=n, status=status, date=day))
    return path


def rules(findings: list[lint.Finding]) -> list[str]:
    return sorted(f.rule for f in findings)


@pytest.fixture
def adr_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "adr"
    directory.mkdir()
    return directory


def refresh_index(directory: Path) -> None:
    (directory / adr.INDEX_FILE).write_text(adr.render_index(directory))


def test_valid_adrs_have_no_findings(adr_dir: Path) -> None:
    write_adr(adr_dir, 1)
    write_adr(adr_dir, 2, status="superseded by [0001](0001-decision-1.md)")
    refresh_index(adr_dir)

    assert lint.lint_adrs(adr_dir) == []


def test_bad_file_name(adr_dir: Path) -> None:
    (adr_dir / "1-Bad_Name.md").write_text("# x\n")

    assert "ADR001" in rules(lint.lint_adrs(adr_dir))


def test_title_problems(adr_dir: Path) -> None:
    (adr_dir / "0001-no-title.md").write_text(
        VALID.format(n=1, status="accepted", date="2026-01-01").replace("# 0001. Title", "Title")
    )
    wrong = write_adr(adr_dir, 2)
    wrong.write_text(wrong.read_text().replace("# 0002.", "# 0009."))
    refresh_index(adr_dir)

    assert rules(lint.lint_adrs(adr_dir)) == ["ADR002", "ADR002"]


def test_duplicate_numbers(adr_dir: Path) -> None:
    write_adr(adr_dir, 1)
    (adr_dir / "0001-another.md").write_text(
        VALID.format(n=1, status="accepted", date="2026-01-01")
    )
    refresh_index(adr_dir)

    assert rules(lint.lint_adrs(adr_dir)) == ["ADR003"]


def test_status_and_supersession(adr_dir: Path) -> None:
    write_adr(adr_dir, 1, status="approved")
    write_adr(adr_dir, 2, status="superseded by [0009](0009-missing.md)")
    refresh_index(adr_dir)

    assert rules(lint.lint_adrs(adr_dir)) == ["ADR004", "ADR005"]


def test_date_format(adr_dir: Path) -> None:
    write_adr(adr_dir, 1, day="22/09/2026")
    refresh_index(adr_dir)

    assert rules(lint.lint_adrs(adr_dir)) == ["ADR006"]


def test_missing_or_empty_sections(adr_dir: Path) -> None:
    path = write_adr(adr_dir, 1)
    path.write_text(
        path.read_text().replace("## Consequences\n\nSo what.\n", "## Consequences\n\n")
    )
    refresh_index(adr_dir)

    findings = lint.lint_adrs(adr_dir)
    assert rules(findings) == ["ADR007"]
    assert "Consequences" in findings[0].message


def test_stale_or_missing_index(adr_dir: Path) -> None:
    write_adr(adr_dir, 1)
    assert rules(lint.lint_adrs(adr_dir)) == ["ADR008"]

    refresh_index(adr_dir)
    write_adr(adr_dir, 2)
    assert rules(lint.lint_adrs(adr_dir)) == ["ADR008"]


def test_links_and_mermaid(tmp_path: Path) -> None:
    (tmp_path / "exists.md").write_text("# ok\n")
    (tmp_path / "doc.md").write_text(
        "[ok](exists.md) [anchor](exists.md#section) [same page](#top) [web](https://example.com)\n"
        "[mail](mailto:a@b.c) `[example](not-a-link.md)` ![img](missing.png) [broken](nope.md)\n"
        "```mermaid\nflowchart LR\n  a --> b\n```\n"
        "```mermaid\nnotAType\n```\n"
        "```\n[inside code](ignored.md)\n```\n"
    )

    findings = lint.lint_markdown(tmp_path)

    assert [(f.rule, f.line) for f in findings] == [("DOC001", 2), ("DOC001", 2), ("DOC002", 8)]
    assert "missing.png" in findings[0].message


def test_arc42_sections(tmp_path: Path) -> None:
    (tmp_path / "01-introduction-and-goals.md").write_text("# 1\n")

    findings = lint.lint_arc42(tmp_path)

    assert len(findings) == len(lint.ARC42_REQUIRED) - 1
    assert all(f.rule == "DOC003" for f in findings)


def test_finding_format() -> None:
    assert str(lint.Finding("DOC001", Path("a.md"), "broken", 3)) == "a.md:3: DOC001 broken"
    assert str(lint.Finding("DOC003", Path("dir"), "missing")) == "dir: DOC003 missing"


def test_the_shipped_template_is_valid() -> None:
    template = Path(__file__).resolve().parents[1] / "template" / "docs"
    assert lint.lint_docs(template) == []

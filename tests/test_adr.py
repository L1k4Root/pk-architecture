from datetime import date
from pathlib import Path

from archkit import adr


def test_slugify() -> None:
    assert (
        adr.slugify("Use PostgreSQL for Idempotency Keys!") == "use-postgresql-for-idempotency-keys"
    )
    assert adr.slugify("  --  ") == "decision"


def test_create_numbers_sequentially_and_parses_back(tmp_path: Path) -> None:
    first = adr.create(tmp_path, "Use EdDSA for tokens", today=date(2026, 9, 22))
    second = adr.create(tmp_path, "Adopt OpenTelemetry")

    assert first.name == "0001-use-eddsa-for-tokens.md"
    assert second.name == "0002-adopt-opentelemetry.md"

    record = adr.parse(first)
    assert record.number == 1
    assert record.title == "Use EdDSA for tokens"
    assert record.status == "proposed"
    assert record.date == "2026-09-22"
    assert set(adr.REQUIRED_SECTIONS) <= set(record.sections)
    assert all(record.sections[s] for s in adr.REQUIRED_SECTIONS)


def test_load_all_skips_template_index_and_other_files(tmp_path: Path) -> None:
    adr.create(tmp_path, "One")
    (tmp_path / adr.TEMPLATE_FILE).write_text("# 0000. Template\n")
    (tmp_path / adr.INDEX_FILE).write_text("# index\n")
    (tmp_path / "notes.md").write_text("# notes\n")

    assert [r.number for r in adr.load_all(tmp_path)] == [1]


def test_superseded_by(tmp_path: Path) -> None:
    path = tmp_path / "0001-old.md"
    path.write_text(
        "# 0001. Old\n\n- Status: superseded by [0002](0002-new.md)\n- Date: 2026-01-01\n"
    )

    assert adr.parse(path).superseded_by == "0002-new.md"
    assert adr.parse(adr.create(tmp_path, "New")).superseded_by is None


def test_metadata_is_only_read_before_the_first_section(tmp_path: Path) -> None:
    path = tmp_path / "0001-x.md"
    path.write_text(
        "# 0001. X\n\n- Status: accepted\n- Date: 2026-01-01\n\n"
        "## Context\n\n- Status: this bullet is content, not metadata\n"
    )

    record = adr.parse(path)
    assert record.status == "accepted"
    assert "this bullet is content" in record.sections["Context"]


def test_render_index(tmp_path: Path) -> None:
    adr.create(tmp_path, "First decision", today=date(2026, 1, 2))

    index = adr.render_index(tmp_path)

    assert "| [0001](0001-first-decision.md) | First decision | proposed | 2026-01-02 |" in index
    assert index.startswith("# Architecture Decision Records")

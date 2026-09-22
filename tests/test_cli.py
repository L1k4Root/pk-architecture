from pathlib import Path

import pytest

from archkit.cli import main


def test_init_new_index_and_lint(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["init", str(tmp_path)]) == 0
    docs = tmp_path / "docs"
    assert (docs / "architecture" / "05-building-block-view.md").exists()
    assert main(["lint", str(docs)]) == 0

    assert (
        main(["adr", "new", "Use PostgreSQL for idempotency keys", "--dir", str(docs / "adr")]) == 0
    )
    created = docs / "adr" / "0002-use-postgresql-for-idempotency-keys.md"
    assert created.exists()
    assert main(["adr", "index", "--dir", str(docs / "adr"), "--check"]) == 0
    assert main(["lint", str(docs)]) == 0
    assert "docs OK" in capsys.readouterr().err


def test_init_refuses_to_overwrite(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "keep.md").write_text("mine")

    assert main(["init", str(tmp_path)]) == 1


def test_index_check_detects_drift(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    adr_dir = tmp_path / "adr"
    main(["adr", "new", "First", "--dir", str(adr_dir)])
    (adr_dir / "README.md").write_text("stale")

    assert main(["adr", "index", "--dir", str(adr_dir), "--check"]) == 1
    assert "out of date" in capsys.readouterr().err
    assert main(["adr", "index", "--dir", str(adr_dir)]) == 0
    assert main(["adr", "index", "--dir", str(adr_dir), "--check"]) == 0


def test_index_check_without_index(tmp_path: Path) -> None:
    (tmp_path / "adr").mkdir()
    (tmp_path / "adr" / "0001-x.md").write_text("# 0001. X\n")

    assert main(["adr", "index", "--dir", str(tmp_path / "adr"), "--check"]) == 1


def test_lint_reports_findings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "doc.md").write_text("[broken](missing.md)\n")

    assert main(["lint", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert "DOC001 broken link: missing.md" in captured.out
    assert "1 problem(s)" in captured.err


def test_lint_requires_a_directory(tmp_path: Path) -> None:
    assert main(["lint", str(tmp_path / "missing")]) == 1

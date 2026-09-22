"""Lint architecture documentation.

Rules (each finding carries the rule id, so it can be looked up in the README):

  ADR001  file name must be NNNN-kebab-case.md
  ADR002  title must be "# NNNN. Title" with the same number as the file
  ADR003  numbers must be unique
  ADR004  status must be proposed|accepted|rejected|deprecated|superseded by [NNNN](file)
  ADR005  a superseding ADR must exist
  ADR006  date must be an ISO date (YYYY-MM-DD)
  ADR007  Context, Decision and Consequences sections must exist and not be empty
  ADR008  the ADR index (README.md) must be up to date
  DOC001  relative links must point to existing files
  DOC002  mermaid blocks must start with a known diagram type
  DOC003  required arc42 sections must exist
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from archkit import adr as adrs

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^```(\w*)\s*$")
INLINE_CODE = re.compile(r"`[^`]*`")
MERMAID_TYPES = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "C4Context",
    "C4Container",
    "C4Component",
    "C4Dynamic",
    "C4Deployment",
    "gantt",
    "timeline",
    "mindmap",
    "architecture-beta",
)

# arc42 sections this template requires (file name prefixes in docs/architecture/).
ARC42_REQUIRED = (
    "01-introduction-and-goals",
    "03-context-and-scope",
    "04-solution-strategy",
    "05-building-block-view",
    "06-runtime-view",
    "07-deployment-view",
    "08-crosscutting-concepts",
    "09-architecture-decisions",
    "10-quality-requirements",
    "11-risks-and-technical-debt",
)


@dataclass(frozen=True)
class Finding:
    rule: str
    path: Path
    message: str
    line: int = 0

    def __str__(self) -> str:
        location = f"{self.path}:{self.line}" if self.line else str(self.path)
        return f"{location}: {self.rule} {self.message}"


def lint_adrs(directory: Path) -> list[Finding]:
    findings: list[Finding] = []
    files = [
        p
        for p in sorted(directory.glob("*.md"))
        if p.name not in (adrs.INDEX_FILE, adrs.TEMPLATE_FILE)
    ]
    seen: dict[int, Path] = {}

    for path in files:
        if not adrs.FILENAME.match(path.name):
            findings.append(Finding("ADR001", path, "file name must be NNNN-kebab-case.md"))
            continue
        record = adrs.parse(path)

        if not record.title:
            findings.append(Finding("ADR002", path, 'missing title "# NNNN. Title"'))
        else:
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
            title_match = adrs.TITLE.match(first_line)
            if not title_match or int(title_match.group(1)) != record.number:
                findings.append(Finding("ADR002", path, "title number must match the file name", 1))

        if record.number in seen:
            findings.append(
                Finding(
                    "ADR003",
                    path,
                    f"number {record.number:04d} also used by {seen[record.number].name}",
                )
            )
        seen.setdefault(record.number, path)

        if record.status not in adrs.STATUSES:
            superseded = record.superseded_by
            if superseded is None:
                findings.append(
                    Finding(
                        "ADR004",
                        path,
                        f"invalid status {record.status!r}; use one of "
                        f"{', '.join(adrs.STATUSES)} or 'superseded by [NNNN](file.md)'",
                    )
                )
            elif not (directory / superseded).exists():
                findings.append(
                    Finding("ADR005", path, f"superseding ADR {superseded} does not exist")
                )

        try:
            date.fromisoformat(record.date)
        except ValueError:
            findings.append(
                Finding("ADR006", path, f"invalid date {record.date!r}, use YYYY-MM-DD")
            )

        for section in adrs.REQUIRED_SECTIONS:
            if not record.sections.get(section):
                findings.append(
                    Finding("ADR007", path, f"section '## {section}' is missing or empty")
                )

    index = directory / adrs.INDEX_FILE
    if files and (
        not index.exists() or index.read_text(encoding="utf-8") != adrs.render_index(directory)
    ):
        findings.append(Finding("ADR008", index, "index is out of date; run `archkit adr index`"))
    return findings


def lint_markdown(root: Path) -> list[Finding]:
    """Broken relative links and malformed mermaid blocks in every Markdown file."""
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.md")):
        in_fence = False
        mermaid_start = 0
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            fence = FENCE.match(line.strip())
            if fence and not in_fence:
                in_fence = True
                mermaid_start = number if fence.group(1) == "mermaid" else 0
                continue
            if line.strip() == "```" and in_fence:
                in_fence = False
                continue
            if in_fence:
                if mermaid_start == number - 1:
                    kind = line.strip().split(" ")[0]
                    if kind not in MERMAID_TYPES:
                        findings.append(
                            Finding(
                                "DOC002", path, f"unknown mermaid diagram type {kind!r}", number
                            )
                        )
                continue
            # Links inside `inline code` are examples, not links.
            for match in LINK.finditer(INLINE_CODE.sub("", line)):
                target = match.group(1) or match.group(2)
                if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                    continue  # absolute URL, mailto:, or same-page anchor
                file_part = target.split("#", 1)[0]
                if file_part and not (path.parent / file_part).exists():
                    findings.append(Finding("DOC001", path, f"broken link: {target}", number))
    return findings


def lint_arc42(directory: Path) -> list[Finding]:
    names = {p.stem for p in directory.glob("*.md")}
    return [
        Finding("DOC003", directory, f"missing arc42 section {section}.md")
        for section in ARC42_REQUIRED
        if section not in names
    ]


def lint_docs(root: Path) -> list[Finding]:
    """Lint a docs root that contains `architecture/` and/or `adr/`."""
    findings = lint_markdown(root)
    if (root / "architecture").is_dir():
        findings += lint_arc42(root / "architecture")
    if (root / "adr").is_dir():
        findings += lint_adrs(root / "adr")
    return findings

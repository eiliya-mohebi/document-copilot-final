"""Compact SEC HTML tables before chunking.

SEC filings lay tables out with dozens of empty spacer columns, duplicated
cells from colspans, split header rows, and '$'-only columns. Docling keeps
that grid verbatim, which makes chunk serialization emit one garbage
"key, N = ." pair per phantom cell. Compaction merges/drops those artifacts
so chunks read "Money market funds, 2020 Fair Value = 2,171".
"""

from __future__ import annotations

from docling_core.types.doc.document import TableCell, TableData

_NOISE = ("", "$", ".")


def compact_table(data: TableData) -> TableData | None:
    """Return a compacted copy of the table, or None to keep the original."""
    grid = [[(cell.text or "").strip() for cell in row] for row in data.grid]
    if not grid:
        return None
    ncols = max(len(row) for row in grid)
    grid = [row + [""] * (ncols - len(row)) for row in grid]

    columns = [[row[j] for row in grid] for j in range(ncols)]
    merged: list[list[str]] = []
    for column in columns:
        if merged and _mergeable(merged[-1], column):
            merged[-1] = _merge(merged[-1], column)
        else:
            merged.append(column)
    merged = [col for col in merged if any(c not in _NOISE for c in col)]
    if not merged:
        return None

    rows = [[col[i] for col in merged] for i in range(len(grid))]
    rows = [row for row in rows if any(c not in _NOISE for c in row)]
    if not rows:
        return None

    rows, n_header = _collapse_header_rows(rows)

    cells = [
        TableCell(
            text=text,
            start_row_offset_idx=i,
            end_row_offset_idx=i + 1,
            start_col_offset_idx=j,
            end_col_offset_idx=j + 1,
            column_header=i < n_header,
        )
        for i, row in enumerate(rows)
        for j, text in enumerate(row)
    ]
    return TableData(num_rows=len(rows), num_cols=len(merged), table_cells=cells)


def _mergeable(a: list[str], b: list[str]) -> bool:
    """Adjacent columns merge when every row agrees: equal, or one side is noise.

    Handles both colspan duplication (same text repeated) and the '$' sign
    rendered in its own column next to the amount.
    """
    return all(
        x in _NOISE or y in _NOISE or x == y for x, y in zip(a, b, strict=True)
    )


def _merge(a: list[str], b: list[str]) -> list[str]:
    return [x if x not in _NOISE else y for x, y in zip(a, b, strict=True)]


def _collapse_header_rows(rows: list[list[str]]) -> tuple[list[list[str]], int]:
    """SEC tables have no <th>; leading rows with an empty first cell are
    headers (e.g. a year row above a label row). Collapse them into one."""
    n_header = 0
    while n_header < len(rows) - 1 and not rows[n_header][0]:
        n_header += 1
    if n_header > 1:
        combined = [
            " ".join(filter(None, (row[j] for row in rows[:n_header])))
            for j in range(len(rows[0]))
        ]
        rows = [combined] + rows[n_header:]
    return rows, min(n_header, 1)

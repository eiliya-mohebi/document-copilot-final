"""Compaction of SEC-style sparse tables before chunk serialization."""

from __future__ import annotations

from docling_core.types.doc.document import TableCell, TableData

from ingest.tables import compact_table


def make_table(rows: list[list[str]]) -> TableData:
    cells = [
        TableCell(
            text=text,
            start_row_offset_idx=i,
            end_row_offset_idx=i + 1,
            start_col_offset_idx=j,
            end_col_offset_idx=j + 1,
        )
        for i, row in enumerate(rows)
        for j, text in enumerate(row)
    ]
    return TableData(num_rows=len(rows), num_cols=len(rows[0]), table_cells=cells)


def grid_texts(data: TableData) -> list[list[str]]:
    return [[cell.text for cell in row] for row in data.grid]


def test_drops_empty_spacer_columns_and_rows():
    table = make_table(
        [
            ["Label", "", "Value", ""],
            ["Cash", "", "17,305", ""],
            ["", "", "", ""],
        ]
    )

    compacted = compact_table(table)

    assert grid_texts(compacted) == [["Label", "Value"], ["Cash", "17,305"]]


def test_merges_colspan_duplicates_and_dollar_columns():
    # SEC layout: label repeated across colspan cells, '$' in its own column.
    table = make_table(
        [
            ["Cash", "Cash", "Cash", "$", "17,305"],
            ["Money market funds", "Money market funds", "Money market funds", "", "9,608"],
        ]
    )

    compacted = compact_table(table)

    assert grid_texts(compacted) == [
        ["Cash", "17,305"],
        ["Money market funds", "9,608"],
    ]


def test_collapses_split_header_rows_into_one():
    table = make_table(
        [
            ["", "2021", "2021"],
            ["", "Adjusted Cost", "Fair Value"],
            ["Cash", "17,305", "17,305"],
        ]
    )

    compacted = compact_table(table)

    grid = grid_texts(compacted)
    assert grid[0] == ["", "2021 Adjusted Cost", "2021 Fair Value"]
    assert grid[1] == ["Cash", "17,305", "17,305"]
    assert all(cell.column_header for cell in compacted.grid[0])
    assert not any(cell.column_header for cell in compacted.grid[1])


def test_all_noise_table_returns_none():
    table = make_table([["", "$", ""], ["", "", ""]])

    assert compact_table(table) is None

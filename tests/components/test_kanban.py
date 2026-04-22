from __future__ import annotations

from dashing_boards.components.kanban.component import _render_board


def test_render_board_produces_one_column_per_config() -> None:
    rows = [
        {"id": "1", "title": "A", "status": "todo"},
        {"id": "2", "title": "B", "status": "doing"},
        {"id": "3", "title": "C", "status": "todo"},
    ]
    columns = _render_board(rows, ["todo", "doing", "done"], "status", "title", "id", "sid", "aio")
    assert len(columns) == 3

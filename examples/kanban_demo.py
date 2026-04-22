"""Kanban demo. Click ◀/▶ on a card to move it between columns."""

from __future__ import annotations

from dash import Dash

from dashing_boards import DataType, KanbanBoard, Page, StaticData

rows = [
    {"id": "1", "title": "Write requirements", "status": "done"},
    {"id": "2", "title": "Build MVP", "status": "doing"},
    {"id": "3", "title": "Add Kanban v2 with real drag", "status": "todo"},
    {"id": "4", "title": "Write docs", "status": "todo"},
]
source = StaticData(rows, DataType.DATAFRAME, source_id="board")

app = Dash(__name__)
app.layout = Page(
    [KanbanBoard(source, columns=["todo", "doing", "done"]), source.store()],
    title="Kanban demo (MVP)",
    subtitle="Python-only. Native drag-and-drop coming later via dnd-kit.",
)

if __name__ == "__main__":
    app.run(debug=True)

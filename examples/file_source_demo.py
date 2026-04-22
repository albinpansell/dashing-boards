"""FileDataSource demo - a CSV file wired to a Table with 2-way writes.

Edits in the Table atomically overwrite the CSV on disk.
"""

from __future__ import annotations

from pathlib import Path

from dash import Dash

from dashing_boards import FileDataSource, Page, Table


csv_path = Path(__file__).parent / "_tasks.csv"
if not csv_path.exists():
    csv_path.write_text("id,title,status\n1,Write docs,todo\n2,Ship PR,doing\n3,Take break,done\n")

source = FileDataSource(csv_path, writable=True, watch=True, source_id="tasks")

app = Dash(__name__)
app.layout = Page(
    [Table(source, editable=True), source.store()],
    title="File source demo",
    subtitle=f"Bound to {csv_path.name}. Edits persist to disk.",
)

if __name__ == "__main__":
    app.run(debug=True)

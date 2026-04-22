from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from dash import MATCH, Input, Output, State, callback, callback_context, dcc, html
from dash.exceptions import PreventUpdate

from .source import PollingDataSource, WritableDataSource, _store_id
from .types import DataType

_SUPPORTED_FORMATS = {"csv", "tsv", "json", "jsonl", "yaml", "parquet", "md", "txt"}


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"yml", "yaml"}:
        return "yaml"
    if suffix == "markdown":
        return "md"
    if suffix in _SUPPORTED_FORMATS:
        return suffix
    return "txt"


def _mtime_id(source_id: str) -> dict[str, str]:
    return {"component": "DataSource", "sub": "file_mtime", "source_id": source_id}


class FileDataSource(PollingDataSource, WritableDataSource):
    """Read (and optionally write) a local file as a DataSource.

    Watching: when `watch=True`, a `dcc.Interval` polls `os.stat(mtime)`
    every `watch_interval_s` seconds. When the mtime changes, the file
    is re-read and the Store updated. Polling is dependency-free; fine
    for local single-user dashboards.

    Safety: if `root_dir` is set, the path must be inside it. Writes
    outside the root raise.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        format: str = "auto",
        data_type: DataType | None = None,
        writable: bool = False,
        watch: bool = False,
        watch_interval_s: float = 2.0,
        root_dir: str | os.PathLike[str] | None = None,
        source_id: str | None = None,
    ) -> None:
        resolved = Path(path).resolve()
        if root_dir is not None:
            root = Path(root_dir).resolve()
            try:
                resolved.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"Path {resolved} is outside root {root}") from exc

        fmt = _detect_format(resolved) if format == "auto" else format
        if fmt not in _SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format '{fmt}'")

        inferred_type = _default_data_type(fmt) if data_type is None else data_type
        refresh = watch_interval_s if watch else None
        super().__init__(inferred_type, refresh, source_id)
        self._path = resolved
        self._format = fmt
        self._writable = writable
        self._root_dir = Path(root_dir).resolve() if root_dir is not None else None

    @property
    def path(self) -> Path:
        return self._path

    def fetch(self) -> Any:
        if not self._path.exists():
            return _empty_for(self.data_type)
        return _read_file(self._path, self._format, self.data_type)

    def write(self, value: Any) -> None:
        if not self._writable:
            raise RuntimeError(f"FileDataSource '{self.source_id}' is read-only")
        if self._format in {"parquet"}:
            _write_parquet(self._path, value)
            return

        serialized = _serialize(self._format, self.data_type, value)
        # Atomic write: temp file in the same dir, then os.replace.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, prefix=".tmp-", suffix=self._path.suffix)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(serialized)
            os.replace(tmp_path, self._path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


def _default_data_type(fmt: str) -> DataType:
    if fmt in {"csv", "tsv", "parquet"}:
        return DataType.DATAFRAME
    if fmt in {"json", "jsonl", "yaml"}:
        return DataType.DICT
    return DataType.STRING


def _empty_for(data_type: DataType) -> Any:
    if data_type in {DataType.DATAFRAME, DataType.TREE_ROWS, DataType.STRING_LIST, DataType.TABLE_2D}:
        return []
    if data_type == DataType.DICT:
        return {}
    if data_type == DataType.BOOL:
        return False
    if data_type == DataType.NUMBER:
        return 0
    return ""


def _read_file(path: Path, fmt: str, data_type: DataType) -> Any:
    if fmt in {"txt", "md"}:
        return path.read_text(encoding="utf-8")
    if fmt == "json":
        return json.loads(path.read_text(encoding="utf-8"))
    if fmt == "jsonl":
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return lines
    if fmt == "yaml":
        import yaml  # type: ignore[import-untyped]

        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if fmt in {"csv", "tsv"}:
        import pandas as pd

        sep = "\t" if fmt == "tsv" else ","
        df = pd.read_csv(path, sep=sep)
        if data_type == DataType.TABLE_2D:
            return [list(df.columns)] + df.astype(object).where(df.notna(), None).values.tolist()
        return df.astype(object).where(df.notna(), None).to_dict(orient="records")
    if fmt == "parquet":
        import pandas as pd

        df = pd.read_parquet(path)
        return df.astype(object).where(df.notna(), None).to_dict(orient="records")
    raise ValueError(f"Unsupported format '{fmt}'")


def _serialize(fmt: str, data_type: DataType, value: Any) -> str:
    if fmt in {"txt", "md"}:
        return value if isinstance(value, str) else str(value)
    if fmt == "json":
        return json.dumps(value, indent=2, default=str)
    if fmt == "jsonl":
        if not isinstance(value, list):
            raise TypeError("jsonl write expects a list")
        return "\n".join(json.dumps(row, default=str) for row in value) + "\n"
    if fmt == "yaml":
        import yaml  # type: ignore[import-untyped]

        return yaml.safe_dump(value, sort_keys=False)
    if fmt in {"csv", "tsv"}:
        import pandas as pd

        sep = "\t" if fmt == "tsv" else ","
        if data_type == DataType.TABLE_2D:
            if not value:
                return ""
            df = pd.DataFrame(value[1:], columns=value[0])
        else:
            df = pd.DataFrame(value)
        return df.to_csv(index=False, sep=sep)
    raise ValueError(f"Unsupported format '{fmt}' for serialize")


def _write_parquet(path: Path, value: Any) -> None:
    import pandas as pd

    df = pd.DataFrame(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

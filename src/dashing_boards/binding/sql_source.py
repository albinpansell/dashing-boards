from __future__ import annotations

from typing import Any

from .source import PollingDataSource, WritableDataSource
from .types import DataType


class SqlDataSource(PollingDataSource, WritableDataSource):
    """Read (and optionally write) a relational database via SQLAlchemy.

    The `engine` can target SQLite, DuckDB (via `duckdb-engine`), Postgres, etc.
    `query` is executed on every read; results are returned as DATAFRAME
    records (list[dict]) or TABLE_2D (list[list[Any]]) depending on `data_type`.

    Writes: if `write_target=(table_name, pk_column)` is set, `write(records)`
    performs a simple upsert (delete-by-pk + insert).
    """

    def __init__(
        self,
        engine: Any,
        query: str,
        params: dict[str, Any] | None = None,
        data_type: DataType = DataType.DATAFRAME,
        refresh_interval_s: float | None = None,
        write_target: tuple[str, str] | None = None,
        source_id: str | None = None,
    ) -> None:
        if data_type not in {DataType.DATAFRAME, DataType.TABLE_2D, DataType.DICT}:
            raise ValueError(f"SqlDataSource supports DATAFRAME, TABLE_2D, or DICT; got {data_type.value}")
        super().__init__(data_type, refresh_interval_s, source_id)
        self._engine = engine
        self._query = query
        self._params = params or {}
        self._write_target = write_target

    def fetch(self) -> Any:
        from sqlalchemy import text

        with self._engine.connect() as conn:
            result = conn.execute(text(self._query), self._params)
            rows = result.mappings().all()

        if self.data_type == DataType.DATAFRAME:
            return [dict(r) for r in rows]
        if self.data_type == DataType.TABLE_2D:
            if not rows:
                return []
            keys = list(rows[0].keys())
            return [keys] + [[r[k] for k in keys] for r in rows]
        # DICT: return first row, or empty dict
        return dict(rows[0]) if rows else {}

    def write(self, value: Any) -> None:
        if self._write_target is None:
            raise RuntimeError(f"SqlDataSource '{self.source_id}' has no write_target; cannot write")
        if self.data_type != DataType.DATAFRAME:
            raise RuntimeError("Writes are only supported for DATAFRAME sources")

        table_name, pk_col = self._write_target
        from sqlalchemy import MetaData, Table, delete

        if not isinstance(value, list):
            raise TypeError("DATAFRAME write expects list[dict]")

        metadata = MetaData()
        with self._engine.begin() as conn:
            table = Table(table_name, metadata, autoload_with=conn)
            pks = [row[pk_col] for row in value if pk_col in row]
            if pks:
                conn.execute(delete(table).where(table.c[pk_col].in_(pks)))
            if value:
                conn.execute(table.insert(), value)

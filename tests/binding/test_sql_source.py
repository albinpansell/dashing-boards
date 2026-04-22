from __future__ import annotations

import pytest

from dashing_boards import DataType, SqlDataSource

sqlalchemy = pytest.importorskip("sqlalchemy")


def _engine_with_sales():
    from sqlalchemy import create_engine, text

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, revenue REAL)"))
        conn.execute(text("INSERT INTO sales (id, product, revenue) VALUES (1, 'A', 10.0), (2, 'B', 20.0)"))
    return engine


def test_sql_source_dataframe() -> None:
    engine = _engine_with_sales()
    src = SqlDataSource(engine, "SELECT product, revenue FROM sales ORDER BY product", source_id="sq1")
    assert src.fetch() == [{"product": "A", "revenue": 10.0}, {"product": "B", "revenue": 20.0}]


def test_sql_source_table_2d() -> None:
    engine = _engine_with_sales()
    src = SqlDataSource(
        engine, "SELECT product FROM sales ORDER BY product", data_type=DataType.TABLE_2D, source_id="sq2"
    )
    assert src.fetch() == [["product"], ["A"], ["B"]]


def test_sql_source_write_upserts() -> None:
    engine = _engine_with_sales()
    src = SqlDataSource(
        engine,
        "SELECT id, product, revenue FROM sales ORDER BY id",
        write_target=("sales", "id"),
        source_id="sq3",
    )
    src.write([{"id": 1, "product": "A", "revenue": 99.0}, {"id": 3, "product": "C", "revenue": 5.0}])
    assert src.fetch() == [
        {"id": 1, "product": "A", "revenue": 99.0},
        {"id": 2, "product": "B", "revenue": 20.0},
        {"id": 3, "product": "C", "revenue": 5.0},
    ]


def test_sql_source_rejects_unsupported_data_type() -> None:
    with pytest.raises(ValueError, match="supports"):
        SqlDataSource(object(), "SELECT 1", data_type=DataType.STRING)

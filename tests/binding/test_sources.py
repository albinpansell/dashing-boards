from __future__ import annotations

import json
from pathlib import Path

import pytest

from dashing_boards import DataType, FileDataSource, StaticData
from dashing_boards.binding.source import CallableDataSource


def test_static_data_returns_initial_value() -> None:
    src = StaticData("hello", DataType.STRING, source_id="t1")
    assert src.initial() == "hello"
    assert src.data_type == DataType.STRING
    assert src.store_id == {"component": "DataSource", "source_id": "t1"}


def test_callable_data_source_invokes_fn_each_fetch() -> None:
    counter = {"n": 0}

    def fn() -> int:
        counter["n"] += 1
        return counter["n"]

    src = CallableDataSource(fn, DataType.NUMBER, source_id="t2")
    assert src.fetch() == 1
    assert src.fetch() == 2


def test_file_source_reads_json(tmp_path: Path) -> None:
    p = tmp_path / "a.json"
    p.write_text(json.dumps({"k": 1}))
    src = FileDataSource(p, source_id="t3")
    assert src.fetch() == {"k": 1}


def test_file_source_reads_csv_records(tmp_path: Path) -> None:
    pytest.importorskip("pandas")
    p = tmp_path / "a.csv"
    p.write_text("a,b\n1,x\n2,y\n")
    src = FileDataSource(p, source_id="t4")
    assert src.fetch() == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_file_source_atomic_write_json(tmp_path: Path) -> None:
    p = tmp_path / "out.json"
    src = FileDataSource(p, writable=True, data_type=DataType.DICT, source_id="t5")
    src.write({"hello": "world"})
    assert json.loads(p.read_text()) == {"hello": "world"}


def test_file_source_refuses_write_when_read_only(tmp_path: Path) -> None:
    p = tmp_path / "ro.txt"
    p.write_text("x")
    src = FileDataSource(p, writable=False, source_id="t6")
    with pytest.raises(RuntimeError, match="read-only"):
        src.write("y")


def test_file_source_rejects_path_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("x")
    with pytest.raises(ValueError, match="outside"):
        FileDataSource(outside, root_dir=root)

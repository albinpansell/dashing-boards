from __future__ import annotations

import dash_bootstrap_components as dbc
import pytest
from dash import html

from dashing_boards.components.tree_table import TreeTableAIO, TreeTableModel


def rows() -> list[dict[str, object]]:
    return [
        {"id": "root", "parent_id": None, "name": "Root", "cost": 0},
        {"id": "child", "parent_id": "root", "name": "Child", "cost": 10},
    ]


def test_component_has_expected_structure() -> None:
    component = TreeTableAIO(rows=rows(), aio_id="sample")
    assert isinstance(component, html.Div)
    assert component.id == TreeTableAIO.ids.aio_root("sample")
    assert len(component.children) == 3


def test_build_table_returns_table() -> None:
    component = TreeTableAIO(rows=rows(), aio_id="x")
    state_data = component.children[0].data
    config_data = component.children[1].data
    table_container = TreeTableAIO.build_table("x", state_data, config_data)
    assert isinstance(table_container, html.Div)
    assert isinstance(table_container.children[1], dbc.Table)


def test_default_columns_hide_id_fields() -> None:
    model = TreeTableModel(rows=rows())
    columns = TreeTableAIO._display_columns(model, None)
    assert columns == ["name", "cost"]


def test_coerce_value_uses_existing_type() -> None:
    assert TreeTableAIO._coerce_value(3, "7") == 7
    assert TreeTableAIO._coerce_value(3.5, "7.5") == 7.5
    assert TreeTableAIO._coerce_value(True, "false") is False
    assert TreeTableAIO._coerce_value(False, True) is True
    assert TreeTableAIO._coerce_value("x", "7") == "7"


def test_coerce_value_rejects_invalid_boolean_text() -> None:
    with pytest.raises(ValueError, match="Invalid boolean value"):
        TreeTableAIO._coerce_value(True, "unexpected")

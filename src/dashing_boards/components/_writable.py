from __future__ import annotations

from typing import Any

from dash import callback_context
from dash.exceptions import PreventUpdate

from ..binding.source import PollingDataSource, WritableDataSource


def triggered_value() -> Any:
    """Return the current value of the input that triggered the callback.

    Raises PreventUpdate if there is no trigger. Used in writeback
    callbacks that accept a list of ALL-wildcarded inputs but only
    want the one that actually changed.
    """
    if not callback_context.triggered:
        raise PreventUpdate
    return callback_context.triggered[0]["value"]


def mirror_to_backing(value: Any) -> None:
    """If the triggering DataSource is WritableDataSource, persist to its backing system.

    Callable from inside a Dash callback only (uses callback_context).
    Errors are swallowed with a printed warning to avoid crashing the callback.
    """
    trigger = callback_context.triggered_id
    if not isinstance(trigger, dict):
        return
    source_id = trigger.get("source_id")
    if not source_id:
        return
    src = PollingDataSource._registry.get(source_id)
    if src is None or not isinstance(src, WritableDataSource):
        return
    try:
        src.write(value)
    except Exception as exc:  # noqa: BLE001
        print(f"[dashing_boards] write-back to '{source_id}' failed: {exc}")

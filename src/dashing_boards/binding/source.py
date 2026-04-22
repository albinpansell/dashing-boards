from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable

from dash import MATCH, Input, Output, State, callback, callback_context, dcc, html
from dash.exceptions import PreventUpdate

from .types import DataType


def _store_id(source_id: str) -> dict[str, str]:
    return {"component": "DataSource", "source_id": source_id}


def _interval_id(source_id: str) -> dict[str, str]:
    return {"component": "DataSource", "sub": "interval", "source_id": source_id}


def _refresh_btn_id(source_id: str) -> dict[str, str]:
    return {"component": "DataSource", "sub": "refresh_btn", "source_id": source_id}


class DataSource(ABC):
    """Holds a payload of a declared DataType.

    Backed by a dcc.Store. The store's id is pattern-matchable so
    components and callbacks can bind to it via MATCH/ALL without
    needing a Python-level subscribe primitive.
    """

    def __init__(self, data_type: DataType, source_id: str | None = None) -> None:
        self.data_type = data_type
        self.source_id = source_id or f"ds-{uuid.uuid4().hex[:8]}"

    @property
    def store_id(self) -> dict[str, str]:
        return _store_id(self.source_id)

    @abstractmethod
    def initial(self) -> Any:
        """Initial payload written into the backing Store."""

    def store(self) -> html.Div:
        """Render the backing Store (plus any source-specific machinery).

        Place this once in the app layout. Default: just the Store.
        Subclasses that need intervals or hidden buttons override.
        """
        return html.Div(dcc.Store(id=self.store_id, data=self.initial()))


class StaticData(DataSource):
    """In-memory payload, fixed at construction time."""

    def __init__(self, value: Any, data_type: DataType, source_id: str | None = None) -> None:
        super().__init__(data_type, source_id)
        self._value = value

    def initial(self) -> Any:
        return self._value


class PollingDataSource(DataSource):
    """Base for sources that re-read a backing system on an interval.

    Subclasses implement `fetch()` returning the latest payload.
    A hidden dcc.Interval drives a pattern-matched callback that writes
    the fetch result into the Store. If `refresh_interval_s` is None,
    the source behaves as a one-shot (initial read only).
    """

    _registry: dict[str, "PollingDataSource"] = {}

    def __init__(
        self,
        data_type: DataType,
        refresh_interval_s: float | None = None,
        source_id: str | None = None,
    ) -> None:
        super().__init__(data_type, source_id)
        self.refresh_interval_s = refresh_interval_s
        PollingDataSource._registry[self.source_id] = self

    @abstractmethod
    def fetch(self) -> Any:
        """Return the current payload from the backing system."""

    def initial(self) -> Any:
        return self.fetch()

    def store(self) -> html.Div:
        children: list[Any] = [dcc.Store(id=self.store_id, data=self.initial())]
        if self.refresh_interval_s is not None:
            children.append(
                dcc.Interval(
                    id=_interval_id(self.source_id),
                    interval=int(self.refresh_interval_s * 1000),
                    n_intervals=0,
                )
            )
        return html.Div(children)


@callback(
    Output({"component": "DataSource", "source_id": MATCH}, "data", allow_duplicate=True),
    Input({"component": "DataSource", "sub": "interval", "source_id": MATCH}, "n_intervals"),
    prevent_initial_call=True,
)
def _poll_refresh(_n: int | None) -> Any:
    trigger = callback_context.triggered_id
    if not trigger or not isinstance(trigger, dict):
        raise PreventUpdate
    source_id = trigger.get("source_id")
    if not source_id:
        raise PreventUpdate
    src = PollingDataSource._registry.get(source_id)
    if src is None:
        raise PreventUpdate
    return src.fetch()


class CallableDataSource(PollingDataSource):
    """Source whose payload comes from an arbitrary callable."""

    def __init__(
        self,
        fn: Callable[[], Any],
        data_type: DataType,
        refresh_interval_s: float | None = None,
        source_id: str | None = None,
    ) -> None:
        super().__init__(data_type, refresh_interval_s, source_id)
        self._fn = fn

    def fetch(self) -> Any:
        return self._fn()


class WritableDataSource(DataSource):
    """Mixin marker for sources that accept writes back to the backing system.

    Components call `source.write(value)` from a server-side callback to
    persist user edits. The Store update still happens via the callback
    output; this just mirrors to disk/DB.
    """

    def write(self, value: Any) -> None:  # pragma: no cover - abstract behaviour
        raise NotImplementedError

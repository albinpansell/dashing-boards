from __future__ import annotations

import uuid
from abc import abstractmethod
from typing import Any, ClassVar

from dash import html

from .source import DataSource
from .types import DataType


class DataBoundComponent(html.Div):
    """Base for components that render a DataSource.

    Subclass contract:
    - Set ACCEPTED_TYPES to the DataTypes the component can display.
    - Implement _build() returning the child nodes. Use
      self.source.source_id in any pattern-matched ids so class-level
      callbacks can resolve the right store via MATCH.
    """

    ACCEPTED_TYPES: ClassVar[frozenset[DataType]] = frozenset()

    def __init__(
        self,
        source: DataSource,
        aio_id: str | None = None,
        container_props: dict[str, Any] | None = None,
    ) -> None:
        if not self.ACCEPTED_TYPES:
            raise TypeError(f"{type(self).__name__}.ACCEPTED_TYPES must be non-empty")
        if source.data_type not in self.ACCEPTED_TYPES:
            accepted = sorted(t.value for t in self.ACCEPTED_TYPES)
            raise TypeError(
                f"{type(self).__name__} accepts {accepted}; got '{source.data_type.value}' "
                f"from source '{source.source_id}'"
            )
        self.source = source
        self.aio_id = aio_id or f"aio-{uuid.uuid4().hex[:8]}"
        props = dict(container_props or {})
        super().__init__(children=self._build(), **props)

    @abstractmethod
    def _build(self) -> list[Any]:
        """Return the component's child nodes."""

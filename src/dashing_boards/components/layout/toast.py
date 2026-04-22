from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc


class Toast(dbc.Toast):
    def __init__(
        self,
        message: str,
        header: str = "",
        is_open: bool = True,
        duration_ms: int | None = 4000,
        toast_id: str | None = None,
        icon: str = "primary",
    ) -> None:
        kwargs: dict[str, Any] = {
            "header": header,
            "is_open": is_open,
            "dismissable": True,
            "icon": icon,
        }
        if duration_ms is not None:
            kwargs["duration"] = duration_ms
        if toast_id is not None:
            kwargs["id"] = toast_id
        super().__init__(message, **kwargs)

from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import Dash


SORTABLE_JS_URL = "https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"


def make_app(*args: Any, **kwargs: Any) -> Dash:
    """Create a Dash app with the standard Bootstrap theme applied.

    Ensures consistent fonts/styling across all dashing_boards components.
    Any caller-supplied `external_stylesheets` / `external_scripts` are appended.
    """
    extra_css = kwargs.pop("external_stylesheets", []) or []
    kwargs["external_stylesheets"] = [dbc.themes.BOOTSTRAP, *extra_css]
    extra_js = kwargs.pop("external_scripts", []) or []
    kwargs["external_scripts"] = [SORTABLE_JS_URL, *extra_js]
    return Dash(*args, **kwargs)

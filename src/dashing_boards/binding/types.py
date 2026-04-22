from __future__ import annotations

from enum import Enum


class DataType(str, Enum):
    """Shape of the payload a DataSource carries.

    Components declare which of these they accept. This is about the
    *data shape* (string, 2D array, tree rows), not where the data comes
    from (static, SQL, API).
    """

    STRING = "string"
    NUMBER = "number"
    BOOL = "bool"
    STRING_LIST = "string_list"
    TABLE_2D = "table_2d"  # list[list[Any]]
    TREE_ROWS = "tree_rows"  # list[dict] with id/parent_id
    DICT = "dict"
    DATAFRAME = "dataframe"  # list[dict] - records orientation
    GRAPH = "graph"  # {"nodes": [...], "edges": [...]}

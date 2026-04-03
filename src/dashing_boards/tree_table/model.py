from __future__ import annotations

from collections import deque
from typing import Any

from .aggregation import AggregationType, apply_aggregation, parse_aggregation


class TreeTableModel:
    REQUIRED_COLUMNS = ("id", "parent_id", "name")

    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        aggregation_map: dict[str, AggregationType | str] | None = None,
    ) -> None:
        self._rows: list[dict[str, Any]] = [dict(row) for row in (rows or [])]
        self._aggregation_map: dict[str, AggregationType] = {
            key: parse_aggregation(value) for key, value in (aggregation_map or {}).items()
        }
        for field in self._aggregation_map:
            self._validate_aggregation_field(field)
        self._validate_rows()
        self._apply_all_aggregations()

    @property
    def rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows]

    @property
    def columns(self) -> list[str]:
        ordered_columns: list[str] = list(self.REQUIRED_COLUMNS)
        for row in self._rows:
            for column in row:
                if column not in ordered_columns:
                    ordered_columns.append(column)
        return ordered_columns

    def set_aggregation(self, field: str, aggregation: AggregationType | str) -> None:
        self._validate_aggregation_field(field)
        self._aggregation_map[field] = parse_aggregation(aggregation)
        self._apply_all_aggregations()

    def get_aggregation(self, field: str) -> AggregationType:
        return self._aggregation_map.get(field, AggregationType.NONE)

    def get_item(self, item_id: str) -> dict[str, Any]:
        for row in self._rows:
            if str(row["id"]) == item_id:
                return dict(row)
        raise ValueError(f"Item not found: {item_id}")

    def get_children_ids(self, parent_id: str | None) -> list[str]:
        return [str(row["id"]) for row in self._rows if self._parent_matches(row.get("parent_id"), parent_id)]

    def has_children(self, item_id: str) -> bool:
        return len(self.get_children_ids(item_id)) > 0

    def get_depth(self, item_id: str) -> int:
        parent_lookup = {str(row["id"]): row.get("parent_id") for row in self._rows}
        depth = 0
        current = item_id
        while current in parent_lookup:
            parent_id = parent_lookup[current]
            if parent_id is None:
                break
            current = str(parent_id)
            depth += 1
        return depth

    def visible_items(self, collapsed_ids: set[str] | None = None) -> list[dict[str, Any]]:
        collapsed = collapsed_ids or set()
        result: list[dict[str, Any]] = []
        queue: deque[tuple[str, int]] = deque((root_id, 0) for root_id in self.get_children_ids(None))

        while queue:
            item_id, depth = queue.popleft()
            item = self.get_item(item_id)
            item["_depth"] = depth
            item["_has_children"] = self.has_children(item_id)
            item["_collapsed"] = item_id in collapsed
            result.append(item)

            if item_id in collapsed:
                continue

            children = self.get_children_ids(item_id)
            for child_id in reversed(children):
                queue.appendleft((child_id, depth + 1))

        return result

    def update_field(self, item_id: str, field: str, value: Any) -> None:
        if field == "id":
            raise ValueError("Cannot update id field")

        row = self._get_row_ref(item_id)
        row[field] = value

        aggregation = self.get_aggregation(field)
        if aggregation == AggregationType.EQUAL:
            self._propagate_equal_to_children(item_id, field)
        elif aggregation != AggregationType.NONE:
            self._propagate_up(field, aggregation)

    def _validate_rows(self) -> None:
        for row in self._rows:
            missing = [column for column in self.REQUIRED_COLUMNS if column not in row]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

        ids = [str(row["id"]) for row in self._rows]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate ids found")

        id_set = set(ids)
        for row in self._rows:
            parent_id = row.get("parent_id")
            if parent_id is not None and str(parent_id) not in id_set:
                raise ValueError(f"Parent id not found: {parent_id}")

        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        parent_lookup = {str(row["id"]): row.get("parent_id") for row in self._rows}
        for start_id in parent_lookup:
            seen: set[str] = set()
            current: str | None = start_id
            while current is not None:
                if current in seen:
                    raise ValueError("Cycle detected in tree")
                seen.add(current)
                parent = parent_lookup.get(current)
                current = None if parent is None else str(parent)

    def _apply_all_aggregations(self) -> None:
        for field, aggregation in self._aggregation_map.items():
            if aggregation == AggregationType.NONE:
                continue
            if aggregation == AggregationType.EQUAL:
                for root_id in self.get_children_ids(None):
                    self._propagate_equal_to_children(root_id, field)
            else:
                self._propagate_up(field, aggregation)

    def _propagate_equal_to_children(self, parent_id: str, field: str) -> None:
        parent_value = self._get_row_ref(parent_id).get(field)
        for child_id in self.get_children_ids(parent_id):
            child = self._get_row_ref(child_id)
            child[field] = parent_value
            self._propagate_equal_to_children(child_id, field)

    def _propagate_up(self, field: str, aggregation: AggregationType) -> None:
        parents = [item_id for item_id in (str(row["id"]) for row in self._rows) if self.has_children(item_id)]
        parents.sort(key=self.get_depth, reverse=True)
        for parent_id in parents:
            child_values = [self._get_row_ref(child_id).get(field) for child_id in self.get_children_ids(parent_id)]
            aggregated = apply_aggregation(aggregation, child_values)
            self._get_row_ref(parent_id)[field] = aggregated

    def _get_row_ref(self, item_id: str) -> dict[str, Any]:
        for row in self._rows:
            if str(row["id"]) == item_id:
                return row
        raise ValueError(f"Item not found: {item_id}")

    @staticmethod
    def _parent_matches(actual_parent: object, expected_parent: str | None) -> bool:
        if expected_parent is None:
            return actual_parent is None
        if actual_parent is None:
            return False
        return str(actual_parent) == expected_parent

    def _validate_aggregation_field(self, field: str) -> None:
        if field in self.REQUIRED_COLUMNS:
            raise ValueError(f"Cannot set aggregation on required field: {field}")

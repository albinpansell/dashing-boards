from __future__ import annotations

from enum import Enum
from typing import Iterable


class AggregationType(Enum):
    NONE = "none"
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    EQUAL = "equal"


def parse_aggregation(value: AggregationType | str) -> AggregationType:
    if isinstance(value, AggregationType):
        return value
    return AggregationType(str(value).lower())


def apply_aggregation(aggregation: AggregationType, values: Iterable[object]) -> object:
    if aggregation == AggregationType.NONE:
        return None

    if aggregation == AggregationType.EQUAL:
        valid = [value for value in values if value is not None and not _is_nan(value)]
        return valid[0] if valid else None

    numeric_values = [float(value) for value in values if _is_number(value)]
    if not numeric_values:
        return None

    if aggregation == AggregationType.SUM:
        return sum(numeric_values)
    if aggregation == AggregationType.AVERAGE:
        return sum(numeric_values) / len(numeric_values)
    if aggregation == AggregationType.MIN:
        return min(numeric_values)
    if aggregation == AggregationType.MAX:
        return max(numeric_values)

    return None


def _is_nan(value: object) -> bool:
    try:
        return value != value
    except (TypeError, ValueError):
        return False


def _is_number(value: object) -> bool:
    if value is None or _is_nan(value):
        return False
    if isinstance(value, bool):
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True

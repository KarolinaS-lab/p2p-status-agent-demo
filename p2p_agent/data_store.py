"""Read-only synthetic data store.

The store loads the JSON file once into immutable structures (tuples of
MappingProxyType). It exposes query functions only; there is no insert,
update, delete, approve or pay function anywhere in this package.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .config import DATA_FILE


def _freeze(row: dict) -> Mapping:
    return MappingProxyType(dict(row))


@lru_cache(maxsize=4)
def load_records(path: str | None = None) -> tuple[Mapping, ...]:
    p = Path(path) if path else DATA_FILE
    with p.open("r", encoding="utf-8") as fh:  # opened read-only
        raw = json.load(fh)
    return tuple(_freeze(r) for r in raw["records"])


def rows_for_id(record_id: str) -> tuple[Mapping, ...]:
    return tuple(r for r in load_records() if r["record_id"] == record_id)


def rows_for_number(number: str) -> tuple[Mapping, ...]:
    return tuple(r for r in load_records() if r["record_id"].split("-", 1)[1] == number)

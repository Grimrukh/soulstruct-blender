from __future__ import annotations

__all__ = [
    "iter_tracked_objects",
    "count_states",
    "objects_by_state",
    "export_csv",
]

import csv
import os
import typing as tp

import bpy

from .config import DEFAULT_EXPORT

def iter_tracked_objects() -> tp.Iterable[bpy.types.Object]:
    for obj in bpy.data.objects:
        if obj.map_progress.state != "NONE":
            yield obj

def count_states():
    t = ts = w = d = 0
    total = 0
    for obj in iter_tracked_objects():
        s = obj.map_progress.state
        if   s == "TODO":          t  += 1
        elif s == "TODO_SCENERY":  ts += 1
        elif s == "WIP":           w  += 1
        elif s == "DONE":          d  += 1
        total += 1
    return t, ts, w, d, total

def objects_by_state(state: str, name_filter: str = "", visible_only: bool = False) -> tp.List[bpy.types.Object]:
    nf = (name_filter or "").strip().lower()
    items = []
    for obj in iter_tracked_objects():
        if visible_only and not obj.visible_get():
            continue
        if obj.map_progress.state == state:
            if nf and nf not in obj.name.lower():
                continue
            items.append(obj)
    items.sort(key=lambda o: o.name)
    return items

def export_csv(filepath: str = str(DEFAULT_EXPORT)) -> str:
    rows = [["Name", "State", "Note", "Last Edit", "CollectionPath"]]
    for obj in iter_tracked_objects():
        coll_path = [coll.name for coll in obj.users_collection]
        rows.append([
            obj.name,
            obj.map_progress.state,
            obj.map_progress.note,
            obj.map_progress.last_edit,
            " | ".join(coll_path),
        ])
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return filepath

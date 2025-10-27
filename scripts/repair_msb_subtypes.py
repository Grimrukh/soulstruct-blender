"""Script that checks MSB entry collection names to re-assign lost MSB subtypes."""

import re

import bpy

from soulstruct.games import DARK_SOULS_DSR

from soulstruct.blender.types import SoulstructType
from soulstruct.blender.msb.operator_config import BLENDER_MSB_EVENT_CLASSES, BLENDER_MSB_REGION_CLASSES
from soulstruct.blender.msb.properties.events import BlenderMSBEventSubtype
from soulstruct.blender.msb.properties.parts import BlenderMSBPartSubtype
from soulstruct.blender.msb.properties.regions import BlenderMSBRegionSubtype
from soulstruct.blender.msb.types.darksouls1r import BlenderMSBRegion

_RE_MSB_COLL_NAME = re.compile(r"^(m\d\d_\d\d_\d\d_\d\d) MSB$")
_RE_MSB_PART_COLL_NAME = re.compile(r"^m\d\d_\d\d_\d\d_\d\d (.*) Parts$")

_RE_EVENT_NAME = re.compile(r"^(.*) <(.*)>(\.\d\d\d)?")  # optional dupe suffix

_BLENDER_EVENT_CLASSES = BLENDER_MSB_EVENT_CLASSES[DARK_SOULS_DSR]
_BLENDER_REGION_CLASSES = BLENDER_MSB_REGION_CLASSES[DARK_SOULS_DSR]


def _detect_part_subtype(coll_name: str) -> BlenderMSBPartSubtype | None:
    match = _RE_MSB_PART_COLL_NAME.match(coll_name)
    if match:
        subtype = match.group(1).replace(" ", "")
        return BlenderMSBPartSubtype[subtype]  # look up enum by name, not value
    return None


def split_region_event_collection(msb_collection: bpy.types.Collection, dry_run=False
):
    """Split Regions/Events collection into Regions and Events subcollections based on MSB collection name.

    NOTE: Dry run will still create the destination subcollections if they do not exist, but will not move any objects.
    """

    # Parse MSB collection name.
    if not (msb_match := _RE_MSB_COLL_NAME.match(msb_collection.name)):
        raise ValueError(f"MSB collection name '{msb_collection.name}' does not match expected pattern.")
    msb_stem = msb_match.group(1)

    # Expect child collection for Regions/Events.
    for coll in msb_collection.children:
        if coll.name != f"{msb_stem} Regions/Events":
            continue
        region_events_coll = coll
        break
    else:
        raise ValueError(f"MSB collection '{msb_collection.name}' has no Regions/Events subcollection.")

    region_coll = BlenderMSBRegion.get_msb_subcollection(msb_collection, msb_stem)

    # Move objects to appropriate collections, putting Events under their subtype collection.
    # NOTE: Child events should retain their relationship to Regions after separating.

    for obj in region_events_coll.objects:
        if obj.soulstruct_type == SoulstructType.MSB_REGION:
            # Move to Regions collection.
            if dry_run:
                print(f"Moving region '{obj.name}' to collection '{region_coll.name}'.")
            else:
                region_events_coll.objects.unlink(obj)
                region_coll.objects.link(obj)
        elif obj.soulstruct_type == SoulstructType.MSB_EVENT:
            # Move to Events collection.
            event_subtype = obj.MSB_EVENT.entry_subtype
            event_class = _BLENDER_EVENT_CLASSES[event_subtype]
            events_coll = event_class.get_msb_subcollection(msb_collection, msb_stem)
            if dry_run:
                print(f"Moving event '{obj.name}' to collection '{events_coll.name}'.")
            else:
                region_events_coll.objects.unlink(obj)
                events_coll.objects.link(obj)
        else:
            print(f"WARNING: Object '{obj.name}' in Regions/Events collection is not an MSB Region or Event. Ignoring.")


def _repair_region_subtype(obj: bpy.types.Object, dry_run=False) -> None:
    """All regions use 'All' subtype."""
    if obj.soulstruct_type != SoulstructType.MSB_REGION:
        print(f"Ignoring non-MSB Region object '{obj.name}'.")
        return
    if dry_run:
        print(f"'{obj.name}'.MSB_REGION.entry_subtype = 'All'")
    else:
        obj.MSB_REGION.entry_subtype = BlenderMSBRegionSubtype.All


def _repair_event_subtype(obj: bpy.types.Object, dry_run=False) -> None:
    if obj.soulstruct_type != SoulstructType.MSB_EVENT:
        print(f"Ignoring non-MSB Event object '{obj.name}'.")
        return

    # Examine suffix for subtype.
    event_match = _RE_EVENT_NAME.match(obj.name)
    if not event_match:
        print(f"ERROR: Could not detect subtype of MSB Event entry '{obj.name}' from its name.")
        return
    event_name = event_match.group(1)
    suffix = event_match.group(2)
    # Look up enum by name, not value.
    try:
        event_enum = BlenderMSBEventSubtype[suffix]
    except KeyError:
        print(f"ERROR: Unrecognized MSB Event subtype suffix in obj: '{obj.name}'")
        return
    new_event_name = f"{event_name} <E>"
    if dry_run:
        print(f"'{obj.name}'.MSB_EVENT.entry_subtype = {event_enum}")
        print(f"    Renaming MSB Event '{obj.name}' -> '{new_event_name}'")
    else:
        obj.MSB_EVENT.entry_subtype = event_enum
        obj.name = new_event_name


def _repair_part_subtype(obj: bpy.types.Object, subtype: BlenderMSBPartSubtype, dry_run=False) -> None:
    if obj.soulstruct_type != SoulstructType.MSB_PART:
        print(f"Ignoring non-MSB Part object '{obj.name}'.")
        return
    if dry_run:
        print(f"'{obj.name}'.MSB_PART.entry_subtype = {subtype}")
    else:
        obj.MSB_PART.entry_subtype = subtype


def repair_msb_subtypes(msb_collection: bpy.types.Collection, dry_run=False) -> None:

    # Parse MSB collection name.
    if not (msb_match := _RE_MSB_COLL_NAME.match(msb_collection.name)):
        raise ValueError(f"MSB collection name '{msb_collection.name}' does not match expected pattern.")
    msb_stem = msb_match.group(1)

    # Expect child collections for Regions/Events and Parts.
    for coll in msb_collection.children:

        if coll.name == f"{msb_stem} Regions/Events":
            # Legacy joint collection for both Regions and Events.
            region_events_coll = coll
            for obj in region_events_coll.objects:
                if obj.soulstruct_type == SoulstructType.MSB_REGION:
                    _repair_region_subtype(obj, dry_run=dry_run)
                elif obj.soulstruct_type == SoulstructType.MSB_EVENT:
                    _repair_event_subtype(obj, dry_run=dry_run)
                else:
                    print(f"Ignoring non-MSB Region/Event object '{obj.name}'.")
            continue

        if coll.name == f"{msb_stem} Regions":
            for obj in coll.objects:
                _repair_region_subtype(obj, dry_run=dry_run)
            continue

        if coll.name == f"{msb_stem} Events":
            for obj in coll.objects:
                _repair_event_subtype(obj, dry_run=dry_run)
            continue

        if coll.name == f"{msb_stem} Parts":
            # Iterate over subtype child collections.
            for part_subtype_coll in coll.children:
                subtype = _detect_part_subtype(part_subtype_coll.name)
                if subtype is None:
                    print(f"Ignoring unrecognized MSB Part collection name {part_subtype_coll.name}")
                    continue
                for obj in part_subtype_coll.objects:
                    _repair_part_subtype(obj, subtype, dry_run=dry_run)
            continue

        print(f"Ignoring unrecognized MSB sub-collection {coll.name}.")


if __name__ == "__main__":
    # MSB collection must be active.

    repair_msb_subtypes(bpy.context.collection)
    # split_region_event_collection(bpy.context.collection)

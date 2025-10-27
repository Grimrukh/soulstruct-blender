"""Script to run in Blender to move a subset of MSB entries -- and their Map Piece, Collision, and Navmesh models as
appropriate -- from one MSB collection (and Model collection) to another.
"""
import typing as tp

import bpy
from bpy.types import Collection

from soulstruct.blender.types import SoulstructType
from soulstruct.blender.utilities.misc import MAP_STEM_RE
from soulstruct.blender.msb.properties import BlenderMSBPartSubtype


def main(source_map_stem: str, dest_map_stem: str, entry_filter_func: tp.Callable[[bpy.types.Object], bool]):
    """Move MSB entries from one map to another, along with their map geometry models.

    NOTE: This is designed for Dark Souls 1 (either version) only, mainly because of how the models are renamed and
    because of the exact Part collections used.

    To ensure you don't accidentally move EVERYTHING between maps, you must provide a filter function. You can move
    everything by having this function always return `True`, of course.

    All of the impacted source/dest collections are checked at the start of the function, and must exist before any
    moves are done.

    Map geometry models are automatically renamed using the "rename_flver", "rename_hkx_collision", and "rename_nvm"
    object operators added to Blender by `io_soulstruct`. These will rename their user parts as well, as appropriate.

    Args:
        source_map_stem: Map stem of the source map (e.g. "m10_01_00_00").
        dest_map_stem: Map stem of the destination map (e.g. "m16_00_00_00").
        entry_filter_func: Function that takes an MSB entry object and returns True if it should be moved.
            Example: `lambda obj: obj.MSB_PART.part_subtype == "MSB_MAP_PIECE" and obj.name.startswith("m12")`.
            This would move all Map Piece parts starting with "m12".
    """
    source_map_stem_match = MAP_STEM_RE.match(source_map_stem)
    if not source_map_stem_match:
        raise ValueError(f"Source map stem '{source_map_stem}' does not match expected format.")
    dest_map_stem_match = MAP_STEM_RE.match(dest_map_stem)
    if not dest_map_stem_match:
        raise ValueError(f"Destination map stem '{dest_map_stem}' does not match expected format.")

    # Get geometry model suffix change, e.g. 'B1A10' -> 'B0A16'.
    source_map_suffix = f"B{int(source_map_stem_match.group(2)):1}A{int(source_map_stem_match.group(1)):02d}"
    dest_map_suffix = f"B{int(dest_map_stem_match.group(2)):1}A{int(dest_map_stem_match.group(1)):02d}"

    source_msb_collection = bpy.data.collections[f"{source_map_stem} MSB"]

    dest_part_collections = {
        BlenderMSBPartSubtype.MapPiece: bpy.data.collections[f"{dest_map_stem} Map Piece Parts"],
        BlenderMSBPartSubtype.Collision: bpy.data.collections[f"{dest_map_stem} Collision Parts"],
        BlenderMSBPartSubtype.Navmesh: bpy.data.collections[f"{dest_map_stem} Navmesh Parts"],
        BlenderMSBPartSubtype.ConnectCollision: bpy.data.collections[f"{dest_map_stem} Connect Collision Parts"],
        BlenderMSBPartSubtype.Object: bpy.data.collections[f"{dest_map_stem} Object Parts"],
        BlenderMSBPartSubtype.Character: bpy.data.collections[f"{dest_map_stem} Character Parts"],
        BlenderMSBPartSubtype.PlayerStart: bpy.data.collections[f"{dest_map_stem} Player Start Parts"],
    }  # type: dict[BlenderMSBPartSubtype, Collection]

    # TODO: Need to update Event subcollections.
    dest_regions_events_collection = bpy.data.collections[f"{dest_map_stem} Regions/Events"]  # type: Collection

    dest_model_collections = {
        BlenderMSBPartSubtype.MapPiece: bpy.data.collections[f"{dest_map_stem} Map Piece Models"],
        BlenderMSBPartSubtype.Collision: bpy.data.collections[f"{dest_map_stem} Collision Models"],
        BlenderMSBPartSubtype.Navmesh: bpy.data.collections[f"{dest_map_stem} Navmesh Models"],
    }

    msb_objs_to_move = [obj for obj in source_msb_collection.all_objects if entry_filter_func(obj)]
    print(f"Moving {len(msb_objs_to_move)} MSB entries from {source_map_stem} to {dest_map_stem}.")

    # Collected over MSB parts.
    model_obj_names = {
        BlenderMSBPartSubtype.MapPiece: set(),
        BlenderMSBPartSubtype.Collision: set(),
        BlenderMSBPartSubtype.Navmesh: set(),
    }
    moved_names = set()  # don't move children twice (e.g. Event children of Regions)

    for obj in msb_objs_to_move:

        if obj.name in moved_names:
            continue

        armature_parent = None
        if obj.soulstruct_type == SoulstructType.MSB_PART:
            if obj.MSB_PART.entry_subtype == "NONE":
                print(f"Skipping Part with NONE subtype: {obj.name}")
                continue

            part_subtype = obj.MSB_PART.entry_subtype_enum

            if part_subtype in model_obj_names and obj.MSB_PART.model:
                model_obj_names[part_subtype].add(obj.MSB_PART.model.name)

            new_collection = dest_part_collections[part_subtype]
            print(f"Moving Part: {obj.name}")

            if obj.parent and obj.parent.type == "ARMATURE":
                armature_parent = obj.parent  # move Map Piece Part armature

        elif obj.soulstruct_type == SoulstructType.MSB_REGION:
            new_collection = dest_regions_events_collection
            print(f"Moving Region: {obj.name}")
        elif obj.soulstruct_type == SoulstructType.MSB_EVENT:
            new_collection = dest_regions_events_collection
            print(f"Moving Event: {obj.name}")
        else:
            # Ignore object. (Could be an Armature that will be moved with its child Part mesh.)
            continue

        moved_names.add(obj.name)

        new_collection.objects.link(obj)
        # Remove from any source map collections.
        for old_collection in obj.users_collection:
            if source_map_stem in old_collection.name:
                old_collection.objects.unlink(obj)

        # Move any children as well (not expecting any, but just in case).
        for child in obj.children_recursive:
            new_collection.objects.link(child)
            for old_collection in child.users_collection:
                if source_map_stem in old_collection.name:
                    old_collection.objects.unlink(child)
            moved_names.add(child.name)

        if armature_parent:
            new_collection.objects.link(armature_parent)
            # Remove from any m10_01_00_00 collections.
            for old_collection in armature_parent.users_collection:
                if source_map_stem in old_collection.name:
                    old_collection.objects.unlink(armature_parent)
            moved_names.add(armature_parent.name)

            # Move any other children of Armature too (e.g. Dummies).
            for child in armature_parent.children_recursive:
                new_collection.objects.link(child)
                for old_collection in child.users_collection:
                    if source_map_stem in old_collection.name:
                        old_collection.objects.unlink(child)
                moved_names.add(child.name)

    for part_subtype, model_names in model_obj_names.items():
        new_collection = dest_model_collections[part_subtype]
        for model_name in model_names:
            model_obj = bpy.data.objects[model_name]
            print(f"Moving model: {model_name}")

            new_collection.objects.link(model_obj)
            for old_collection in model_obj.users_collection:
                if source_map_stem in old_collection.name:
                    old_collection.objects.unlink(model_obj)

            # Move any children as well (e.g. NVM Event Entities).
            for child in model_obj.children_recursive:
                new_collection.objects.link(child)
                for old_collection in child.users_collection:
                    if source_map_stem in old_collection.name:
                        old_collection.objects.unlink(child)

            if part_subtype == BlenderMSBPartSubtype.MapPiece:

                if model_obj.parent and model_obj.parent.type == "ARMATURE":
                    model_armature_parent = model_obj.parent
                    new_collection.objects.link(model_armature_parent)
                    for old_collection in model_armature_parent.users_collection:
                        if source_map_stem in old_collection.name:
                            old_collection.objects.unlink(model_armature_parent)

                new_map_piece_name = model_obj.name.replace(source_map_suffix, dest_map_suffix)

                bpy.context.view_layer.objects.active = model_obj
                bpy.ops.object.rename_flver(
                    new_name=new_map_piece_name,
                    rename_parts=True,
                )
                print(f"  Renamed Map Piece model to: {model_obj.name}")

            # Fortunately, all Burg Collision/Navmesh models start with h1/n1.

            elif part_subtype == BlenderMSBPartSubtype.Collision:
                new_collision_name = model_obj.name.replace(source_map_suffix, dest_map_suffix)
                bpy.context.view_layer.objects.active = model_obj
                bpy.ops.object.rename_hkx_collision(
                    new_name=new_collision_name,
                    rename_parts=True,
                )
                print(f"  Renamed Collision model to: {model_obj.name}")

            elif part_subtype == BlenderMSBPartSubtype.Navmesh:
                new_navmesh_name = model_obj.name.replace(source_map_suffix, dest_map_suffix)
                bpy.context.view_layer.objects.active = model_obj
                bpy.ops.object.rename_nvm(
                    new_name=new_navmesh_name,
                    rename_parts=True,
                )
                print(f"  Renamed Navmesh model to: {model_obj.name}")


if __name__ == '__main__':
    # Example usage:
    main(
        source_map_stem="m10_01_00_00",
        dest_map_stem="m16_00_00_00",
        entry_filter_func=lambda obj: "_BURG" in obj.name
    )

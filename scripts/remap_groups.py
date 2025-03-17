"""Script that helps remaps the draw, display, and navmesh groups of all Parts in a map.

Also contains functions to change the IDs of Collisions and Navmeshes.
"""
import bpy

# Remapped in order from top to bottom.
GROUP_REMAP = {
    0: 10,
    1: 11,
    # ...
}


def _get_remapped_groups(remap_dict: dict[int, int], bit_set):
    new_set = set()
    for enabled_bit in bit_set.enabled_bits:
        new_bit = remap_dict.get(enabled_bit, enabled_bit)
        new_set.add(new_bit)
    return new_set


def remap_groups(map_stem: str, remap_dict: dict[int, int], region_tag: str, doit=False):

    from io_soulstruct.msb.darksouls1ptde.parts import BlenderMSBPart

    # Error raised here if Parts collection is absent.
    parts_col = bpy.data.collections[f"{map_stem} Parts"]

    for obj in parts_col.all_objects:

        if region_tag not in obj.name:
            continue
        if not obj.soulstruct_type == "MSB_PART":
            continue
        if obj.MSB_PART.entry_subtype == "MSB_CONNECT_COLLISION":
            continue  # different map's groups

        print(obj.name)
        draw_groups_props = obj.MSB_PART.get_draw_groups_props_128()
        draw_groups = BlenderMSBPart._get_groups_bit_set(draw_groups_props)
        if draw_groups.enabled_bits:
            print("  Draw Groups:")
            print("   ", sorted(draw_groups.enabled_bits))
            new_groups_set = _get_remapped_groups(remap_dict, draw_groups)
            print("   ", sorted(new_groups_set))
            if doit:
                BlenderMSBPart._set_groups_bit_set(draw_groups_props, new_groups_set)

        display_groups_props = obj.MSB_PART.get_display_groups_props_128()
        display_groups = BlenderMSBPart._get_groups_bit_set(display_groups_props)
        if display_groups.enabled_bits:
            print("  Display Groups:")
            print("   ", sorted(display_groups.enabled_bits))
            new_groups_set = _get_remapped_groups(remap_dict, display_groups)
            print("   ", sorted(new_groups_set))
            if doit:
                BlenderMSBPart._set_groups_bit_set(display_groups_props, new_groups_set)

        if obj.MSB_PART.entry_subtype == "MSB_NAVMESH":
            navmesh_groups_props = obj.MSB_NAVMESH.get_navmesh_groups_props_128()
            navmesh_groups = BlenderMSBPart._get_groups_bit_set(navmesh_groups_props)
            if navmesh_groups.enabled_bits:
                print("  Navmesh Groups:")
                print("   ", sorted(navmesh_groups.enabled_bits))
                new_groups_set = _get_remapped_groups(remap_dict, navmesh_groups)
                print("   ", sorted(new_groups_set))
                if doit:
                    BlenderMSBPart._set_groups_bit_set(navmesh_groups_props, new_groups_set)
        elif obj.MSB_PART.entry_subtype == "MSB_COLLISION":
            navmesh_groups_props = obj.MSB_COLLISION.get_navmesh_groups_props_128()
            navmesh_groups = BlenderMSBPart._get_groups_bit_set(navmesh_groups_props)
            if navmesh_groups.enabled_bits:
                print("  Navmesh Groups:")
                print("   ", sorted(navmesh_groups.enabled_bits))
                new_groups_set = _get_remapped_groups(remap_dict, navmesh_groups)
                print("   ", sorted(new_groups_set))
                if doit:
                    BlenderMSBPart._set_groups_bit_set(navmesh_groups_props, new_groups_set)


def rename_collision_models(remap_dict: dict[int, int], region_tag: str, doit=False):
    for obj in bpy.context.selected_objects:
        if obj.soulstruct_type != "COLLISION":
            continue
        if region_tag not in obj.name:
            print(f"NOT renaming Collision without given tag '{region_tag}': {obj.name}")
            continue

        old_name = obj.name
        old_id = int(old_name[1:5])
        try:
            new_id = remap_dict[old_id]
        except KeyError:
            print(f"NOT renaming Collision whose model ID is not a remapped group: {old_name}")
            continue
        new_name = f"h{new_id:04d}{old_name[5:]}"
        print(f"Renaming Collision: {old_name} -> {new_name}")
        if doit:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.rename_hkx_collision(new_name=new_name, rename_parts=True)


def rename_navmesh_models(remap_dict: dict[int, int], region_tag: str, doit=False):
    for obj in bpy.context.selected_objects:
        if obj.soulstruct_type != "NAVMESH":
            continue
        if region_tag not in obj.name:
            print(f"NOT renaming Navmesh without given tag '{region_tag}': {obj.name}")
            continue

        old_name = obj.name
        old_id = int(old_name[1:5])
        try:
            new_id = remap_dict[old_id]
        except KeyError:
            print(f"NOT renaming Navmesh whose model ID is not a remapped group: {old_name}")
            continue
        new_name = f"n{new_id:04d}{old_name[5:]}"
        print(f"Renaming Navmesh: {old_name} -> {new_name}")
        if doit:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.rename_nvm(new_name=new_name, rename_parts=True)


# Set `doit=True` to actually execute the changes, or leave as False to just preview changes in stdout.
remap_groups("m00_00_00_00", GROUP_REMAP, "_SUFFIX", False)
# rename_collision_models(GROUP_REMAP, "_SUFFIX", False)
# rename_navmesh_models(GROUP_REMAP, "_SUFFIX", False)

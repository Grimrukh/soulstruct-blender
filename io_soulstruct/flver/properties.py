from __future__ import annotations

__all__ = [
    "FLVERToolSettings",

    "FLVERProps",
    "FLVERDummyProps",
    "FLVERBoneProps",
]

import bpy

from soulstruct.base.models.flver.bone import FLVERBoneUsageFlags
from soulstruct.base.models.flver.material import Material

_MASK_ID_STRINGS = []


# noinspection PyUnusedLocal
def _get_display_mask_id_items(self, context) -> list[tuple[str, str, str]]:
    """Dynamic `EnumProperty` that iterates over all materials of selected meshes to find all unique Model Mask IDs."""
    _MASK_ID_STRINGS.clear()
    _MASK_ID_STRINGS.append("No Mask")
    items = [
        ("-1", "No Mask", "Select all materials that do not have a display mask"),
    ]  # type: list[tuple[str, str, str]]

    mask_id_set = set()  # type: set[str]
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        for mat in obj.data.materials:
            if match := Material.DISPLAY_MASK_RE.match(mat.name):
                mask_id = match.group(1)
                mask_id_set.add(mask_id)
    for mask_id in sorted(mask_id_set):
        _MASK_ID_STRINGS.append(mask_id)
        items.append(
            (mask_id, f"Mask {mask_id}", f"Select all materials with display mask {mask_id}")
        )
    return items


class FLVERToolSettings(bpy.types.PropertyGroup):
    """Holds settings for the various operators below. Drawn manually in operator browser windows."""

    vertex_color_layer_name: bpy.props.StringProperty(
        name="Vertex Color Layer",
        description="Name of the vertex color layer to use for setting vertex alpha",
        default="VertexColors0",
    )
    vertex_alpha: bpy.props.FloatProperty(
        name="Alpha",
        description="Alpha value to set for selected vertices",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    set_selected_face_vertex_alpha_only: bpy.props.BoolProperty(
        name="Set Selected Face Vertex Alpha Only",
        description="Only set alpha values for loops (face corners) that are part of selected faces",
        default=False,
    )
    dummy_id_draw_enabled: bpy.props.BoolProperty(name="Draw Dummy IDs", default=False)
    dummy_id_font_size: bpy.props.IntProperty(name="Dummy ID Font Size", default=16, min=1, max=100)

    uv_scale: bpy.props.FloatProperty(
        name="UV Scale",
        description="Scale to apply to UVs after unwrapping",
        default=1.0,
        min=0.0,
    )

    rebone_target_bone: bpy.props.StringProperty(
        name="Rebone Target Bone",
        description="New bone (vertex group) to assign to vertices with 'Rebone Vertices' operator",
    )

    display_mask_id: bpy.props.EnumProperty(
        name="Display Mask",
        items=_get_display_mask_id_items,
    )


class FLVERProps(bpy.types.PropertyGroup):
    """Extension properties for all Blender objects that represent FLVER models.

    These properties exist simply as `bpy.types.Object.flver` and are expected to be set on the FLVER Mesh objects, not
    their parent Armature objects.
    """

    big_endian: bpy.props.BoolProperty(
        name="Is Big Endian",
        description="If enabled, FLVER will be exported in big-endian format (old consoles only)",
        default=False,
    )
    version: bpy.props.EnumProperty(
        name="FLVER format version",
        description="Name of version enum for FLVER",
        items=[
            ("DEFAULT", "Selected Game", "Use default version of currently selected game in Blender"),
            ("DarkSouls2_Armor9320", "DarkSouls2_Armor9320", "Rare DS2 version"),
            ("DarkSouls_PS3_o0700_o0701", "DarkSouls_PS3_o0700_o0701", "Rare DS1 version for PS3"),
            ("DarkSouls_A", "DarkSouls_A", "Standard DS1 version (PTDE and DSR)"),
            ("DarkSouls_B", "DarkSouls_B", "Rare DS1 version"),
            ("DarkSouls2_NT", "DarkSouls2_NT", "DS2 network test version"),
            ("DarkSouls2", "DarkSouls2", "Standard DS2 version"),
            ("Bloodborne_DS3_A", "Bloodborne_DS3_A", "Standard Bloodborne/DS3 version (A)"),
            ("Bloodborne_DS3_B", "Bloodborne_DS3_B", "Standard Bloodborne/DS3 version (B)"),
            ("Sekiro_TestChr", "Sekiro_TestChr", "Sekiro test version"),
            ("Sekiro_EldenRing", "Sekiro_EldenRing", "Standard Sekiro/Elden Ring version"),
        ],
        default="Null",  # TODO: detect from active game
    )
    unicode: bpy.props.BoolProperty(
        name="Is Unicode",
        description="FLVER format uses unicode strings",
        default=True,  # TODO: automated from version?
    )
    unk_x4a: bpy.props.BoolProperty(
        name="Unk x4a",
        description="Unknown bool at FLVER header offset 0x4a",
        default=False,
    )
    unk_x4c: bpy.props.IntProperty(
        name="Unk x4c",
        description="Unknown integer at FLVER header offset x4c",
        default=0,
    )
    unk_x5c: bpy.props.IntProperty(
        name="Unk x5c",
        description="Unknown integer at FLVER header offset x5c",
        default=0,
    )
    unk_x5d: bpy.props.IntProperty(
        name="Unk x5d",
        description="Unknown integer at FLVER header offset x5d",
        default=0,
    )
    unk_x68: bpy.props.IntProperty(
        name="Unk x68",
        description="Unknown integer at FLVER header offset x68",
        default=0,
    )


class FLVERDummyProps(bpy.types.PropertyGroup):
    """Extension properties for Blender objects that represent FLVER Dummy objects."""

    parent_bone: bpy.props.PointerProperty(
        name="In Space of Bone",
        type=bpy.types.Bone,
        description="FLVER Bone that this Dummy's transform is parented to, if any. NOT the same as 'Attach' bone "
                    "followed in animations, which is set as real Blender parent), but is manually used to affect "
                    "exported transform",
    )
    color_rgba: bpy.props.IntVectorProperty(
        name="Color RGBA",
        description="Color of the Dummy object (8-bit channels)",
        size=4,
        default=(255, 255, 255, 255),
        min=0,
        max=255,
    )
    flag_1: bpy.props.BoolProperty(
        name="Flag 1",
        description="Unknown boolean flag at FLVER Dummy offset 0x2e",
        default=True,  # seems more common
    )
    use_upward_vector: bpy.props.BoolProperty(
        name="Use Upward Vector",
        description="If enabled, this Dummy object uses an upward vector for orientation",
        default=True,
    )
    unk_x30: bpy.props.IntProperty(
        name="Unk x30",
        description="Unknown integer at FLVER Dummy offset 0x30 (always zero before Sekiro)",
        default=0,
    )
    unk_x34: bpy.props.IntProperty(
        name="Unk x34",
        description="Unknown integer at FLVER Dummy offset 0x34 (always zero before Sekiro)",
        default=0,
    )


class FLVERBoneProps(bpy.types.PropertyGroup):
    """Extension properties for Blender Bones that represent FLVER bones."""

    is_unused: bpy.props.BoolProperty(
        name="Is Unused",
        description="Enabled if this bone is unused in the FLVER (bit flag 0b0001)",
        default=False,
    )
    is_used_by_local_dummy: bpy.props.BoolProperty(
        name="Is Used by Local Dummy",
        description="Enabled if this bone is used by a Dummy in this very FLVER (not an attached one like c0000) "
                    "(bit flag 0b0010)",
        default=False,
    )
    is_used_by_equipment: bpy.props.BoolProperty(
        name="Is Used by Equipment",
        description="Enabled if this bone is used by other equipment FLVERs that are rigged to this FLVER (e.g. c0000) "
                    "(bit flag 0b0100)",
        default=False,
    )
    is_used_by_local_mesh: bpy.props.BoolProperty(
        name="Is Used by Local Mesh",
        description="Enabled if this bone is used by the mesh of this very FLVER (bit flag 0b1000)",
        default=False,
    )

    def get_flags(self) -> int:
        flags = 0
        if self.is_unused:
            flags |= FLVERBoneUsageFlags.UNUSED
        if self.is_used_by_local_dummy:
            flags |= FLVERBoneUsageFlags.DUMMY
        if self.is_used_by_equipment:
            flags |= FLVERBoneUsageFlags.cXXXX
        if self.is_used_by_local_mesh:
            flags |= FLVERBoneUsageFlags.MESH
        return flags

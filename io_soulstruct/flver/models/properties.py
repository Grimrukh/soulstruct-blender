from __future__ import annotations

__all__ = [
    "FLVERProps",
    "FLVERDummyProps",
    "FLVERBoneProps",
    "FLVERImportSettings",
    "FLVERExportSettings",
]

import bpy

from soulstruct.base.models.flver.bone import FLVERBoneUsageFlags


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
        name="Version",
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
        default="DEFAULT",  # detected from active game
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

    # INTERNAL USE
    submesh_vertices_merged: bpy.props.BoolProperty(
        name="Submesh Vertices Merged",
        description="If disabled, submesh (material) vertices were NOT merged on import (faster but harder to edit)",
        default=False,
    )


class FLVERDummyProps(bpy.types.PropertyGroup):
    """Extension properties for Blender objects that represent FLVER Dummy objects."""

    parent_bone_name: bpy.props.StringProperty(
        name="In Space of Bone",
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


class FLVERImportSettings(bpy.types.PropertyGroup):
    """Common FLVER import settings. Drawn manually in operator browser windows."""

    merge_submesh_vertices: bpy.props.BoolProperty(
        name="Merge Submesh Vertices",
        description="Carefully merge FLVER submesh (material) vertices into a single mesh for easier editing. If "
                    "disabled, submeshes will still be merged into a single mesh, but their faces will not be joined "
                    "at any edges or vertices, making them painful to edit (but faster to import)",
        default=True,
    )

    import_textures: bpy.props.BoolProperty(
        name="Import Textures",
        description="Import DDS textures from TPFs in expected locations for detected FLVER model source type",
        default=True,
    )

    omit_default_bone: bpy.props.BoolProperty(
        name="Omit Default Bone",
        description="If imported FLVER has a single default bone (e.g. standard Map Pieces), do not create an "
                    "Armature parent object for the FLVER Mesh (default bone will be created again on export)",
        default=True,
    )

    material_blend_mode: bpy.props.EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ("OPAQUE", "Opaque", "Opaque Blend Mode"),
            ("CLIP", "Clip", "Clip Blend Mode"),
            ("HASHED", "Hashed", "Hashed Blend Mode"),
            ("BLEND", "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: bpy.props.FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )


class FLVERExportSettings(bpy.types.PropertyGroup):
    """Common FLVER export settings. Drawn manually in operator browser windows."""

    export_textures: bpy.props.BoolProperty(
        name="Export Textures",
        description="Export textures used by FLVER into bundled TPF, split CHRTPFBDT, or a map TPFBHD. Only works "
                    "when using a type-specific FLVER export operator. DDS formats for different texture types can be "
                    "set. Be wary of texture degradation from repeated DDS conversion at import/export",
        default=False,
    )

    create_lod_face_sets: bpy.props.BoolProperty(
        name="Create LOD Face Sets",
        description="Duplicate exported meshes (face set 0) to additional Level of Detail (LoD) face sets based on "
                    "each material's 'Face Set Count'. Acceptable for older games but not recommended for later games "
                    "with high-res meshes (unfortunately no good solution for this yet)",
        default=False,
    )

    base_edit_bone_length: bpy.props.FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    allow_missing_textures: bpy.props.BoolProperty(
        name="Allow Missing Textures",
        description="Allow ANY sampler nodes to have no Image assigned in Blender shader, not just those with no "
                    "default path specified in their MATBIN (for later games)",
        default=False,
    )

    allow_unknown_texture_types: bpy.props.BoolProperty(
        name="Allow Unknown Texture Types",
        description="Allow and export Blender texture nodes that have unrecognized sampler names",
        default=False,
    )

    normal_tangent_dot_max: bpy.props.FloatProperty(
        name="Normal/Tangent Dot Max",
        description="Maximum dot product between vertex normal and tangent vectors to NOT merge them on export. "
                    "Default of 0.999 corresponds to 2.56 degrees. Lower values will merge face corners into the same "
                    "vertices more aggressively. Value 1.0 will do no merging, which speeds up export but inflates "
                    "FLVER size with more duplicate vertices",
        default=0.999,
        precision=4,
        min=0.0,
        max=1.0,
    )

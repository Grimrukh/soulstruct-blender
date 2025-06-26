from __future__ import annotations

__all__ = [
    "FLVERProps",
    "FLVERDummyProps",
    "FLVERBoneProps",
    "FLVERImportSettings",
    "FLVERExportSettings",
]

import bpy

from soulstruct.flver import FLVERBoneUsageFlags, FLVERVersion
from soulstruct.games import *

from soulstruct.blender.bpy_base.property_group import SoulstructPropertyGroup


class FLVERProps(SoulstructPropertyGroup):
    """Extension properties for all Blender Mesh objects that represent FLVER models.

    These properties are stored on the Mesh, not any Armature parent.
    """

    # Valid properties can depend on each FLVER's `version`, not the active game.
    FLVER0_PROP_NAMES = (
        "big_endian",
        "version",
        "unicode",
        "f0_unk_x4a",
        "f0_unk_x4b",
        "f0_unk_x4c",
        "f0_unk_x5c",

        # Internal usage:
        "bone_data_type",
        "mesh_vertices_merged",
    )

    FLVER2_PROP_NAMES = (
        "big_endian",
        "version",
        "unicode",
        "f2_unk_x4a",
        "f2_unk_x4c",
        "f2_unk_x5c",
        "f2_unk_x5d",
        "f2_unk_x68",

        # Internal usage:
        "bone_data_type",
        "mesh_vertices_merged",
    )

    # Game-specific property names for each FLVER version.
    GAME_PROP_NAMES = {
        DEMONS_SOULS: FLVER0_PROP_NAMES,

        DARK_SOULS_PTDE: FLVER2_PROP_NAMES,
        DARK_SOULS_DSR: FLVER2_PROP_NAMES,
        BLOODBORNE: FLVER2_PROP_NAMES,
        ELDEN_RING: FLVER2_PROP_NAMES,
    }

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
            # NOTE: Old Demon's Souls versions are not supported, and will be converted to "DemonsSouls" on import.
            (FLVERVersion.DemonsSouls.name, "Demon's Souls", "Standard DeS version"),
            (FLVERVersion.DarkSouls2_Armor9320.name, "Dark Souls 2 (Armor 9320)", "Rare DS2 version"),
            (FLVERVersion.DarkSouls_PS3_o0700_o0701.name, "Dark Souls (PS3 o0700/o0701)", "Rare DS1 version for PS3"),
            (FLVERVersion.DarkSouls_A.name, "Dark Souls 1 (PTDE/DSR)", "DS1 version (PTDE and DSR)"),
            (FLVERVersion.DarkSouls_B.name, "Dark Souls 1 (Alt.)", "Rare DS1 version"),
            (FLVERVersion.DarkSouls2_NT.name, "Dark Souls 2 (NT)", "DS2 network test version"),
            (FLVERVersion.DarkSouls2.name, "Dark Souls 2", "Standard DS2 version"),
            (FLVERVersion.Bloodborne_DS3_A.name, "Bloodborne/DS3 (A)", "Standard Bloodborne/DS3 version (A)"),
            (FLVERVersion.Bloodborne_DS3_B.name, "Bloodborne/DS3 (B)", "Standard Bloodborne/DS3 version (B)"),
            (FLVERVersion.Sekiro_TestChr.name, "Sekiro (Test)", "Sekiro test version"),
            (FLVERVersion.Sekiro_EldenRing.name, "Sekiro/Elden Ring", "Standard Sekiro/Elden Ring version"),
            (FLVERVersion.ArmoredCore6.name, "Armored Core 6", "Standard Sekiro/Elden Ring version"),
        ],
        default="DEFAULT",  # detected from active game
    )
    unicode: bpy.props.BoolProperty(
        name="Is Unicode",
        description="FLVER format uses unicode strings",
        default=True,  # TODO: automated from version?
    )

    # Modern `FLVER` unknowns:
    f2_unk_x4a: bpy.props.BoolProperty(
        name="FLVER2 Unk x4a",
        description="Unknown bool at FLVER2 header offset 0x4a",
        default=False,
    )
    f2_unk_x4c: bpy.props.IntProperty(
        name="FLVER2 Unk x4c",
        description="Unknown integer at FLVER2 header offset 0x4c",
        default=0,
    )
    f2_unk_x5c: bpy.props.IntProperty(
        name="FLVER2 Unk x5c",
        description="Unknown integer at FLVER2 header offset 0x5c",
        default=0,
    )
    f2_unk_x5d: bpy.props.IntProperty(
        name="FLVER2 Unk x5d",
        description="Unknown integer at FLVER2 header offset 0x5d",
        default=0,
    )
    f2_unk_x68: bpy.props.IntProperty(
        name="FLVER2 Unk x68",
        description="Unknown integer at FLVER2 header offset 0x68",
        default=0,
    )

    # Old `FLVER0` unknowns:
    f0_unk_x4a: bpy.props.IntProperty(
        name="FLVER0 Unk x4a",
        description="Unknown integer at FLVER0 header offset 0x4a",
        default=1,
    )
    f0_unk_x4b: bpy.props.IntProperty(
        name="FLVER0 Unk x4b",
        description="Unknown integer at FLVER0 header offset 0x4b",
        default=0,
    )
    f0_unk_x4c: bpy.props.IntProperty(
        name="FLVER0 Unk x4c",
        description="Unknown integer at FLVER0 header offset 0x4c",
        default=65535,
    )
    f0_unk_x5c: bpy.props.IntProperty(
        name="FLVER0 Unk x5c",
        description="Unknown integer at FLVER0 header offset 0x5c",
        default=0,
    )

    # INTERNAL USE
    bone_data_type: bpy.props.EnumProperty(
        name="Bone Data Type",
        description="Indicates whether FLVER bone data was written to Edit Bone transforms (rigged FLVERs such as "
                    "Characters and most Objects) or Edit Bone custom data (static FLVERs such as Map Pieces; Edit "
                    "Bones all left at origin) or omitted entirely (ignorable default bone). The same data source will "
                    "be used on FLVER export",
        items=[
            (
                "EditBone",
                "Edit Bones",
                "Bone data is written to Edit Bones (usually Characters, Equipment, and most Objects, Assets)",
            ),
            (
                "Custom",
                "Custom (Initial Pose)",
                "Bone data is written to custom Edit Bone FLVER property and initially written to PoseBone data (may "
                "be overwritten by animation data; usually Map Pieces and some Objects)",
            ),
            (
                "Omitted",
                "Omitted",
                "Armature/Bones are omitted (usually Map Pieces with only one default bone)",
            ),
        ],
        default="EditBone",
    )

    mesh_vertices_merged: bpy.props.BoolProperty(
        name="Mesh Vertices Merged",
        description="If disabled, FLVER mesh (material) vertices were NOT merged on import (faster but harder to "
                    "edit). For import posterity only; does not affect export",
        default=False,
    )


class FLVERDummyProps(SoulstructPropertyGroup):
    """Extension properties for Blender objects that represent FLVER Dummy objects."""

    # No game-specific properties.

    parent_bone_name: bpy.props.StringProperty(
        name="In Space of Bone",
        description="Dummy transform in FLVER file is stored relative to this FLVER bone. NOT the same as the Dummy "
                    "attach bone that can be followed during animations, which is set as its real Blender parent",
    )
    color_rgba: bpy.props.IntVectorProperty(
        name="Color RGBA",
        description="Color of the Dummy object (8-bit channels). Not used in-game but useful for model visualization",
        size=4,
        default=(255, 255, 255, 255),
        min=0,
        max=255,
    )
    follows_attach_bone: bpy.props.BoolProperty(
        name="Follows Attach Bone",
        description="If enabled, Dummy will follow its attach bone (Blender parent bone) during animations. Note that "
                    "Dummies will always follow their attach bones here in Blender due to parenting, but will not do "
                    "so in-game if this is disabled",
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


class FLVERBoneProps(SoulstructPropertyGroup):
    """Extension properties for Blender Bones that represent FLVER bones."""

    # No game-specific properties.

    flver_translate: bpy.props.FloatVectorProperty(
        name="Translate",
        description="Custom bone translate to write to FLVER in 'Custom' bone data mode",
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    flver_rotate: bpy.props.FloatVectorProperty(
        name="Rotate",
        description="Custom bone rotate (Euler angles) to write to FLVER in 'Custom' bone data mode",
        size=3,
        default=(0.0, 0.0, 0.0),
    )
    flver_scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Custom bone scale to write to FLVER in 'Custom' bone data mode",
        size=3,
        default=(1.0, 1.0, 1.0),
    )

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


class FLVERImportSettings(SoulstructPropertyGroup):
    """Common FLVER import settings.

    Note that these are always drawn manually in operator browser windows, never in Panels.
    """

    # No game-specific properties.

    merge_mesh_vertices: bpy.props.BoolProperty(
        name="Merge Mesh Vertices",
        description="Carefully merge FLVER mesh (material) vertices into a single mesh for easier editing. If "
                    "disabled, FLVER meshes will still be merged into a single mesh, but their faces will not be "
                    "joined at any edges or vertices, making them painful to edit (but faster to import)",
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

    add_name_suffix: bpy.props.BoolProperty(
        name="Add Model Description Suffix",
        description="Add '<Description>' (if known) to the object name (e.g. character model names)",
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


class FLVERExportSettings(SoulstructPropertyGroup):
    """Common FLVER export settings. Drawn manually in operator browser windows."""

    # No game-specific properties.

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

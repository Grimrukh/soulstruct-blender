from __future__ import annotations

__all__ = [
    "FLVERImportSettings",
    "FLVERExportSettings",
]

import bpy


class FLVERImportSettings(bpy.types.PropertyGroup):
    """Common FLVER import settings. Drawn manually in operator browser windows."""

    import_textures: bpy.props.BoolProperty(
        name="Import Textures",
        description="Import DDS textures from TPFs in expected locations for detected FLVER model source type",
        default=True,
    )

    omit_default_bone: bpy.props.BoolProperty(
        name="Omit Default Bone",
        description="If imported FLVER has a single default bone (e.g. standard Map Pieces), do not create an "
                    "Armature object for it, and instead make the Mesh the root FLVER object",
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

    msb_entry_name_match: bpy.props.StringProperty(
        name="MSB Part Name Match",
        description="Glob/Regex for filtering MSB part names when importing all parts",
        default="*",
    )

    msb_entry_name_match_mode: bpy.props.EnumProperty(
        name="MSB Part Name Match Mode",
        description="Whether to use glob or regex for MSB part name matching",
        items=[
            ("GLOB", "Glob", "Use glob for MSB part name matching"),
            ("REGEX", "Regex", "Use regex for MSB part name matching"),
        ],
        default="GLOB",
    )

    include_pattern_in_parent_name: bpy.props.BoolProperty(
        name="Include Pattern in Parent Name",
        description="Include the glob/regex pattern in the name of the parent object for imported MSB parts",
        default=True,
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
        description="Duplicate exported meshes (face set 0) to additional LOD face sets based on each material's "
                    "'Face Set Count'. Not recommended for later games with high-resolution meshes (unfortunately no "
                    "good solution for this yet)",
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

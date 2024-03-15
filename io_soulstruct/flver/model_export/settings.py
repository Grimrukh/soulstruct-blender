from __future__ import annotations

__all__ = ["FLVERExportSettings"]

import bpy


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
        description="Allow MTD-defined textures to have no node image data in Blender",
        default=False,
    )

    allow_unknown_texture_types: bpy.props.BoolProperty(
        name="Allow Unknown Texture Types",
        description="Allow and export Blender texture nodes that have non-MTD-defined texture types",
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

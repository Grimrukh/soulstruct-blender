from __future__ import annotations

__all__ = [
    "AnimationImportSettings",
    "AnimationExportSettings",
]

import bpy

from ..base.register import io_soulstruct_properties, io_soulstruct_pointer_property
from .skeleton import HKX_SKELETON_BONE_SOURCE_ITEMS, HKXSkeletonBoneSource


@io_soulstruct_properties
@io_soulstruct_pointer_property(bpy.types.Scene, "animation_import_settings")
class AnimationImportSettings(bpy.types.PropertyGroup):

    to_60_fps: bpy.props.BoolProperty(
        name="To 60 FPS",
        description="Convert animation to 60 FPS (from FromSoft standard 30 FPS)",
        default=True,
    )


@io_soulstruct_properties
@io_soulstruct_pointer_property(bpy.types.Scene, "animation_export_settings")
class AnimationExportSettings(bpy.types.PropertyGroup):

    from_60_fps: bpy.props.BoolProperty(
        name="From 60 FPS",
        description="Convert animation to FromSoft standard 30 FPS from Blender 60 FPS",
        default=True,
    )

    selected_frames_only: bpy.props.BoolProperty(
        name="Selected Frames Only",
        description="Export only frames between current start and end (inclusive) of Blender timeline. Otherwise, "
                    "first to last keyframe times will be exported",
        default=False,
    )

    skeleton_bone_source: bpy.props.EnumProperty(
        name="Skeleton Bone Source",
        description="Which FLVER Armature bones to write to a newly generated HKX skeleton",
        items=HKX_SKELETON_BONE_SOURCE_ITEMS,
        default=HKXSkeletonBoneSource.TEMPLATE,
    )

    skeleton_include_ancestor_bones: bpy.props.BoolProperty(
        name="Include Ancestor Bones",
        description="Also export all ancestors of every sourced bone in a newly generated HKX skeleton. If disabled, "
                    "each bone is parented to its nearest exported ancestor instead",
        default=True,
    )

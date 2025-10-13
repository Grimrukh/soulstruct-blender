from __future__ import annotations

__all__ = [
    "FLVERPropsPanel",
    "FLVERDummyPropsPanel",
    "FLVERBonePropsPanel",
]

from soulstruct.flver import FLVERVersion

from soulstruct.blender.bpy_base.panel import SoulstructPanel
from ..types import BlenderFLVER, BlenderFLVERDummy


class FLVERPropsPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate FLVER fields for active object."""
    bl_label = "FLVER Properties"
    bl_idname = "OBJECT_PT_flver"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.active_object:
            return False
        return BlenderFLVER.is_obj_type(context.active_object)

    def draw(self, context):
        bl_flver = BlenderFLVER.from_armature_or_mesh(context.active_object)
        if bl_flver.version == "DEFAULT":
            # Use active game's properties.
            prop_names = bl_flver.type_properties.get_game_prop_names(context)
        elif FLVERVersion[bl_flver.version].is_flver0():
            prop_names = bl_flver.type_properties.FLVER0_PROP_NAMES
        else:
            prop_names = bl_flver.type_properties.FLVER2_PROP_NAMES

        for prop in prop_names:
            if prop == "mesh_vertices_merged":
                # Label only (value locked after import).
                txt = f"Meshes were {'' if bl_flver.mesh_vertices_merged else 'NOT '}merged on import."
                self.layout.label(text=txt)
            else:
                self.layout.prop(bl_flver.type_properties, prop)


class FLVERDummyPropsPanel(SoulstructPanel):
    """Draw a Panel in the Object properties window exposing the appropriate FLVER Dummy fields for active object."""
    bl_label = "FLVER Dummy Properties"
    bl_idname = "OBJECT_PT_flver_dummy"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context) -> bool:
        return BlenderFLVERDummy.is_obj_type(context.active_object)

    def draw(self, context):
        bl_dummy = BlenderFLVERDummy.from_active_object(context)
        props = bl_dummy.type_properties
        for prop in props.__annotations__:
            self.layout.prop(props, prop)


class FLVERBonePropsPanel(SoulstructPanel):
    """Draw a Panel in the Bone properties window exposing the appropriate FLVER Bone fields for active bone."""
    bl_label = "FLVER Bone Properties"
    bl_idname = "BONE_PT_flver_bone"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context) -> bool:
        if not context.bone or not context.active_object:
            return False
        # Only shown for bones in an FLVER armature.
        return BlenderFLVER.is_obj_type(context.active_object)

    def draw(self, context):
        if context.mode == "EDIT_ARMATURE":
            # Not safe to edit these properties in Edit Mode.
            self.layout.label(text="Unavailable in Edit Mode.")
            return

        self.layout.label(text="Transform Overrides (Local Space):")
        props = context.bone.FLVER_BONE
        for prop in props.__annotations__:
            self.layout.prop(props, prop)

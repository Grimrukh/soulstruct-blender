from __future__ import annotations

__all__ = [
    "FLVERPropsPanel",
    "FLVERDummyPropsPanel",
]

import bpy

from soulstruct.base.models import FLVERVersion

from ..types import BlenderFLVER, BlenderFLVERDummy


class FLVERPropsPanel(bpy.types.Panel):
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
        prop_names = bl_flver.type_properties.__annotations__
        if bl_flver.version == "DEFAULT":
            pass  # show all properties
        elif FLVERVersion[bl_flver.version].is_flver0():
            prop_names = [prop for prop in prop_names if not prop.startswith("f2_")]
        else:
            prop_names = [prop for prop in prop_names if not prop.startswith("f0_")]
        for prop in prop_names:
            self.layout.prop(bl_flver.type_properties, prop)


class FLVERDummyPropsPanel(bpy.types.Panel):
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

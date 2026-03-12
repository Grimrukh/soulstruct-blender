from __future__ import annotations

__all__ = [
    "FLVERPropsPanel",
    "FLVERDummyPropsPanel",
    "FLVERBonePropsPanel",
]

from soulstruct.flver import FLVERVersion

from soulstruct.blender.bpy_base.panel import SoulstructPanel
from ..types import BlenderFLVER, BlenderFLVERDummy
from ..properties import FLVERProps, FLVERSubmeshProps


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
        flver_props = bl_flver.type_properties  # type: FLVERProps
        if bl_flver.version == "DEFAULT":
            # Use active game's properties.
            prop_names = flver_props.get_game_prop_names(context)
        elif FLVERVersion[bl_flver.version].is_flver0():
            prop_names = flver_props.FLVER0_PROP_NAMES
        else:
            prop_names = list(flver_props.FLVER2_PROP_NAMES)
            # Put `f2_unk_*` props under a collapsed section.
            header, panel = self.layout.panel("FLVER2 Unknowns", default_closed=True)
            header.label(text="FLVER2 Unknowns")
            for f2_unk_prop in (
                "f2_unk_x4a",
                "f2_unk_x4c",
                "f2_unk_x5c",
                "f2_unk_x5d",
                "f2_unk_x68",
            ):
                prop_names.remove(f2_unk_prop)
                if panel:
                    panel.prop(flver_props, f2_unk_prop)

        for prop in prop_names:
            if prop == "mesh_vertices_merged":
                # Label only (value locked after import).
                txt = f"Meshes were {'' if bl_flver.mesh_vertices_merged else 'NOT '}merged on import."
                self.layout.label(text=txt)
            else:
                self.layout.prop(flver_props, prop)

        # Draw submesh properties, either global or as a list.
        if flver_props.submesh_props:
            submeshes_box = self.layout.box()
            for submesh_props in flver_props.submesh_props:
                submesh_props: FLVERSubmeshProps
                submesh_box = submeshes_box.box()
                # Show material name text.
                submesh_box.label(text=submesh_props.material.name if submesh_props.material else "<LOST MATERIAL>")
                for prop in submesh_props.get_all_prop_names():
                    submesh_box.prop(submesh_props, prop)
            # Draw button to clear all submesh properties (to use global instead).
            self.layout.operator("flver.clear_submesh_props", text="Clear Submesh Properties")
        else:
            submeshes_box = self.layout.box()
            submeshes_box.label(text="Global Submesh Properties:")
            submeshes_box.prop(flver_props, "global_is_dynamic", text="Is Dynamic")
            submeshes_box.prop(flver_props, "global_default_bone_index", text="Default Bone Index")
            submeshes_box.prop(flver_props, "global_face_set_count", text="Face Set Count")
            submeshes_box.label(text="Use Backface Culling: <From Material>")
            # Draw button to add per-submesh properties (to use instead of global).
            self.layout.operator("flver.add_submesh_props", text="Add Per-Material Submesh Properties")


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

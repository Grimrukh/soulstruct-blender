import bpy

from .operators import *

# ----------------------------------------
# Debug Material (global enable + mode UI)
# ----------------------------------------
class MaterialDebugPanel(bpy.types.Panel):
    bl_label = "Debug Material View"
    bl_idname = "MAPPROG_PT_debug_material"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Experimental"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        """Only show if the scene has the settings we use."""
        return hasattr(context.scene, "material_debug_settings")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        settings = context.scene.material_debug_settings

        # Injection controls
        inj = col.box()
        inj.label(text="Material Injection")
        row = inj.row(align=True)
        row.operator(AddDebugNodeGroupToMaterials.bl_idname, icon="SHADING_TEXTURE")
        row.operator(RemoveDebugNodeGroupFromMaterials.bl_idname, icon="X")
        inj.prop(settings, "enabled", text="Enable Debug Overlays")

        # Mode & per-mode options
        dbg = col.box()
        dbg.label(text="Debug Mode")
        dbg.prop(settings, "mode", text="Mode")
        if settings.mode == "ALPHA":
            dbg.prop(settings, "alpha_attr_name", text="Alpha Attribute")
            dbg.label(text="Shows vertex color alpha channel as heatmap.")
        elif settings.mode == "UV":
            dbg.prop(settings, "uv_checker_scale", text="UV Checker Scale")
            dbg.label(text="Node-only checker overlay for quick UV QA.")

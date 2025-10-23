from __future__ import annotations

__all__ = [
    "DEBUG_GROUP_NAME",
    "DEBUG_WRAP_LABEL",
    "MaterialDebugSettings",
    "sync_material_debug_nodes",
]

import bpy

DEBUG_GROUP_NAME = "SoulstructDebugGroup"
DEBUG_WRAP_LABEL = "SoulstructDebugWrap"


def sync_material_debug_nodes(context):
    ng = bpy.data.node_groups.get(DEBUG_GROUP_NAME)
    if not ng:
        return  # this function does not create the group

    settings = context.scene.material_debug_settings

    ng.nodes["DEBUG_ENABLED"].outputs[0].default_value = 1.0 if settings.enabled else 0.0
    ng.nodes["DEBUG_MODE"].outputs[0].default_value = settings.get_mode_value()
    ng.nodes["DEBUG_UV_CHECKER_SCALE"].outputs[0].default_value = settings.uv_checker_scale
    ng.nodes["DEBUG_ALPHA_ATTR"].attribute_name = settings.alpha_attr_name

# noinspection PyUnusedLocal
def _material_debug_sync(self, context):
    sync_material_debug_nodes(context)


class MaterialDebugSettings(bpy.types.PropertyGroup):
    """Global add-on settings stored in Scene."""

    MODE_NODE_VALUES = {
        "NONE": 0.0,
        "PROGRESS": 1.0,
        "ALPHA": 2.0,
        "UV": 3.0,
    }

    enabled: bpy.props.BoolProperty(
        name="Enable Material Debug Mode",
        description="Enable material debug mode for testing and development",
        default=False,
        update=_material_debug_sync,
    )

    mode: bpy.props.EnumProperty(
        name="Debug Mode",
        items=[
            ("NONE", "None", "No debug mode"),
            ("PROGRESS", "Progress", "Apply progress tint overlay to materials"),
            ("ALPHA", "Vertex Alpha", "Visualize vertex alpha on objects"),
            ("UV", "UV Density", "Visualize UV density on objects"),
        ],
        default="NONE",
        update=_material_debug_sync,
    )

    def get_mode_value(self) -> float:
        return self.MODE_NODE_VALUES.get(self.mode, 0.0)

    alpha_attr_name: bpy.props.StringProperty(
        name="Alpha Attribute Name",
        description="Name of the vertex color attribute to use for alpha visualization",
        default="VertexColors0",
        update=_material_debug_sync,
    )

    uv_checker_scale: bpy.props.FloatProperty(
        name="UV Checker Scale",
        description="Grid repeats per UV unit (bigger values = smaller tiles)",
        default=16.0, min=0.1, soft_max=128.0,
        update=_material_debug_sync,
    )

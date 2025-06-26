from __future__ import annotations

__all__ = [
    "hsv_color",
    "create_basic_material",
]


import bpy
from mathutils import Color


def hsv_color(hue: float, saturation: float, value: float, alpha=1.0) -> tuple[float, float, float, float]:
    """Create an RGBA color tuple from HSV and `alpha` values (all in range [0, 1])."""
    color = Color()
    color.hsv = (hue, saturation, value)
    return color.r, color.g, color.b, alpha


def create_basic_material(
    material_name: str, color: tuple[float, float, float, float], wireframe_pixel_width=0.0
) -> bpy.types.Material:
    """Create a very basic Blender material with a single diffuse `color`.

    If `wireframe_pixel_width > 0`, the material will also render a wireframe with lines of the given width.
    """
    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    nodes = bl_material.node_tree.nodes
    nodes.clear()
    links = bl_material.node_tree.links

    diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = color
    diffuse.location = (0, 0)

    # Also set viewport display diffuse color.
    bl_material.diffuse_color = color

    material_output = nodes.new(type="ShaderNodeOutputMaterial")
    material_output.location = (400, 0)

    if wireframe_pixel_width <= 0.0:
        # No wireframe. Just connect BSDF to output.
        links.new(diffuse.outputs["BSDF"], material_output.inputs["Surface"])
        return bl_material

    wireframe = nodes.new(type="ShaderNodeWireframe")
    wireframe.location = (0, 150)
    wireframe.inputs["Size"].default_value = wireframe_pixel_width
    wireframe.use_pixel_size = True

    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, -150)
    emission.inputs["Strength"].default_value = 1.0
    emission.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)  # black

    mix_shader = nodes.new(type="ShaderNodeMixShader")
    mix_shader.location = (200, 0)

    links.new(wireframe.outputs["Fac"], mix_shader.inputs["Fac"])
    links.new(diffuse.outputs["BSDF"], mix_shader.inputs[1])
    links.new(emission.outputs["Emission"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], material_output.inputs["Surface"])

    return bl_material

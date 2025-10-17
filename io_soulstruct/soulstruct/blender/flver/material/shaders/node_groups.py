from __future__ import annotations

__all__ = [
    "create_node_groups",
]

import bpy

from .enums import MathOperation
from .node_tree import new_shader_math_node
from soulstruct.blender.utilities.files import ADDON_PACKAGE_PATH


def create_node_groups():
    """One-off function for creating node groups for game-specific normal processing."""

    if "Process Specular" not in bpy.data.node_groups:
        group = bpy.data.node_groups.new("Process Specular", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_specular_processing_node_group(group, is_metallic=False)

    if "Process Specular (Metallic)" not in bpy.data.node_groups:
        group = bpy.data.node_groups.new("Process Specular (Metallic)", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_specular_processing_node_group(group, is_metallic=True)

    if "Flip Green, Compute Blue" not in bpy.data.node_groups:
        # For DSR.
        group = bpy.data.node_groups.new("Flip Green, Compute Blue", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_rg_normal_processing_node_group_tree(group)

    if "Flip Green" not in bpy.data.node_groups:
        # For most games.
        group = bpy.data.node_groups.new("Flip Green", 'ShaderNodeTree')
        group.use_fake_user = True
        _build_flip_green_node_group_tree(group)


def _build_specular_processing_node_group(tree: bpy.types.NodeTree, is_metallic: bool):

    # Create input/output sockets for group.
    tree.interface.new_socket(
        name="Color", description="Specular Map Texture Color Input", in_out="INPUT", socket_type="NodeSocketColor"
    )
    if is_metallic:
        tree.interface.new_socket(
            name="Metallic", description="Metallic strength", in_out="OUTPUT", socket_type="NodeSocketFloat"
        )
    else:
        tree.interface.new_socket(
            name="Specular IOR Level", description="Specular IOR level", in_out="OUTPUT", socket_type="NodeSocketFloat"
        )
    tree.interface.new_socket(
        name="Roughness", description="Specular roughness", in_out="OUTPUT", socket_type="NodeSocketFloat"
    )
    tree.interface.new_socket(
        name="Transmission Weight", description="Specular transmission", in_out="OUTPUT", socket_type="NodeSocketFloat"
    )

    # Create nodes for group input and output.
    group_in = tree.nodes.new('NodeGroupInput')
    group_in.location = (-400, 0)

    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (200, 0)

    # Separate the incoming color into R, G, B.
    sep_rgb = tree.nodes.new('ShaderNodeSeparateRGB')
    sep_rgb.location = (-200, 0)
    tree.links.new(group_in.outputs["Color"], sep_rgb.inputs[0])

    red_flip = new_shader_math_node(tree, MathOperation.SUBTRACT, (0, 150), 1.0, sep_rgb.outputs["R"])
    red_flip.name = red_flip.label = "Red Flip"
    green_flip = new_shader_math_node(tree, MathOperation.SUBTRACT, (0, 0), 1.0, sep_rgb.outputs["G"])
    green_flip.name = green_flip.label = "Green Flip"

    tree.links.new(red_flip.outputs[0], group_out.inputs["Metallic" if is_metallic else "Specular IOR Level"])
    tree.links.new(green_flip.outputs[0], group_out.inputs["Roughness"])
    tree.links.new(sep_rgb.outputs["B"], group_out.inputs["Transmission Weight"])  # not flipped


def _build_flip_green_node_group_tree(tree: bpy.types.NodeTree):
    """Build node group that just flips green channel."""

    # Create input/output sockets for group.
    tree.interface.new_socket(
        name="Color", description="Normal Map Texture Color Input", in_out="INPUT", socket_type="NodeSocketColor"
    )
    tree.interface.new_socket(
        name="Normal", description="Normal Map Color Output", in_out="OUTPUT", socket_type="NodeSocketColor"
    )

    # Create nodes for group input and output.
    group_in = tree.nodes.new('NodeGroupInput')
    group_in.location = (-400, 0)

    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (400, 0)

    # Separate the incoming color into R, G, B.
    sep_rgb = tree.nodes.new('ShaderNodeSeparateRGB')
    sep_rgb.location = (-200, 0)
    tree.links.new(group_in.outputs["Color"], sep_rgb.inputs[0])

    # Flip the G channel:
    flip_g = new_shader_math_node(tree, MathOperation.SUBTRACT, (0, 0), 1.0, sep_rgb.outputs["G"])
    flip_g.label = "Flip"

    # Recombine R, flipped G, and B channels.
    combine_rgb = tree.nodes.new('ShaderNodeCombineRGB')
    combine_rgb.location = (200, 0)
    tree.links.new(sep_rgb.outputs["R"], combine_rgb.inputs['R'])
    tree.links.new(flip_g.outputs[0], combine_rgb.inputs['G'])  # flipped
    tree.links.new(sep_rgb.outputs["B"], combine_rgb.inputs['B'])

    # Output the resulting normal.
    tree.links.new(combine_rgb.outputs[0], group_out.inputs["Normal"])


def _build_rg_normal_processing_node_group_tree(tree: bpy.types.NodeTree):

    # Create input/output sockets for group.
    tree.interface.new_socket(
        name="Color", description="Normal Map Texture Color Input", in_out="INPUT", socket_type="NodeSocketColor"
    )
    tree.interface.new_socket(
        name="Normal", description="Normal Map Color Output", in_out="OUTPUT", socket_type="NodeSocketColor"
    )

    ry = 200
    gy = 0
    by = -200

    # Create nodes for group input and output.
    group_in = tree.nodes.new('NodeGroupInput')
    group_in.location = (-400, 0)

    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (2200, 0)

    # Separate the incoming color into R, G, B.
    sep_rgb = tree.nodes.new('ShaderNodeSeparateRGB')
    sep_rgb.location = (-200, 0)
    tree.links.new(group_in.outputs["Color"], sep_rgb.inputs[0])

    # Process the Red channel (X):
    #    X_temp = 2*R - 1
    mult_r = new_shader_math_node(tree, MathOperation.MULTIPLY, (0, ry), input_0=sep_rgb.outputs["R"], input_1=2.0)
    sub_r = new_shader_math_node(tree, MathOperation.SUBTRACT, (200, ry), input_0=mult_r.outputs[0], input_1=1.0)
    # sub_r output is X in [-1,1].

    # Process the Green channel:
    #    First flip: G' = 1 - G
    flip_g = new_shader_math_node(
        tree, MathOperation.SUBTRACT, (0, gy), 1.0, sep_rgb.outputs["G"]
    )
    flip_g.label = "Flip"
    #    Then convert to [-1,1]: Y = 2*G' - 1
    mult_g = new_shader_math_node(tree, MathOperation.MULTIPLY, (200, gy), flip_g.outputs[0], 2.0)
    sub_g = new_shader_math_node(tree, MathOperation.SUBTRACT, (400, gy), mult_g.outputs[0], 1.0)

    # Compute X^2 and Y^2.
    x_sq = new_shader_math_node(tree, MathOperation.POWER, (600, ry), sub_r.outputs[0], 2.0)
    y_sq = new_shader_math_node(tree, MathOperation.POWER, (600, gy), sub_g.outputs[0], 2.0)

    # Sum X^2 and Y^2.
    sq_sum = new_shader_math_node(tree, MathOperation.ADD, (800, by), x_sq.outputs[0], y_sq.outputs[0])

    # Compute Z^2 = 1 - (X^2 + Y^2).
    z_sq = new_shader_math_node(tree, MathOperation.SUBTRACT, (1000, by), 1.0, sq_sum.outputs[0])

    # Clamp to ensure non-negative, then compute Z = sqrt(1 - X^2 - Y^2).
    z_sq_clamped = new_shader_math_node(tree, MathOperation.MAXIMUM, (1200, by), z_sq.outputs[0], 0.0)
    z = new_shader_math_node(tree, MathOperation.SQRT, (1400, by), z_sq_clamped.outputs[0])
    # `z` output is Z in [0,1] (since our input is hemispherical, Z is always positive).

    # Remap computed components back to [0,1] for Blender's Normal Map node:
    #    Remap function: Out = (component + 1) / 2
    add_x = new_shader_math_node(tree, MathOperation.ADD, (1600, 200), sub_r.outputs[0], 1.0)
    output_r = new_shader_math_node(tree, MathOperation.MULTIPLY, (1800, 200), add_x.outputs[0], 0.5)
    add_y = new_shader_math_node(tree, MathOperation.ADD, (1600, 0), sub_g.outputs[0], 1.0)
    output_g = new_shader_math_node(tree, MathOperation.MULTIPLY, (1800, 0), add_y.outputs[0], 0.5)
    add_z = new_shader_math_node(tree, MathOperation.ADD, (1600, -200), z.outputs[0], 1.0)
    output_b = new_shader_math_node(tree, MathOperation.MULTIPLY, (1800, -200), add_z.outputs[0], 0.5)

    # Recombine the remapped channels into one vector.
    combine_rgb = tree.nodes.new('ShaderNodeCombineRGB')
    combine_rgb.location = (2000, 0)
    tree.links.new(output_r.outputs[0], combine_rgb.inputs['R'])
    tree.links.new(output_g.outputs[0], combine_rgb.inputs['G'])  # flipped
    tree.links.new(output_b.outputs[0], combine_rgb.inputs['B'])  # computed

    # Output the resulting normal.
    tree.links.new(combine_rgb.outputs[0], group_out.inputs["Normal"])

def try_add_node_group(node_group_name: str):
    # Tries to add a node group to your file from the 'Shaders.blend' file, if it is not already added.
    if node_group_name in bpy.data.node_groups:
        return
    try:
        shaders_blend_path = ADDON_PACKAGE_PATH("Shaders.blend")
        with bpy.data.libraries.load(str(shaders_blend_path)) as (data_from, data_to):
            data_to.node_groups = [node_group_name]
    except:
        raise Exception("Could not locate the specified node group inside the 'Shaders.blend' file.")
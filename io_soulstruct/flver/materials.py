from __future__ import annotations

__all__ = [
    "get_submesh_blender_material",
]

import typing as tp

import bpy

from soulstruct.base.models.flver.material import Material
from soulstruct.base.models.flver.mesh import Mesh

from io_soulstruct.utilities import LoggingOperator
from .utilities import MTDInfo


def get_submesh_blender_material(
    operator: LoggingOperator,
    material: Material,
    material_name: str,
    mtd_info: MTDInfo,
    mesh: Mesh,
    blend_mode="HASHED",
) -> bpy.types.Material:
    """Create a new material in the current Blender scene from a FLVER material.

    Will use material texture stems to search for PNG or DDS images in the Blender image data. If no image is found,
    the texture will be left unassigned in the material.
    """

    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    if blend_mode:
        bl_material.blend_method = blend_mode

    # Critical `Material` information stored in custom properties.
    bl_material["Flags"] = material.flags  # int
    bl_material["GX Index"] = material.gx_index  # int
    bl_material["MTD Path"] = material.mtd_path  # str
    bl_material["Unk x18"] = material.unk_x18  # int
    # TODO: How to handle texture path prefixes? Look up names in map TPFBHDs on export and copy path?
    #  TPFBHD TPF contents don't actually have full paths, so maybe they're not even needed in the FLVER data.
    #  Test if this is the case and just drop them if possible.

    node_tree = bl_material.node_tree
    node_tree.nodes.remove(node_tree.nodes["Principled BSDF"])
    node_tree.links.clear()
    output_node = node_tree.nodes["Material Output"]
    builder = NodeTreeBuilder(node_tree)

    vertex_colors_node = builder.add_vertex_colors_node()
    uv_nodes = {}
    tex_image_nodes = {}  # type: dict[str, bpy.types.Node]
    bsdf_nodes = [None, None]  # type: list[bpy.types.Node | None]

    missing_textures = list(mtd_info.texture_types)
    for texture_type, texture in material.get_texture_dict().items():
        if texture_type not in mtd_info.texture_types:
            operator.warning(
                f"Texture type '{texture_type}' does not seem to be supported by shader '{material.mtd_name}'. "
                f"Creating FLVER material texture node anyway (with no UV input).",
            )
            uv_index = None
        elif texture_type not in missing_textures:
            operator.warning(
                f"Texture type '{texture_type}' occurred multiple times in FLVER material, which is invalid. Please "
                f"repair this corrupt FLVER file. Ignoring this texture.",
            )
            continue
        else:
            missing_textures.remove(texture_type)
            uv_index = mtd_info.texture_types[texture_type]

        if not texture.path:
            # Empty texture in FLVER (e.g. 'g_DetailBumpmap' in every single DS1 FLVER).
            tex_image_node = builder.add_tex_image_node(texture_type, None)
            tex_image_nodes[texture_type] = tex_image_node
            continue

        # Try to find texture in Blender image data as a PNG (preferred) or DDS.
        try:
            bl_image = bpy.data.images[texture.stem + ".png"]
        except KeyError:
            try:
                bl_image = bpy.data.images[texture.stem + ".dds"]
            except KeyError:
                operator.warning(
                    f"Could not find texture '{texture.stem}' in Blender image data. "
                    f"Creating FLVER material texture node anyway, but image will be unassigned.",
                )
                bl_image = None

        tex_image_node = builder.add_tex_image_node(texture_type, bl_image)
        tex_image_nodes[texture_type] = tex_image_node

        if uv_index is not None:
            # Connect to appropriate UV node, creating it if necessary.
            uv_map_name = f"UVMap{uv_index}"
            if uv_map_name in uv_nodes:
                uv_node = uv_nodes[uv_map_name]
            else:
                uv_node = uv_nodes[uv_map_name] = builder.add_uv_node(uv_map_name)
            builder.link(uv_node.outputs["Vector"], tex_image_node.inputs["Vector"])

    if mtd_info.is_water:
        # Special simplified shader. Uses 'g_Bumpmap' only.
        water_mix = builder.new("ShaderNodeMixShader", (builder.MIX_X, builder.MIX_Y))
        transparent = builder.new("ShaderNodeBsdfTransparent", (builder.BSDF_X, 0))
        glass = builder.new("ShaderNodeBsdfGlass", (builder.BSDF_X, 1000), input_defaults={"IOR": 1.333})
        builder.link(transparent.outputs[0], water_mix.inputs[1])
        builder.link(glass.outputs[0], water_mix.inputs[2])

        bumpmap_node = tex_image_nodes["g_Bumpmap"]
        normal_map_node = builder.add_normal_map_node("UVMap1", bumpmap_node.location[1])

        builder.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
        builder.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
        builder.link(vertex_colors_node.outputs["Alpha"], water_mix.inputs["Fac"])
        return bl_material

    # Standard shader: one or two Principled BSDFs mixed 50/50, or one Principled BSDF mixed with a Transparent BSDF
    # for alpha-supporting shaders (includes edge shaders currently).
    bsdf_nodes[0] = builder.add_principled_bsdf_node("Texture Slot 1")
    if mtd_info.has_two_slots:
        bsdf_nodes[1] = builder.add_principled_bsdf_node("Texture Slot 1")
        mix_node = builder.new("ShaderNodeMixShader", location=(builder.MIX_X, builder.MIX_Y))
        builder.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
        builder.link(bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
        builder.link(vertex_colors_node.outputs["Alpha"], mix_node.inputs["Fac"])
        builder.link(mix_node.outputs["Shader"], output_node.inputs["Surface"])
    elif mtd_info.alpha or mtd_info.edge:
        # Mix main Principled BSDF with a Transparent BSDF using vertex alpha.
        # TODO: Assumes single BSDF; will not render with second texture slot at all. Confirm 'M' shaders never use Alp.
        transparent_node = builder.new("ShaderNodeBsdfTransparent", location=(builder.BSDF_X, builder.bsdf_y))
        mix_node = builder.new("ShaderNodeMixShader", location=(builder.MIX_X, builder.MIX_Y))
        builder.link(transparent_node.outputs["BSDF"], mix_node.inputs[1])
        builder.link(bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[2])  # more vertex alpha -> more opacity
        builder.link(vertex_colors_node.outputs["Alpha"], mix_node.inputs["Fac"])
        builder.link(mix_node.outputs["Shader"], output_node.inputs["Surface"])
    else:
        builder.link(bsdf_nodes[0].outputs["BSDF"], output_node.inputs["Surface"])

    if "g_Lightmap" in tex_image_nodes:
        lightmap_node = tex_image_nodes["g_Lightmap"]
        for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
            if texture_type not in tex_image_nodes:
                continue
            bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
            if bsdf_node is None:
                continue  # TODO: bad state
            tex_image_node = tex_image_nodes[texture_type]
            overlay_node_y = tex_image_node.location[1]
            overlay_node = builder.new(
                "ShaderNodeMixRGB", location=(builder.OVERLAY_X, overlay_node_y), blend_type="OVERLAY"
            )
            builder.link(tex_image_node.outputs["Color"], overlay_node.inputs["Color1"])
            builder.link(lightmap_node.outputs["Color"], overlay_node.inputs["Color2"])  # order is important!

            bsdf_input = "Base Color" if texture_type.startswith("g_Diffuse") else "Specular"
            builder.link(overlay_node.outputs["Color"], bsdf_node.inputs[bsdf_input])
            if texture_type.startswith("g_Diffuse"):
                # Plug diffuse alpha into BSDF alpha.
                builder.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
    else:
        # Plug diffuse and specular textures directly into Principled BSDF.
        for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
            if texture_type not in tex_image_nodes:
                continue
            bsdf_node = bsdf_nodes[1] if texture_type.endswith("_2") else bsdf_nodes[0]
            if bsdf_node is None:
                continue  # TODO: bad state
            tex_image_node = tex_image_nodes[texture_type]
            if texture_type.startswith("g_Diffuse"):
                builder.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                builder.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            else:  # g_Specular[_2]
                builder.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Specular"])

    if "g_Height" in tex_image_nodes:
        height_node = tex_image_nodes["g_Height"]
        displace_node = builder.new("ShaderNodeDisplacement", location=(builder.OVERLAY_X, height_node.location[1]))
        # TODO: Is UVMap1 correct for displacement? Should I mix UV map data using vertex alpha here?
        builder.link(uv_nodes["UVMap1"].outputs["Vector"], height_node.inputs["Vector"])
        builder.link(height_node.outputs["Color"], displace_node.inputs["Normal"])
        builder.link(displace_node.outputs["Displacement"], output_node.inputs["Displacement"])

    for texture_type, bsdf_node in zip(("g_Bumpmap", "g_Bumpmap_2"), bsdf_nodes):
        if texture_type not in tex_image_nodes or texture_type not in mtd_info.texture_types:
            continue
        if bsdf_node is None:
            continue  # TODO: bad state
        # Create normal map node.
        bumpmap_node = tex_image_nodes[texture_type]
        uv_index = mtd_info.texture_types[texture_type]
        uv_map_name = f"UVMap{uv_index}"
        normal_map_node = builder.add_normal_map_node(uv_map_name, bumpmap_node.location[1])
        builder.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
        builder.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    # Set additional real and custom properties from FLVER submesh.
    bl_material["Is Bind Pose"] = mesh.is_bind_pose
    # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
    bl_material["Default Bone Index"] = mesh.default_bone_index
    # Currently, main face set is simply copied to all additional face sets on export.
    bl_material["Face Set Count"] = len(mesh.face_sets)
    bl_material.use_backface_culling = mesh.cull_back_faces

    return bl_material


class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials."""

    tree: bpy.types.NodeTree

    # X coordinates of node type columns.
    VERTEX_COLORS_X = -950
    UV_X = -750
    TEX_X = -550
    OVERLAY_X = -250  # includes Normal Map node for 'g_Bumpmap'
    BSDF_X = -50
    MIX_X, MIX_Y = 150, 0  # only one (max)
    OUTPUT_X, OUTPUT_Y = 250, 0  # only one

    def __init__(self, node_tree: bpy.types.NodeTree):
        self.tree = node_tree

        # Auto-decremented Y coordinates for each node type (so newer nodes are further down).
        self.uv_y = 1000
        self.tex_y = 1000
        self.bsdf_y = 1000

    def new(
        self, node_type: str, location: tuple[int, int] = None, /, input_defaults: dict[str, tp.Any] = None, **kwargs
    ) -> bpy.types.Node:
        node = self.tree.nodes.new(node_type)
        if location is not None:
            node.location = location
        for k, v in kwargs.items():
            setattr(node, k, v)
        if input_defaults:
            for k, v in input_defaults.items():
                node.inputs[k].default_value = v
        return node

    def link(self, node_output, node_input) -> bpy.types.NodeLink:
        return self.tree.links.new(node_output, node_input)

    def add_vertex_colors_node(self) -> bpy.types.Node:
        return self.new(
            "ShaderNodeAttribute",
            location=(self.OVERLAY_X, 1200),
            name="VertexColors",
            attribute_name="VertexColors",
        )

    def add_uv_node(self, uv_map_name: str):
        """Create an attribute node for the given UV layer name."""
        node = self.new(
            "ShaderNodeAttribute",
            location=(self.UV_X, self.uv_y),
            name=uv_map_name,
            attribute_name=uv_map_name,
            label=uv_map_name,
        )
        self.uv_y -= 1000
        return node

    def add_tex_image_node(self, texture_type: str, image: bpy.types.Image | None):
        node = self.new(
            "ShaderNodeTexImage",
            location=(self.TEX_X, self.tex_y),
            image=image,
            name=texture_type,
            label=texture_type,
        )
        self.tex_y -= 330
        return node

    def add_principled_bsdf_node(self, bsdf_name: str):
        node = self.new(
            "ShaderNodeBsdfPrincipled",
            location=(self.BSDF_X, self.bsdf_y),
            name=bsdf_name,
            input_defaults={"Roughness": 0.75},
        )
        self.bsdf_y -= 1000
        return node

    def add_normal_map_node(self, uv_map_name: str, location_y: float):
        return self.new(
            "ShaderNodeNormalMap",
            location=(self.OVERLAY_X, location_y),
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": 0.4},
        )

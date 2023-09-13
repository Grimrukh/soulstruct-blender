from __future__ import annotations

__all__ = [
    "flver_to_blender_material",
]

import typing as tp

import bpy

from soulstruct.containers import Binder, BinderEntryNotFoundError
from soulstruct.base.models.flver.material import Material
from soulstruct.base.models.mtd import MTD

from io_soulstruct.utilities import LoggingOperator
from .utilities import MTDInfo


def flver_to_blender_material(
    operator: LoggingOperator,
    material: Material,
    material_name: str,
    blend_mode="HASHED",
    mtdbnd: Binder | None = None,
) -> bpy.types.Material:
    """Create a new material in the current Blender scene from a FLVER material."""
    bl_material = bpy.data.materials.new(name=material_name)
    bl_material.use_nodes = True
    if blend_mode:
        bl_material.blend_method = blend_mode

    # Critical `Material` information stored in custom properties.
    bl_material["MTD Path"] = material.mtd_path  # str
    bl_material["Flags"] = material.flags  # int
    bl_material["GX Index"] = material.gx_index  # int
    bl_material["Unk x18"] = material.unk_x18  # int
    # TODO: How to handle texture path prefixes? Look up names in map TPFBHDs on export and copy path?
    #  TPFBHD TPF contents don't actually have full paths, so maybe they're not even needed in the FLVER data.
    #  Test if this is the case and just drop them if possible.

    node_tree = bl_material.node_tree
    node_tree.nodes.remove(node_tree.nodes["Principled BSDF"])
    node_tree.links.clear()
    output_node = node_tree.nodes["Material Output"]
    builder = NodeTreeBuilder(node_tree)

    mtd_info = None
    if mtdbnd:
        # Search for MTD by name in MTD BND.
        try:
            mtd_entry = mtdbnd.find_entry_matching_name(material.mtd_name)
        except BinderEntryNotFoundError:
            operator.warning(
                f"Could not find MTD '{material.mtd_name}' in given MTDBND. Guessing shader setup from name."
            )
        else:
            mtd_info = MTDInfo.from_mtd_file(mtd_entry.to_binary_file(MTD))

    if mtd_info is None:
        mtd_info = MTDInfo.from_mtd_name(material.mtd_name)

    vertex_colors_node = builder.add_vertex_colors_node()
    created_uv_nodes = {}  # TODO: make sure extra UV data is still exported (plants, etc.)
    created_tex_image_nodes = {}  # type: dict[str, bpy.types.Node]
    created_bsdf_nodes = [None, None]  # type: list[bpy.types.Node | None]

    missing_textures = list(mtd_info.texture_types)
    for texture_type, texture in material.get_texture_dict().items():
        # TODO: Warn if FLVER texture is unsupported by shader.
        #  Also warn if FLVER texture is missing (except for 'g_DetailBumpmap').
        if texture_type not in mtd_info.texture_types:
            operator.warning(
                f"Texture type '{texture_type}' does not seem to be supported by shader '{mtd_info.shader_name}'. "
                f"Creating FLVER material texture node anyway.",
            )
        elif texture_type not in missing_textures:
            operator.warning(
                f"Texture type '{texture_type}' occurred multiple times in FLVER material, which is invalid. Please "
                f"repair this corrupt FLVER file. Ignoring this texture.",
            )
            continue

        missing_textures.remove(texture_type)
        if not texture.path:
            # Empty texture in FLVER (e.g. 'g_DetailBumpmap' in every single DS1 FLVER).
            tex_image_node = builder.add_tex_image_node(texture_type, None)
            created_tex_image_nodes[texture_type] = tex_image_node
            continue

        # Try to find texture in Blender image data as a PNG (preferred) or DDS.
        try:
            bl_image = bpy.data.images.load(texture.stem + ".png")
        except KeyError:
            try:
                bl_image = bpy.data.images.load(texture.stem + ".dds")
            except KeyError:
                operator.warning(
                    f"Could not find texture '{texture.stem}' in Blender image data. "
                    f"Creating FLVER material texture node anyway, but image will be unassigned.",
                )
                bl_image = None

        tex_image_node = builder.add_tex_image_node(texture_type, bl_image)
        created_tex_image_nodes[texture_type] = tex_image_node

        # Connect to appropriate UV node, creating it if necessary.
        uv_index = mtd_info.texture_types[texture_type]
        uv_map_name = f"UVMap{uv_index}"
        uv_node = created_uv_nodes.setdefault(uv_map_name, builder.add_uv_node(uv_map_name))
        builder.link(uv_node.outputs["Vector"], tex_image_node.inputs["Vector"])

    if mtd_info.is_water:
        # Special simplified shader. Uses 'g_Bumpmap' only.
        water_mix = builder.new("ShaderNodeMixShader", (builder.mix_x, builder.mix_y))
        transparent = builder.new("ShaderNodeBsdfTransparent", (builder.bsdf_x, builder.bsdf_y))
        glass = builder.new(
            "ShaderNodeBsdfGlass", (builder.mix_x, builder.mix_y), input_defaults={"IOR": 1.333}
        )
        builder.link(transparent.outputs[0], water_mix.inputs[1])
        builder.link(glass.outputs[0], water_mix.inputs[2])

        bumpmap_node = created_tex_image_nodes["g_Bumpmap"]
        normal_node_location = (builder.overlay_x, bumpmap_node.location[1])
        normal_map_node = builder.add_normal_map_node("UVMap1", normal_node_location)

        builder.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
        builder.link(normal_map_node.outputs["Normal"], glass.inputs["Normal"])
        builder.link(vertex_colors_node.outputs["Alpha"], water_mix.inputs["Fac"])
        return bl_material

    created_bsdf_nodes[0] = builder.add_principled_bsdf_node("Texture Slot 1")
    if mtd_info.multiple:
        created_bsdf_nodes[1] = builder.add_principled_bsdf_node("Texture Slot 1")
        mix_node = builder.new("ShaderNodeMixShader", location=(builder.mix_x, builder.mix_y))
        builder.link(created_bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[1])
        builder.link(created_bsdf_nodes[1].outputs["BSDF"], mix_node.inputs[2])
        builder.link(vertex_colors_node.outputs["Alpha"], mix_node.inputs["Fac"])
        builder.link(mix_node.outputs["Shader"], output_node.inputs["Surface"])
    elif mtd_info.alpha or mtd_info.edge:
        # Mix with a Transparent BSDF.
        # TODO: Assumes single BSDF; will not render with second texture slot at all. Confirm 'M' shaders have no Alp.
        transparent_node = builder.new("ShaderNodeBsdfTransparent", location=(builder.bsdf_x, builder.bsdf_y))
        mix_node = builder.new("ShaderNodeMixShader", location=(builder.mix_x, builder.mix_y))
        builder.link(transparent_node.outputs["BSDF"], mix_node.inputs[1])
        builder.link(created_bsdf_nodes[0].outputs["BSDF"], mix_node.inputs[2])  # more vertex alpha -> more opacity
        builder.link(vertex_colors_node.outputs["Alpha"], mix_node.inputs["Fac"])
        builder.link(mix_node.outputs["Shader"], output_node.inputs["Surface"])
    else:
        builder.link(created_bsdf_nodes[0].outputs["BSDF"], output_node.inputs["Surface"])

    if "g_Lightmap" in created_tex_image_nodes:
        lightmap_node = created_tex_image_nodes["g_Lightmap"]
        for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
            if texture_type not in created_tex_image_nodes:
                continue
            bsdf_node = created_bsdf_nodes[1] if texture_type.endswith("_2") else created_bsdf_nodes[0]
            if bsdf_node is None:
                continue  # TODO: bad state
            tex_image_node = created_tex_image_nodes[texture_type]
            mix_node_location = (builder.overlay_x, tex_image_node.location[1])
            mix_node = builder.new("ShaderNodeMixRGB", location=mix_node_location, blend_type="OVERLAY")
            builder.link(lightmap_node.outputs["Color"], mix_node.inputs["Color1"])
            builder.link(tex_image_node.outputs["Color"], mix_node.inputs["Color2"])

            bsdf_input = "Base Color" if texture_type.startswith("g_Diffuse") else "Specular"
            builder.link(mix_node.outputs["Color"], bsdf_node.inputs[bsdf_input])
    else:
        # Plug diffuse and specular textures directly into Principled BSDF.
        for texture_type in ("g_Diffuse", "g_Specular", "g_Diffuse_2", "g_Specular_2"):
            if texture_type not in created_tex_image_nodes:
                continue
            bsdf_node = created_bsdf_nodes[1] if texture_type.endswith("_2") else created_bsdf_nodes[0]
            if bsdf_node is None:
                continue  # TODO: bad state
            tex_image_node = created_tex_image_nodes[texture_type]
            if texture_type.startswith("g_Diffuse"):
                builder.link(tex_image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
                builder.link(tex_image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
            else:  # g_Specular[_2]
                builder.link(tex_image_node.outputs["Specular"], bsdf_node.inputs["Specular"])

    if "g_Height" in created_tex_image_nodes:
        height_node = created_tex_image_nodes["g_Height"]
        location = (builder.overlay_x, height_node.location[1])
        displace_node = builder.new("ShaderNodeDisplacement", location=location)
        # TODO: Is UVMap1 correct? Should I mix UV map data using vertex alpha here?
        builder.link(created_uv_nodes["UVMap1"].outputs["Vector"], height_node.inputs["Vector"])
        builder.link(height_node.outputs["Color"], displace_node.inputs["Normal"])
        builder.link(displace_node.outputs["Displacement"], output_node.inputs["Displacement"])

    for texture_type, bsdf_node in zip(("g_Bumpmap", "g_Bumpmap_2"), created_bsdf_nodes):
        if texture_type not in created_tex_image_nodes:
            continue
        if bsdf_node is None:
            continue  # TODO: bad state
        # Create normal map node.
        bumpmap_node = created_tex_image_nodes[texture_type]
        uv_map_name = f"UVMap{mtd_info.texture_types[texture_type]}"
        location = (builder.overlay_x, bumpmap_node.location[1])
        normal_map_node = builder.add_normal_map_node(uv_map_name, location)
        builder.link(bumpmap_node.outputs["Color"], normal_map_node.inputs["Color"])
        builder.link(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    return bl_material


class NodeTreeBuilder:
    """Wraps a Blender `NodeTree` and adds utility methods for creating/linking nodes for FLVER materials."""

    tree: bpy.types.NodeTree

    def __init__(self, node_tree: bpy.types.NodeTree):
        self.tree = node_tree
        self.tree.nodes.clear()

        self.uv_x, self.uv_y = -750, 0
        self.tex_x, self.tex_y = -550, 0
        self.overlay_x, self.overlay_y = -350, 0  # includes Normal Map node for g_Bumpmap
        self.bsdf_x, self.bsdf_y = -150, 0
        self.mix_x, self.mix_y = 50, 0
        self.output_x, self.output_y = 150, 0

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
        node = self.new(
            "ShaderNodeAttribute",
            location=(self.uv_x, -150),
            name="VertexColors",
            attribute_name="VertexColors",
        )
        return node

    def add_uv_node(self, uv_map_name: str):
        """Create an attribute node for the given UV layer name."""
        node = self.new(
            "ShaderNodeAttribute",
            location=(self.uv_x, self.uv_y),
            name=uv_map_name,
            attribute_name=uv_map_name,
        )
        self.uv_y += 1000
        return node

    def add_tex_image_node(self, texture_type: str, image: bpy.types.Image | None):
        node = self.new(
            "ShaderNodeTexImage",
            location=(self.tex_x, self.tex_y),
            image=image,
            name=texture_type,
        )
        self.tex_y += 330
        return node

    def add_principled_bsdf_node(self, bsdf_name: str):
        node = self.new(
            "ShaderNodeBsdfPrincipled",
            location=(self.bsdf_x, self.bsdf_y),
            name=bsdf_name,
            input_defaults={"Roughness": 0.75},
        )
        self.bsdf_y += 1000
        return node

    def add_normal_map_node(self, uv_map_name: str, location: tuple[float, float]):
        return self.new(
            "ShaderNodeNormalMap",
            location=location,
            space="TANGENT",
            uv_map=uv_map_name,
            input_defaults={"Strength": 0.4},
        )

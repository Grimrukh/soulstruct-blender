from __future__ import annotations

__all__ = [
    "BlenderImageDict",
    "MaterialNodeCreator",
]

import typing as tp

import bpy

if tp.TYPE_CHECKING:
    from soulstruct.base.models.flver.material import Material, Texture
    from io_soulstruct.utilities import LoggingOperator


# TODO: Turn into import settings.
NORMAL_MAP_STRENGTH = 0.4
# TODO: Maybe water normal strength should be greater than for regular materials.
WATER_NORMAL_MAP_STRENGTH = 0.4
ROUGHNESS = 0.75


class MaterialNodeCreator:
    """Handles creation of various shader node trees that hold textures and simulate FromSoft materials."""

    def create_material(
        self,
        flver_material: Material,
        material_name: str,
        material_blend_mode="HASHED",
    ):
        """Create a Blender material that represents a single `FLVER.Material`.

        NOTE: Actual information contained in the FLVER and used for export is stored in custom properties of the
        Blender material. The node graph generated here is simply for (very helpful) visualization in Blender, and is
        NOT synchronized at all with the custom properties.

        If `use_existing=False`, a new material will be created with the FLVER's values even if a material with that
        name already exists in the Blender environment. Be wary of texture RAM usage in this case! Make sure you delete
        unneeded materials from Blender as you go.
        """
        bl_material = bpy.data.materials.new(name=material_name)  # Blender will add '.###' suffix as needed
        if material_blend_mode:
            bl_material.blend_method = material_blend_mode

        # Get longest shared path between all textures.
        shared_texture_path_prefix = flver_material.get_shared_texture_path_prefix(
            exclude_names=True, exclude_empty_paths=True
        )

        # Texture information is also stored here, using an index 'texture[i]_' prefix.
        for i, game_tex in enumerate(flver_material.textures):
            bl_material[f"texture[{i}]_path_suffix"] = game_tex.path.removeprefix(shared_texture_path_prefix)  # str
            bl_material[f"texture[{i}]_texture_type"] = game_tex.texture_type  # str
            bl_material[f"texture[{i}]_scale"] = tuple(game_tex.scale)  # tuple[float]
            bl_material[f"texture[{i}]_unk_x10"] = game_tex.unk_x10  # int
            bl_material[f"texture[{i}]_unk_x11"] = game_tex.unk_x11  # bool
            bl_material[f"texture[{i}]_unk_x14"] = game_tex.unk_x14  # float
            bl_material[f"texture[{i}]_unk_x18"] = game_tex.unk_x18  # float
            bl_material[f"texture[{i}]_unk_x1C"] = game_tex.unk_x1C  # float

        mtd_info = flver_material.get_mtd_info()

        bl_material.use_nodes = True
        nt = bl_material.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        output_node = nt.nodes["Material Output"]

        textures = flver_material.get_texture_dict()

        # TODO: Finesse node coordinates.

        bsdf_1 = diffuse_node_1 = bsdf_2 = diffuse_node_2 = None
        if mtd_info.diffuse or mtd_info.specular:
            bsdf_1, diffuse_node_1 = self.create_bsdf_node(textures, mtd_info, nt, is_second_slot=False)
        elif mtd_info.water:
            # Pure water shaders, such as 'A10_Water_sewer[We].mtd', do not use any BSDF nodes (bumpmap only).
            if "g_Bumpmap" not in textures:
                self._operator.report(
                    {"WARNING"},
                    f"Material '{flver_material.name}' with water shader '{flver_material.mtd_name}' does not have a "
                    f"'g_Bumpmap' texture. Blender material node tree will be incomplete."
                )
                return bl_material
            bsdf_1 = self.create_water_shader(nt, textures["g_Bumpmap"], vertex_colors_node)
        else:
            # TODO: some kind of shader for materials like 'Snow[L].mtd'
            self._operator.warning(
                f"Imported material '{flver_material.name}' will have no shader output (MTD {flver_material.mtd_name})"
            )

        # print(f"\nCreating Blender material for {flver_material.name}...")
        # print(mtd_info)

        if mtd_info.multiple or mtd_info.alpha:
            # Use a mix shader weighted by vertex alpha.
            slot_mix_shader = nt.nodes.new("ShaderNodeMixShader")
            slot_mix_shader.location = (50, 300)
            nt.links.new(vertex_colors_node.outputs["Alpha"], slot_mix_shader.inputs["Fac"])
            nt.links.new(slot_mix_shader.outputs[0], output_node.inputs["Surface"])
        else:
            slot_mix_shader = None
            if bsdf_1:
                nt.links.new(bsdf_1.outputs[0], output_node.inputs["Surface"])

        if mtd_info.multiple:
            # Multi-textures shader (two slots).
            bsdf_2, diffuse_node_2 = self.create_bsdf_node(textures, mtd_info, nt, is_second_slot=True)
            nt.links.new(bsdf_1.outputs[0], slot_mix_shader.inputs[1])
            nt.links.new(bsdf_2.outputs[0], slot_mix_shader.inputs[2])
        elif mtd_info.alpha:
            # Single-texture shader (one slot). We mix with Transparent BSDF to render vertex alpha.
            # TODO: Could I not just multiply texture alpha and vertex alpha?
            transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
            transparent.location = (-200, 230)
            nt.links.new(transparent.outputs[0], slot_mix_shader.inputs[1])
            if bsdf_1:
                nt.links.new(bsdf_1.outputs[0], slot_mix_shader.inputs[2])
        # TODO: Not sure if I can easily support 'edge' shader alpha.
        else:
            # Single texture, no alpha. Wait to see if lightmap used below.
            pass

        return bl_material

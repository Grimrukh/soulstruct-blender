from __future__ import annotations

__all__ = [
    "BlenderFLVERMaterial",
]

import typing as tp
from pathlib import Path

import bpy

from io_soulstruct.exceptions import MaterialImportError, FLVERExportError
from io_soulstruct.utilities import LoggingOperator, get_bl_custom_prop
from soulstruct.base.models.flver.material import Material, Texture, GXItem
from soulstruct.base.models.flver.submesh import Submesh
from soulstruct.base.models.flver.mesh_tools import SplitSubmeshDef
from .core import NodeTreeBuilder

if tp.TYPE_CHECKING:
    from soulstruct.base.models.shaders import MatDef
    from .properties import FLVERGXItemProps


class BlenderFLVERMaterial:
    """Note that these can wrap ANY Blender material. No type property is checked."""

    material: bpy.types.Material

    def __init__(self, material: bpy.types.Material):
        self.material = material

    @property
    def type_properties(self):
        return self.material.FLVER_MATERIAL

    @property
    def name(self) -> str:
        return self.material.name

    @name.setter
    def name(self, value: str):
        self.material.name = value

    @property
    def tight_name(self):
        """Removes everything after first '[' bracket and strips spaces."""
        return self.material.name.split("[")[0].rstrip()

    @property
    def node_tree(self):
        return self.material.node_tree

    flags: int
    mat_def_path: str
    unk_x18: int
    is_bind_pose: bool
    default_bone_index: int
    face_set_count: int

    # Convenience for reducing long sampler names; not a real FLVER Material property.
    sampler_prefix: str

    @property
    def use_backface_culling(self) -> bool:
        return self.material.use_backface_culling

    @use_backface_culling.setter
    def use_backface_culling(self, value: bool):
        self.material.use_backface_culling = value

    @property
    def gx_items(self) -> list[GXItem]:
        return [
            gx_item_props.to_gx_item()
            for gx_item_props in self.type_properties.gx_items
        ]

    @gx_items.setter
    def gx_items(self, value: list[GXItem]):
        self.type_properties.gx_items.clear()
        for gx_item in value:
            gx_item_prop = self.type_properties.gx_items.add()  # type: FLVERGXItemProps
            gx_item_prop.from_gx_item(gx_item)

    def __getattr__(self, item):
        if item in self.type_properties.__annotations__:
            return getattr(self.type_properties, item)
        raise AttributeError(f"'{self.TYPE}' object has no attribute '{item}'.")

    def __setattr__(self, key, value):
        if key in self.type_properties.__annotations__:
            setattr(self.type_properties, key, value)
        else:
            super().__setattr__(key, value)

    @classmethod
    def from_all_mesh_materials(cls, mesh: bpy.types.MeshObject) -> list[tp.Self]:
        return [cls(mat) for mat in mesh.data.materials]

    @classmethod
    def new_from_flver_material(
        cls,
        operator: LoggingOperator,
        flver_material: Material,
        flver_sampler_texture_stems: dict[str, str],
        material_name: str,
        matdef: MatDef | None,
        submesh: Submesh,
        vertex_color_count: int,
        blend_mode="HASHED",
        warn_missing_textures=True,
    ) -> BlenderFLVERMaterial:
        """Create a new Blender material from a FLVER material.

        Will use material texture stems to search for PNG or DDS images in the Blender image data. If no image is found,
        the texture will be left unassigned in the material.

        Attempts to build a Blender node tree for the material. The only critical information stored in the node tree is the
        sampler names (node labels) and image names (image node `Image` names) of the `ShaderNodeTexImage` nodes created.
        We attempt to connect those textures to UV maps and BSDF nodes, but this is just an attempt to replicate the game
        engine's shaders, and is not needed for FLVER export. (NOTE: Elden Ring tends to store texture paths in MATBIN files
        rather than in the FLVER materials, so even the texture names may not be used on export.)
        """

        bl_material = bpy.data.materials.new(name=material_name)
        bl_material.use_nodes = True
        if blend_mode:
            if matdef and matdef.edge:
                # Always uses "CLIP".
                bl_material.blend_method = "CLIP"
                bl_material.alpha_threshold = 0.5
            else:
                bl_material.blend_method = blend_mode

        material = cls(bl_material)
        # Real Material properties:
        material.flags = flver_material.flags  # int
        material.mat_def_path = flver_material.mat_def_path  # str
        material.unk_x18 = flver_material.unk_x18  # int
        # NOTE: Texture path prefixes not stored, as they aren't actually needed in the TPFBHDs.
        # Submesh properties:
        material.is_bind_pose = submesh.is_bind_pose
        # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
        material.default_bone_index = submesh.default_bone_index
        # TODO: Currently, main face set is simply copied to all additional face sets on export. This is fine for early
        #  games, but probably not for, say, Elden Ring map pieces. Some kind of auto-decimator may be in order.
        material.face_set_count = len(submesh.face_sets)
        material.use_backface_culling = submesh.use_backface_culling
        material.gx_items = flver_material.gx_items

        if not matdef:
            # Store FLVER sampler texture paths directly in custom properties. No shader tree will be built, but at least
            # we can faithfully write FLVER texture paths back to files on export.
            # TODO: Show in FLVER Material panel.
            for sampler_name, texture_stem in flver_sampler_texture_stems.items():
                bl_material[f"Path[{sampler_name}]"] = texture_stem
            return material

        # Retrieve any texture paths given from the MATBIN.
        sampler_texture_stems = {sampler.name: sampler.matbin_texture_stem for sampler in matdef.samplers}

        # Apply FLVER overrides to texture paths.
        found_sampler_names = set()
        for sampler_name, texture_stem in flver_sampler_texture_stems.items():

            if sampler_name in found_sampler_names:
                operator.warning(
                    f"Texture for sampler '{sampler_name}' was given multiple times in FLVER material, which is "
                    f"invalid. Please repair this corrupt FLVER file. Ignoring this duplicate texture instance.",
                )
                continue
            found_sampler_names.add(sampler_name)

            if sampler_name not in sampler_texture_stems:
                # Unexpected sampler name!
                if warn_missing_textures:
                    operator.warning(
                        f"Sampler '{sampler_name}' given in FLVER does not seem to be supported by material definition "
                        f"'{matdef.name}' with shader '{matdef.shader_stem}'. Texture node will be created, but with no UV "
                        f"layer input.",
                    )
                sampler_texture_stems[sampler_name] = texture_stem
                continue

            if not texture_stem:
                # No override given in FLVER. Rare in games that use MTD, but still happens, and very common in later
                # MATBIN games with super-flexible billion-sampler shaders.
                continue

            # Override texture path.
            sampler_texture_stems[sampler_name] = texture_stem

        # Try to build shader nodetree.
        try:
            builder = NodeTreeBuilder(
                operator=operator,
                material=bl_material,
                matdef=matdef,
                sampler_texture_stems=sampler_texture_stems,
                vertex_color_count=vertex_color_count,
            )
            builder.build()
        except (MaterialImportError, KeyError, ValueError, IndexError) as ex:
            operator.warning(
                f"Error building shader for material '{material_name}'. Textures written to custom properties. Error:\n"
                f"    {ex}"
            )
            for sampler_name, texture_stem in flver_sampler_texture_stems.items():
                bl_material[f"Path[{sampler_name}]"] = texture_stem
            return material

        return material

    def to_flver_material(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        matdef: MatDef,
        collected_texture_images: dict[str, bpy.types.Image] = None,
    ) -> Material:
        """Create a FLVER material from Blender material custom properties and texture nodes.

        Texture paths are collected using the provided `MatDef` samplers. For each sampler, if 'Path[sampler.name]' is
        given (even if empty), that is used as the texture path. Otherwise, the texture node named after the alias
        (preferred) or game-specific name for that sampler is searched for, and the name of the Blender Image assigned
        to that node is used as the texture path, even if the Blender Image is a placeholder pixel.

        If a 'Sampler Prefix' custom property is given on the Blender material, it is used to prefix all sampler names.
        This allows node names to be shorted on import, especially for newer games with the full shader name baked into
        every sampler name. (Note that this only matters if the texture node is NOT already an alias, which is mapped
        to the game-specific sampler name using the `MatDef`.)

        If a sampler defines a non-empty `matbin_texture_path`, and that texture's STEM matches the stem of a found
        Blender texture, the FLVER texture is left EMPTY. In this case, the MATBIN already uses that texture; it was
        imported for FLVER viewing convenience, but does not need to be written to the FLVER as a texture path override.
        If the FLVER texture is different, it is written to the FLVER as an override. (Note that older games' MTD-based
        `MatDef`s never have this issue, as they do not provide a `matbin_texture_path`.)

        If an unrecognized sampler name/alias is found on an Image Texture node or as a 'Path[sampler.name]' property,
        the user is warned and that sampler/texture will be ignored, UNLESS `allow_unknown_texture_types` is enabled in
        FLVER export settings. In that case, the texture will be exported to the FLVER material as that texture type
        directly -- but unless you are a wizard who has modified shaders and MTDs/MATBINs, I cannot imagine a use case
        for this.

        If an expected `MatDef` sampler name/alias is MISSING from both 'Path[sampler.name]' properties and texture
        node names, a `FLVERExportError` will be raised, except in the following cases:
            - If `allow_missing_textures` is enabled, ANY sampler name can be missing.
            - If `MatDef.matbin` is given (newer games) and that MATBIN also does not specify a texture path for that
            sampler, we assume that this material/shader does not require that texture.
            - If `MatDef.matbin` is NOT given and the sampler name is 'Detail 0 Normal', it is allowed to be missing,
            because this is clearly an optional and frequently omitted sampler in many shaders in older games.
        In all of these cases, an empty texture path will be written for that texture in the FLVER material. Empty
        texture paths are always permitted if the sampler name is found. Note that the FLVER material importer will
        always create empty Image Texture nodes or empty string properties for samplers with no texture path.
        """
        collected_texture_images = collected_texture_images or {}
        name = self.tight_name

        export_settings = context.scene.flver_export_settings

        flver_material = Material(
            name=name,
            flags=self.flags,
            mat_def_path=self.mat_def_path,
            unk_x18=self.unk_x18,
            gx_items=self.gx_items,  # list-creating property
        )

        # FLVER material texture path extension doesn't actually matter, but we try to be faithful.
        settings = operator.settings(context)
        path_ext = ".tif" if settings.is_game("ELDEN_RING") else ".tga"  # TODO: also TIF in Sekiro?

        if matdef.matbin:
            # Any sampler that does NOT have a path given in MATBIN is allowed to be missing (lack of MATBIN path
            # implies to us that this MATBIN does not use this sampler in the shader).
            allowed_missing_sampler_names = {
                sampler.name for sampler in matdef.samplers if not sampler.matbin_texture_path
            }
        else:
            # Manual specification: 'Detail 0 Normal' is allowed to be missing.
            # TODO: Only for certain older games like DS1R?
            allowed_missing_sampler_names = {"Detail 0 Normal"}

        texture_nodes = {
            node.name: node
            for node in self.node_tree.nodes
            if node.type == "TEX_IMAGE"
        }

        for sampler in matdef.samplers:

            texture_stem = ""
            sampler_name = sampler.name.removeprefix(self.sampler_prefix)
            sampler_found = False

            # Check custom property.
            path_prop = f"Path[{sampler_name}]"
            if path_prop in self.material:
                prop_texture_path = get_bl_custom_prop(self.material, path_prop, str)  # to assert `str` type
                texture_stem = Path(prop_texture_path).stem
                sampler_found = True
            else:
                # Check node named with sampler alias or game-specific name (sans any 'Sampler Prefix').
                for key in (sampler.alias, sampler_name):
                    if key in texture_nodes:
                        node_image = texture_nodes.pop(key).image  # consumes node
                        if node_image:
                            texture_stem = Path(node_image.name).stem
                            collected_texture_images[texture_stem] = node_image
                        sampler_found = True

            if texture_stem and texture_stem == sampler.matbin_texture_stem:
                # Texture path in shader is the same as the MATBIN texture path -- that is, it was imported for
                # FLVER visualization using the MATBIN but does NOT need to be written to the FLVER as an override.
                texture_stem = ""
            elif not sampler_found:
                # Could not find a property or node for sampler.
                if export_settings.allow_missing_textures:
                    pass  # always ignored
                elif sampler.name in allowed_missing_sampler_names:  # full sampler name!
                    pass  # permitted case
                else:
                    raise FLVERExportError(
                        f"Could not find a texture path for sampler '{sampler.name}' in material '{self.name}'. "
                        f"You must create a 'Path[{sampler_name}]' for it (even if empty), or create an Image Texture "
                        f"node for it with a , or "
                        f"enable 'Allow Missing Textures' in FLVER export options."
                    )

            flver_material.textures.append(
                Texture(
                    path=(texture_stem + path_ext) if texture_stem else "",
                    texture_type=sampler_name,
                )
            )

        for node_name, node in texture_nodes.items():
            # Some texture nodes were not used, as they do not match sampler names/aliases.
            if not export_settings.allow_unknown_texture_types:
                operator.warning(
                    f"Unknown sampler type (node name) in material '{self.name}': {node_name}. You can enable "
                    f"'Allow Unknown Texture Types' in FLVER export settings to forcibly export it to the FLVER "
                    f"material as this texture type. This would be unusual, though!"
                )
            else:
                operator.warning(
                    f"Unknown texture type (node name) in material '{self.name}': {node_name}. Exporting "
                    f"to the FLVER material as this texture type."
                )
                texture_stem = Path(node.image.name).stem
                flver_material.textures.append(
                    Texture(
                        path=(texture_stem + path_ext) if node.image else "",
                        texture_type=node_name,
                    )
                )

        return flver_material

    def to_split_submesh_def(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        create_lod_face_sets: bool,
        matdef: MatDef,
        use_chr_layout: bool,
        collected_texture_images: dict[str, bpy.types.Image] = None,
    ) -> SplitSubmeshDef:
        """Use given `matdef` to create a `SplitSubmeshDef` for the given Blender material with either a character
        layout or a map piece layout, depending on `use_chr_layout`."""

        # Some Blender materials may be variants representing distinct Submesh/FaceSet properties; these will be
        # mapped to the same FLVER `Material`/`VertexArrayLayout` combo (created here).
        flver_material = self.to_flver_material(operator, context, matdef, collected_texture_images)
        if use_chr_layout:
            array_layout = matdef.get_character_layout()
        else:
            array_layout = matdef.get_map_piece_layout()

        # We only respect 'Face Set Count' if requested in export options. (Duplicating the main face set is only
        # viable in older games with low-res meshes, but those same games don't even really need LODs anyway.)
        face_set_count = self.face_set_count if create_lod_face_sets else 1
        submesh_kwargs = {
            "is_bind_pose": self.is_bind_pose,
            "default_bone_index": self.default_bone_index,
            "use_backface_culling": self.use_backface_culling,
            "uses_bounding_box": True,  # TODO: assumption (DS1 and likely all later games)
            "face_set_count": face_set_count,
        }
        used_uv_layer_names = [layer.name for layer in matdef.get_used_uv_layers()]
        operator.info(f"Created FLVER material: {flver_material.name} with UV layers: {used_uv_layer_names}")

        return SplitSubmeshDef(
            flver_material,
            array_layout,
            submesh_kwargs,
            used_uv_layer_names,
        )

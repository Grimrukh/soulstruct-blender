from __future__ import annotations

__all__ = [
    "BlenderFLVERMaterial",
]

import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.models.flver import *

from io_soulstruct.exceptions import MaterialImportError, FLVERExportError
from io_soulstruct.utilities import LoggingOperator, get_bl_custom_prop
from io_soulstruct.flver.image import DDSTexture, DDSTextureCollection
from .shaders import NodeTreeBuilder

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
    def tight_name(self) -> str:
        """Removes everything after first '[' bracket and/or first '<' bracket, and strips spaces."""
        return self.material.name.split("[")[0].split("<")[0].strip()

    @property
    def node_tree(self):
        return self.material.node_tree

    AUTO_MATERIAL_PROPS = [
        "flags",
        "mat_def_path",
        "f2_unk_x18",
        "is_bind_pose",
        "default_bone_index",
        "face_set_count",
        "sampler_prefix",
    ]

    is_bind_pose: bool
    mat_def_path: str
    default_bone_index: int
    face_set_count: int

    # FLVER2 only:
    flags: int
    f2_unk_x18: int

    # No FLVER0-only properties.

    sampler_prefix: str  # for sampler truncation; not a real imported/exported FLVER Material property

    @property
    def use_backface_culling(self) -> bool:
        return self.material.use_backface_culling

    @use_backface_culling.setter
    def use_backface_culling(self, value: bool):
        self.material.use_backface_culling = value

    @property
    def gx_items(self) -> list[GXItem]:
        """Ignores items with empty category. Final dummy item appended automatically."""
        return [
            gx_item_props.to_gx_item()
            for gx_item_props in self.type_properties.gx_items
            if len(gx_item_props.category) == 4
        ] + [GXItem.new_terminator()]  # TODO: are these dummy values suitable for all games/FLVERs?

    @gx_items.setter
    def gx_items(self, value: list[GXItem]):
        self.type_properties.gx_items.clear()
        for gx_item in value:
            if gx_item.is_terminator:
                continue  # final dummy items not saved in Blender
            gx_item_prop = self.type_properties.gx_items.add()  # type: FLVERGXItemProps
            gx_item_prop.from_gx_item(gx_item)

    @classmethod
    def from_all_mesh_materials(cls, mesh: bpy.types.MeshObject) -> list[tp.Self]:
        return [cls(mat) for mat in mesh.data.materials]

    @classmethod
    def new_from_flver_material(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        flver_material: Material,
        flver_sampler_texture_stems: dict[str, str],
        material_name: str,
        matdef: MatDef | None,
        mesh: FLVERMesh,
        vertex_color_count: int,
        blend_mode="HASHED",
        warn_missing_textures=True,
        bl_materials_by_matdef_name: dict[str, bpy.types.Material] = None,
    ) -> BlenderFLVERMaterial:
        """Create a new Blender material from a FLVER material.

        Will use material texture stems to search for images of all supported formats in the Blender image data. If no
        image is found, the texture will be left unassigned in the material.

        Attempts to build a Blender node tree for the material. The only critical information stored in the node tree is
        the sampler names (node labels) and image names (image node `Image` names) of the `ShaderNodeTexImage` nodes
        created. We attempt to connect those textures to UV maps and BSDF nodes, but this is just an attempt to
        replicate the game engine's shaders, and is not needed for FLVER export. (NOTE: Elden Ring tends to store
        texture paths in MATBIN files rather than in the FLVER materials, so even the texture names may not be used on
        export.)

        If `bl_materials_by_matdef_name` is given, new Materials will be copied from existing Materials with the same
        MATDEF name, and only the textures updated. This is more efficient than creating identical shader node trees
        over and over for multiple materials.
        """
        if bl_materials_by_matdef_name is not None and flver_material.mat_def_name in bl_materials_by_matdef_name:
            copied = True
            bl_material = bl_materials_by_matdef_name[flver_material.mat_def_name].copy()
            bl_material.name = material_name
            # `use_nodes` already set up, and blend settings will match same MatDef.
        else:
            copied = False
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
        material.default_bone_index = mesh.default_bone_index

        material.mat_def_path = flver_material.mat_def_path  # str
        if isinstance(flver_material, Material):
            material.flags = flver_material.flags  # int
            material.f2_unk_x18 = flver_material.f2_unk_x18  # int
            material.gx_items = flver_material.get_non_terminator_gx_items()  # final dummy `GXItem` not held in Blender
            # TODO: Currently, main face set is simply copied to all additional face sets on export. This is fine for
            #  early games, but probably not for, say, Elden Ring map pieces. Some kind of auto-decimator is in order.
            material.face_set_count = len(mesh.face_sets)

        # Mesh properties:
        material.use_backface_culling = mesh.use_backface_culling  # wraps `face_set[0].use_backface_culling`
        material.is_bind_pose = mesh.is_bind_pose

        # NOTE: Texture path prefixes not stored, as they aren't actually needed in the TPFBHDs.
        # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).

        if not matdef:
            # Store FLVER sampler texture paths directly in custom properties. No shader tree will be built, but
            # at least we can faithfully write FLVER texture paths back to files on export.
            for sampler_name, texture_stem in flver_sampler_texture_stems.items():
                bl_material[f"Path[{sampler_name}]"] = texture_stem
            return material

        # Retrieve any texture paths given by a MATBIN, if present. All lower-case.
        sampler_texture_stems = {sampler.name: sampler.matbin_texture_stem.lower() for sampler in matdef.samplers}

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
                        f"'{matdef.name}' with shader '{matdef.shader_stem}'. Texture node will be created, but with "
                        f"no UV layer input.",
                    )
                sampler_texture_stems[sampler_name] = texture_stem.lower()
                continue

            if not texture_stem:
                # No override given in FLVER. Rare in games that use MTD, but still happens, and very common in later
                # MATBIN games with super-flexible billion-sampler shaders.
                continue

            # Override texture path.
            sampler_texture_stems[sampler_name] = texture_stem.lower()

        if not copied:
            # Try to build shader nodetree.
            try:
                builder = NodeTreeBuilder(
                    operator=operator,
                    context=context,
                    material=bl_material,
                    matdef=matdef,
                    sampler_texture_stems=sampler_texture_stems,
                    vertex_color_count=vertex_color_count,
                )
                builder.build()
            except (MaterialImportError, KeyError, ValueError, IndexError) as ex:
                operator.warning(
                    f"Error building shader for material '{material_name}'. Textures written to custom properties. "
                    f"Error:\n  {ex}"
                )
                for sampler_name, texture_stem in flver_sampler_texture_stems.items():
                    bl_material[f"Path[{sampler_name}]"] = texture_stem

            if bl_materials_by_matdef_name is not None:
                # Record material for MatDef for future copying.
                bl_materials_by_matdef_name[flver_material.mat_def_name] = bl_material
        else:
            # Just replace appropriate texture nodes.
            tex_nodes_by_name = {
                node.name: node
                for node in material.get_image_texture_nodes()
            }
            for sampler_name, texture_stem in sampler_texture_stems.items():
                if sampler_name in tex_nodes_by_name:
                    if not texture_stem:
                        # No texture given in MATBIN or FLVER.
                        tex_nodes_by_name[sampler_name].image = None
                        continue

                    # TODO: NodeTreeBuilder has identical method.
                    # Search for Blender image with no extension, TGA, PNG, or DDS, in that order of preference.
                    for image_name in (
                        f"{texture_stem}", f"{texture_stem}.tga", f"{texture_stem}.png", f"{texture_stem}.dds"
                    ):
                        try:
                            bl_image = bpy.data.images[image_name]
                            break
                        except KeyError:
                            pass
                    else:
                        # Blender image not found. Create empty 1x1 Blender image.
                        bl_image = bpy.data.images.new(name=texture_stem, width=1, height=1, alpha=True)
                        bl_image.pixels = [1.0, 0.0, 1.0, 1.0]  # magenta
                        if context.scene.flver_import_settings.import_textures:  # otherwise, expected to be missing
                            operator.warning(
                                f"Could not find texture '{texture_stem}' in Blender image data. "
                                f"Created 1x1 magenta Image."
                            )

                    tex_nodes_by_name[sampler_name].image = bl_image

        return material

    def to_flver_material(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        matdef: MatDef,
        texture_collection: DDSTextureCollection = None,
        get_texture_path_prefix: tp.Callable[[str], str] | None = None,
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

        If `path_prefix` is given, it will be prepended to the texture paths (e.g. in Demon's Souls).
        """
        if texture_collection is None:
            texture_collection = DDSTextureCollection()
        name = self.tight_name

        export_settings = context.scene.flver_export_settings

        flver_material = Material(
            name=name,
            mat_def_path=self.mat_def_path,
            flags=self.flags,
            f2_unk_x18=self.f2_unk_x18,
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

        # noinspection PyTypeChecker
        texture_nodes = {
            node.name: node
            for node in self.node_tree.nodes
            if node.type == "TEX_IMAGE"
        }  # type: dict[str, bpy.types.ShaderNodeTexImage]

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
                        texture_node = texture_nodes.pop(key)  # type: bpy.types.ShaderNodeTexImage
                        node_image = texture_node.image  # type: bpy.types.Image | None  # consumes node
                        if node_image:
                            texture_stem = Path(node_image.name).stem
                            if len(node_image.pixels) > 4:
                                texture_collection.add(DDSTexture(node_image))
                        sampler_found = True
                        break  # don't check the other key

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

            if get_texture_path_prefix:
                path_prefix = get_texture_path_prefix(texture_stem)
            else:
                path_prefix = ""

            texture_path = (path_prefix + texture_stem + path_ext) if texture_stem else ""
            # TODO: Unknowns currently all ignored.
            texture = Texture(path=texture_path, texture_type=sampler_name)

            flver_material.textures.append(texture)

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
                texture_path = (texture_stem + path_ext) if node.image else ""
                # TODO: Unknowns currently all ignored.
                texture = Texture(path=texture_path, texture_type=node_name)

                flver_material.textures.append(texture)

        return flver_material

    def to_split_mesh_def(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        create_lod_face_sets: bool,
        matdef: MatDef,
        use_map_piece_layout: bool,
        texture_collection: DDSTextureCollection = None,
        get_texture_path_prefix: tp.Callable[[str], str] | None = None,
    ) -> SplitMeshDef:
        """Use given `matdef` to create a `SplitMeshDef` for the given Blender material with either a character
        layout or a map piece layout, depending on `use_chr_layout`."""

        # Some Blender materials may be variants representing distinct Mesh/FaceSet properties; these will be
        # mapped to the same FLVER `Material`/`VertexArrayLayout` combo (created here).
        flver_material = self.to_flver_material(operator, context, matdef, texture_collection, get_texture_path_prefix)
        if use_map_piece_layout:
            array_layout = matdef.get_map_piece_layout()
        else:
            array_layout = matdef.get_non_map_piece_layout()

        # We only respect 'Face Set Count' if requested in export options. (Duplicating the main face set is only
        # viable in older games with low-res meshes, but those same games don't even really need LODs anyway.)
        face_set_count = self.face_set_count if create_lod_face_sets else 1
        mesh_kwargs = {
            "is_bind_pose": self.is_bind_pose,
            "default_bone_index": self.default_bone_index,
            "use_backface_culling": self.use_backface_culling,
            "face_set_count": face_set_count,
            "f0_unk_x46": 0,  # TODO: not sure what this is yet and haven't seen non-zero
            "uses_bounding_boxes": True,  # enabled even for FLVER0 versions
        }

        used_uv_layer_names = [layer.name for layer in matdef.get_used_uv_layers()]
        operator.debug(f"Created FLVER material '{flver_material.name}' with UV layers: {used_uv_layer_names}")

        return SplitMeshDef(
            flver_material,
            array_layout,
            is_bind_pose=self.is_bind_pose,
            kwargs=mesh_kwargs,
            uv_layer_names=used_uv_layer_names,
        )

    def get_image_texture_nodes(self, with_image_only=False) -> list[bpy.types.ShaderNodeTexImage]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        return [
            node for node in self.node_tree.nodes
            if node.type == "TEX_IMAGE" and (not with_image_only or node.image is not None)
        ]

    def get_texture_name_dict(self) -> dict[str, str]:
        """Get a dictionary mapping texture node names (game-specific samplers) to the textures they use.

        If no Image is set to a node, the value will be an empty string.
        """
        return {
            node.name: node.image.name if node.image else ""
            for node in self.get_image_texture_nodes(with_image_only=False)
        }

    def get_hash(self, include_face_set_count=True, is_flver0=False) :
        """Hash based on all FLVER material properties, with `face_set_count` optional (used by default)."""
        hashed = [self.is_bind_pose, self.mat_def_path, self.default_bone_index]
        if not is_flver0:
            hashed.extend([self.flags, self.f2_unk_x18])
        if include_face_set_count:
            hashed.append(self.face_set_count)

        texture_name_dict = self.get_texture_name_dict()
        for sampler_name in sorted(texture_name_dict.keys()):
            texture_name = self.sampler_prefix + texture_name_dict[sampler_name]
            hashed.append((sampler_name, texture_name))

        return hash(tuple(hashed))

    @classmethod
    def add_auto_type_props(cls, *names):
        for prop_name in names:
            setattr(
                cls, prop_name, property(
                    lambda self, pn=prop_name: getattr(self.type_properties, pn),
                    lambda self, value, pn=prop_name: setattr(self.type_properties, pn, value),
                )
            )


BlenderFLVERMaterial.add_auto_type_props(*BlenderFLVERMaterial.AUTO_MATERIAL_PROPS)

from __future__ import annotations

__all__ = [
    "CreatedFLVERMaterials",
    "create_materials",
]

import time
import typing as tp

import bpy

from soulstruct.base.models.flver import *
from soulstruct.base.models.shaders import MatDef, MatDefError
from soulstruct.containers.tpf import TPFTexture

from io_soulstruct.exceptions import *
from io_soulstruct.flver.image.import_operators import *
from io_soulstruct.flver.image.types import DDSTexture, DDSTextureCollection
from io_soulstruct.flver.material.types import BlenderFLVERMaterial
from io_soulstruct.general import GAME_CONFIG
from io_soulstruct.general.cached import get_cached_mtdbnd, get_cached_matbinbnd
from io_soulstruct.general.enums import BlenderImageFormat
from io_soulstruct.utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.matbin import MATBINBND
    from io_soulstruct.flver.image.image_import_manager import ImageImportManager


class CreatedFLVERMaterials(tp.NamedTuple):
    bl_materials: tuple[BlenderFLVERMaterial, ...]
    mesh_bl_material_indices: tuple[int, ...]
    bl_material_uv_layer_names: tuple[tuple[str, ...], ...]


def create_materials(
    operator: LoggingOperator,
    context: bpy.types.Context,
    flver: FLVER,
    model_name: str,
    material_blend_mode: str,
    image_import_manager: ImageImportManager | None = None,
    bl_materials_by_matdef_name: dict[str, bpy.types.Material] = None,
) -> CreatedFLVERMaterials:
    """Create Blender materials needed for `flver`.

    We need to scan the FLVER to actually parse which unique combinations of Material/Mesh properties exist.

    Returns a list of Blender material indices for each mesh, and a list of UV layer names for each Blender
    material (NOT each mesh).
    """

    # Mesh-matched list of dictionaries mapping sample/texture type to texture path (only name matters).
    settings = operator.settings(context)
    import_settings = context.scene.flver_import_settings
    mtdbnd = get_cached_mtdbnd(operator, settings) if not GAME_CONFIG[settings.game].uses_matbin else None
    matbinbnd = get_cached_matbinbnd(operator, settings) if GAME_CONFIG[settings.game].uses_matbin else None
    all_mesh_texture_stems = _get_mesh_flver_textures(flver, matbinbnd)
    bl_materials_by_matdef_name = bl_materials_by_matdef_name or {}  # still worthwhile within one FLVER

    if import_settings.import_textures:
        if image_import_manager or settings.str_image_cache_directory:
            p = time.perf_counter()
            all_texture_stems = {
                v
                for mesh_textures in all_mesh_texture_stems
                for v in mesh_textures.values()
                if v  # obviously ignore empty texture paths
            }
            texture_collection = _load_texture_images(
                operator, context, model_name, all_texture_stems, image_import_manager
            )
            if texture_collection:
                operator.debug(f"Loaded {len(texture_collection)} textures in {time.perf_counter() - p:.3f} s.")
        else:
            operator.info("No imported textures or PNG cache folder given. No textures loaded for FLVER.")

    # Maps FLVER meshes to their Blender material index to store per-face in the merged mesh.
    # Meshes that originally indexed the same FLVER material may have different Blender 'variant' materials that
    # hold certain Mesh/FaceSet properties like `use_backface_culling`.
    # Conversely, Meshes that only serve to handle per-mesh bone maximums (e.g. 38 in DS1) will use the same
    # Blender material and be split again automatically on export (but likely not in an indentical way!).
    mesh_bl_material_indices = []
    # UV layer names used by each Blender material index (NOT each FLVER mesh).
    bl_material_uv_layer_names = []  # type: list[tuple[str, ...]]

    # Map FLVER material hashes to the indices of variant Blender materials sourced from them, which hold distinct
    # Mesh/FaceSet properties.
    flver_material_hash_variants = {}

    # Map FLVER material hashes to their generated `MatDef` instances.
    flver_matdefs = {}  # type: dict[int, MatDef | None]
    for mesh in flver.meshes:
        material_hash = hash(mesh.material)  # TODO: should hash ignore material name?
        if material_hash in flver_matdefs:
            continue  # material already created (used by a previous mesh)

        # Try to look up material info from MTD or MATBIN (Elden Ring).
        try:
            matdef_class = settings.get_game_matdef_class()
        except UnsupportedGameError:
            operator.warning(f"FLVER material shader creation not implemented for game {settings.game.name}.")
            matdef = None
        except MatDefError as ex:
            operator.warning(
                f"Could not create `MatDef` for game material '{mesh.material.mat_def_name}'. Error:\n"
                f"    {ex}"
            )
            matdef = None
        else:
            if GAME_CONFIG[settings.game].uses_matbin:
                matdef = matdef_class.from_matbinbnd_or_name(mesh.material.mat_def_name, matbinbnd)
            else:
                matdef = matdef_class.from_mtdbnd_or_name(mesh.material.mat_def_name, mtdbnd)

        flver_matdefs[material_hash] = matdef

    new_materials = []

    for mesh, mesh_textures in zip(flver.meshes, all_mesh_texture_stems, strict=True):
        material = mesh.material
        material_hash = hash(material)  # NOTE: if there are duplicate FLVER materials, this will combine them
        vertex_color_count = len([f for f in mesh.vertices.dtype.names if "color" in f])

        if material_hash not in flver_material_hash_variants:
            # First time this FLVER material has been encountered. Create it in Blender now.
            # NOTE: Vanilla material names are unused and essentially worthless. They can also be the same for
            #  materials that actually use different lightmaps, EVEN INSIDE the same FLVER model. Names are changed
            #  here to just reflect the index. The original name is NOT kept to avoid stacking up formatting on
            #  export/import and because it is so useless anyway.
            flver_material_index = len(flver_material_hash_variants)
            bl_material_index = len(new_materials)
            matdef = flver_matdefs[material_hash]

            # Create a relatively informative material name. We use material index, mat def, and model name as a
            # suffix to maximize the chances of a unique Blender name.
            bl_material_name = (
                f"{material.name} [{flver_material_index} | {material.mat_def_stem} | {model_name}]"
            )

            bl_material = BlenderFLVERMaterial.new_from_flver_material(
                operator,
                context,
                material,
                flver_sampler_texture_stems=mesh_textures,
                material_name=bl_material_name,
                matdef=matdef,
                mesh=mesh,
                vertex_color_count=vertex_color_count,
                blend_mode=material_blend_mode,
                warn_missing_textures=image_import_manager is not None,
                bl_materials_by_matdef_name=bl_materials_by_matdef_name,
            )

            mesh_bl_material_indices.append(bl_material_index)
            flver_material_hash_variants[material_hash] = [bl_material_index]

            new_materials.append(bl_material)
            if matdef:
                used_uv_layers = matdef.get_used_uv_layers()
                bl_material_uv_layer_names.append(tuple(layer.name for layer in used_uv_layers))
            else:
                # UV layer names not known for this material. `MergedMesh` will just use index, which may cause
                # conflicting types of UV data to occupy the same Blender UV slot.
                bl_material_uv_layer_names.append(())
            continue

        existing_variant_bl_indices = flver_material_hash_variants[material_hash]

        # Check if Blender material needs to be duplicated as a variant with different Mesh properties.
        found_existing_material = False
        for existing_bl_material_index in existing_variant_bl_indices:
            # NOTE: We do not care about enforcing any maximum mesh local bone count in Blender! The FLVER
            # exporter will create additional split meshes as necessary for that.
            existing_bl_material = new_materials[existing_bl_material_index]
            if (
                existing_bl_material.is_bind_pose == mesh.is_bind_pose
                and existing_bl_material.default_bone_index == mesh.default_bone_index
                and existing_bl_material.face_set_count == len(mesh.face_sets)
                and existing_bl_material.use_backface_culling == mesh.use_backface_culling
            ):
                # Blender material already exists with the same Mesh properties. No new variant neeed.
                mesh_bl_material_indices.append(existing_bl_material_index)
                found_existing_material = True
                break

        if found_existing_material:
            continue

        # No match found. New Blender material variant is needed to hold unique mesh data.
        # Since the most common cause of a variant is backface culling being enabled vs. disabled, that difference
        # gets its own prefix: we add ' <BC>' to the end of whichever variant has backface culling enabled.
        variant_index = len(existing_variant_bl_indices)
        first_material = new_materials[existing_variant_bl_indices[0]]
        variant_name = first_material.name + f" <V{variant_index}>"  # may be replaced below

        if (
            first_material.is_bind_pose == mesh.is_bind_pose
            and first_material.default_bone_index == mesh.default_bone_index
            and first_material.face_set_count == len(mesh.face_sets)
            and first_material.use_backface_culling != mesh.use_backface_culling
        ):
            # Only difference is backface culling. We mark 'BC' on the one that has it enabled.
            if first_material.use_backface_culling:
                variant_name = first_material.name  # swap with first material's name (no BC)
                first_material.name += f" <V{variant_index}, BC>"
            else:
                variant_name = first_material.name + f" <V{variant_index}, BC>"  # instead of just variant index

        bl_material = BlenderFLVERMaterial.new_from_flver_material(
            operator,
            context,
            material,
            mesh_textures,
            material_name=variant_name,
            matdef=flver_matdefs[material_hash],
            mesh=mesh,
            vertex_color_count=vertex_color_count,
            blend_mode=material_blend_mode,
            bl_materials_by_matdef_name=bl_materials_by_matdef_name,
        )

        new_bl_material_index = len(new_materials)
        mesh_bl_material_indices.append(new_bl_material_index)
        flver_material_hash_variants[material_hash].append(new_bl_material_index)
        new_materials.append(bl_material)
        if flver_matdefs[material_hash] is not None:
            bl_material_uv_layer_names.append(
                tuple(layer.name for layer in flver_matdefs[material_hash].get_used_uv_layers())
            )
        else:
            bl_material_uv_layer_names.append(())

    return CreatedFLVERMaterials(
        tuple(new_materials), tuple(mesh_bl_material_indices), tuple(bl_material_uv_layer_names)
    )


def _get_mesh_flver_textures(
    flver: FLVER,
    matbinbnd: MATBINBND | None,
) -> list[dict[str, str]]:
    """For each mesh, get a dictionary mapping sampler names (e.g. 'g_Diffuse') to texture path names (e.g.
    'c2000_fur'). The texture path names are always lower-case.

    These paths may come from the FLVER material (older games) or MATBIN (newer games). In the latter case, FLVER
    material paths are usually empty, but will be accepted as overrides if given.
    """
    all_mesh_texture_names = []
    for mesh in flver.meshes:
        mesh_texture_stems = {}
        if matbinbnd:
            try:
                matbin = matbinbnd.get_matbin(mesh.material.mat_def_name)
            except KeyError:
                pass  # missing
            else:
                mesh_texture_stems |= matbin.get_all_sampler_stems(lower=True)
        for texture in mesh.material.textures:
            if texture.path:
                # FLVER texture path can also override MATBIN path.
                mesh_texture_stems[texture.texture_type] = texture.stem.lower()
        all_mesh_texture_names.append(mesh_texture_stems)

    return all_mesh_texture_names


def _load_texture_images(
    operator: LoggingOperator,
    context: bpy.types.Context,
    name: str,
    texture_stems: set[str],
    image_import_manager: ImageImportManager | None = None,
) -> DDSTextureCollection:
    """Load texture images from PNG cache directory or TPFs found with `image_import_manager`.

    Will NEVER load an image that is already in Blender's data, regardless of image type (identified by stem only).
    Note that these stems ARE case-sensitive, as I don't want them to change when a FLVER is imported and exported
    without any other modifications. (The cached images are also case-sensitive.)
    """
    settings = operator.settings(context)

    # TODO: I was checking every Image in Blender's data to find 1x1 magenta dummy textures to replace, but that's
    #  super slow as more and more textures are loaded.
    bl_image_stems = {image_name.split(".")[0] for image_name in bpy.data.images.keys()}

    new_texture_collection = DDSTextureCollection()

    tpf_textures_to_load = {}  # type: dict[str, TPFTexture]
    for texture_stem in texture_stems:
        if texture_stem in bl_image_stems:
            continue  # already loaded
        if texture_stem in tpf_textures_to_load:
            continue  # already queued to load below

        if settings.read_cached_images and settings.str_image_cache_directory:
            cached_path = settings.get_cached_image_path(texture_stem)
            if cached_path.is_file():
                # Found cached image.
                dds_texture = DDSTexture.new_from_image_path(cached_path, settings.pack_image_data)
                new_texture_collection.add(dds_texture)
                bl_image_stems.add(texture_stem)
                continue

        if image_import_manager:
            try:
                # Searching for original texture is NOT case-sensitive.
                texture = image_import_manager.get_flver_texture(texture_stem, name)
            except KeyError as ex:
                operator.warning(f"Could not find FLVER texture '{texture_stem}'. Error: {ex}")
            else:
                tpf_textures_to_load[texture_stem] = texture
                continue

        operator.warning(f"Could not find TPF or cached image '{texture_stem}' for FLVER '{name}'.")

    if tpf_textures_to_load:
        for texture_stem in tpf_textures_to_load:
            operator.debug(f"Loading texture into Blender: {texture_stem}")
        p = time.perf_counter()
        image_format = settings.bl_image_format
        deswizzle_platform = settings.game_config.swizzle_platform
        if image_format == BlenderImageFormat.TARGA:
            all_image_data = batch_get_tpf_texture_tga_data(
                list(tpf_textures_to_load.values()), deswizzle_platform
            )
        elif image_format == BlenderImageFormat.PNG:
            all_image_data = batch_get_tpf_texture_png_data(
                list(tpf_textures_to_load.values()), deswizzle_platform, fmt="rgba"
            )
        else:
            raise ValueError(f"Unsupported image format for DDS conversion: {image_format}")

        if settings.write_cached_images:
            write_image_directory = settings.image_cache_directory  # could be None
        else:
            write_image_directory = None
        operator.debug(
            f"Converted DDS images to {image_format.value} in {time.perf_counter() - p:.3f} s "
            f"(cached = {settings.write_cached_images})"
        )
        for texture_stem, image_data in zip(tpf_textures_to_load.keys(), all_image_data):
            if image_data is None:
                continue  # failed to convert this texture
            dds_texture = DDSTexture.new_from_image_data(
                name=texture_stem,
                image_format=image_format,
                image_data=image_data,
                image_cache_directory=write_image_directory,
                replace_existing=False,  # not currently used
                pack_image_data=settings.pack_image_data,
            )
            new_texture_collection.add(dds_texture)

    return new_texture_collection

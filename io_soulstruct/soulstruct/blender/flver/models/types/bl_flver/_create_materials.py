from __future__ import annotations

__all__ = [
    "CreatedFLVERMaterials",
    "create_materials",
]

import time
import typing as tp
from pathlib import Path

import bpy

from soulstruct.flver.utilities import hash_material
from soulstruct.base.models.shaders import MatDef, MatDefError
from soulstruct.containers.tpf import TPFTexture

import pyrelink.flver as pyre_flver

from .....base.operators import *
from .....exceptions import SoulstructTypeError
from .....flver.image.enums import BlenderImageFormat
from .....flver.image.import_operators import *
from .....flver.image.types import DDSTexture, DDSTextureCollection
from .....flver.material.types import BlenderFLVERMaterial
from .....general import BLENDER_GAME_CONFIG
from .....general.matdefs import get_cached_mtdbnd, get_cached_matbinbnd
from .....utilities import *

if tp.TYPE_CHECKING:
    from soulstruct.base.models.matbin import MATBINBND
    from soulstruct.flver import FLVER
    from .....flver.image.image_import_manager import ImageImportManager


class CreatedFLVERMaterials(tp.NamedTuple):
    """Information about created FLVER materials in Blender."""
    bl_materials: tuple[BlenderFLVERMaterial, ...]
    mesh_bl_material_indices: tuple[int, ...]  # same length as `FLVER.meshes`
    bl_material_uv_layer_names: tuple[tuple[str, ...], ...]  # same length as `bl_materials`


def create_materials(
    operator: LoggingOperator,
    context: bpy.types.Context,
    flver: FLVER,
    model_name: str,
    material_blend_mode: str,
    image_import_manager: ImageImportManager | None = None,
    texture_finders: tp.Sequence[pyre_flver.TextureFinder] = (),
    bl_materials_by_matdef_name: dict[str, bpy.types.Material] = None,
) -> CreatedFLVERMaterials:
    """Create Blender materials needed for `flver`.

    We need to scan the FLVER to actually parse which unique combinations of Material/Mesh properties exist.

    Returns a list of Blender material indices for each FLVER mesh, and a list of UV layer names used by each Blender
    material (NOT per FLVER mesh).
    """

    settings = operator.settings(context)
    import_settings = context.scene.flver_import_settings
    mat_settings = context.scene.flver_material_settings

    mtdbnd = get_cached_mtdbnd(operator, context) if not BLENDER_GAME_CONFIG[settings.game_type].uses_matbin else None
    matbinbnd = get_cached_matbinbnd(operator, context) if BLENDER_GAME_CONFIG[settings.game_type].uses_matbin else None

    # Mesh-matched list of dictionaries mapping sample/texture type to texture path (only name matters).
    all_mesh_texture_stems = _get_mesh_flver_textures(flver, matbinbnd)

    bl_materials_by_matdef_name = bl_materials_by_matdef_name or {}  # still worthwhile within one FLVER

    if import_settings.import_textures:
        # We attempt texure load if ImageImportManager or TextureFinder is given, OR if an image cache directory
        # is given (which does not require either finder class).
        image_cache_dir = mat_settings.get_game_image_cache_directory(context)
        if image_import_manager or texture_finders or is_path_and_dir(image_cache_dir):
            p = time.perf_counter()
            all_texture_stems = {
                v
                for mesh_textures in all_mesh_texture_stems
                for v in mesh_textures.values()
                if v  # obviously ignore empty texture paths
            }
            texture_collection = _load_texture_images(
                operator, context, model_name, all_texture_stems, image_import_manager, texture_finders
            )
            if texture_collection:
                operator.debug(f"Loaded {len(texture_collection)} textures in {time.perf_counter() - p:.3f} s.")
        else:
            operator.info("No imported textures or PNG cache folder given. No textures loaded for FLVER.")

    # Maps FLVER meshes to their Blender material index to store per-face in the merged mesh.
    # FLVER meshes that only serve to handle per-mesh bone maximums (e.g. 38 in DS1) will use the same
    # Blender material and be split again automatically on export (but likely not in an identical way!).
    mesh_bl_material_indices = []
    # UV layer names used by each Blender material index (NOT each FLVER mesh).
    bl_material_uv_layer_names = []  # type: list[tuple[str, ...]]

    # Map (FLVER material hash, backface culling, is_dynamic) to the index of the Blender material sourced from them.
    # All three must match for a Blender material to be shared across meshes: backface culling is stored on the
    # Blender material itself, and `is_dynamic` is stored in the per-material `FLVERSubmeshProps` written by
    # `_set_submesh_props()`, so a single Blender material cannot represent both values of either property.
    flver_material_variants = {}  # type: dict[tuple[int, bool, bool], int]
    # Index assigned to each unique FLVER material hash, purely for Blender material naming.
    flver_material_hash_indices = {}  # type: dict[int, int]

    # Map FLVER material hashes to their generated `MatDef` instances.
    flver_matdefs = {}  # type: dict[int, MatDef | None]
    matdef_class = settings.game_config.matdef_class

    for mesh in flver.meshes:
        material_hash = hash_material(mesh.material)  # TODO: should hash ignore material name?
        if material_hash in flver_matdefs:
            continue  # material already created (used by a previous mesh)

        # Try to look up material info from MTD or MATBIN (Elden Ring).
        if matdef_class:
            mat_def_name = Path(mesh.material.mat_def_path).name
            try:
                if BLENDER_GAME_CONFIG[settings.game_type].uses_matbin:
                    if mat_def_name.endswith(".mtd"):
                        operator.warning(f"Elden Ring MTDs are not yet supported: {mat_def_name}")
                        matdef = None
                    else:
                        matdef = matdef_class.from_matbinbnd_or_name(mat_def_name, matbinbnd)
                else:
                    matdef = matdef_class.from_mtdbnd_or_name(mat_def_name, mtdbnd)
            except MatDefError as ex:
                operator.warning(
                    f"Could not create `MatDef` for game material '{mat_def_name}'. Error:\n"
                    f"    {ex}"
                )
                matdef = None
        else:
            operator.warning(f"FLVER material definition (`MatDef`) not implemented for game {settings.game.name}.")
            matdef = None

        flver_matdefs[material_hash] = matdef

    # Pre-scan which FLVER materials are used by meshes with differing backface culling and/or `is_dynamic`, so that
    # the extra Blender materials created for those variants can be named informatively (the unvarying property is
    # left out of the name, as it would just be noise on every single material).
    hash_varies_backface_culling = _get_varying_material_hashes(flver, lambda mesh: mesh.use_backface_culling)
    hash_varies_is_dynamic = _get_varying_material_hashes(flver, lambda mesh: mesh.is_dynamic)

    new_materials = []

    for mesh, mesh_textures in zip(flver.meshes, all_mesh_texture_stems, strict=True):
        material = mesh.material
        material_hash = hash_material(material)  # NOTE: if there are duplicate FLVER materials, this will combine them
        variant_key = (material_hash, mesh.use_backface_culling, mesh.is_dynamic)

        if variant_key in flver_material_variants:
            # Identical FLVER material AND mesh properties. Blender material can be shared with an earlier mesh.
            mesh_bl_material_indices.append(flver_material_variants[variant_key])
            continue

        vertex_color_count = mesh.vertex_color_count
        mat_def_path = Path(material.mat_def_path)
        matdef = flver_matdefs[material_hash]

        is_first_variant = material_hash not in flver_material_hash_indices
        if is_first_variant:
            flver_material_hash_indices[material_hash] = len(flver_material_hash_indices)

        # Create a relatively informative material name. We use material index, mat def, and model name as a
        # suffix to maximize the chances of a unique Blender name.
        # NOTE: Vanilla material names are unused and essentially worthless. They can also be the same for
        #  materials that actually use different lightmaps, EVEN INSIDE the same FLVER model.
        bl_material_name = (
            f"{material.name} [{flver_material_hash_indices[material_hash]} | {mat_def_path.stem} | {model_name}]"
        )
        # Only tag the properties that actually vary between this FLVER material's meshes.
        if material_hash in hash_varies_backface_culling and mesh.use_backface_culling:
            bl_material_name += " <BC>"
        if material_hash in hash_varies_is_dynamic and not mesh.is_dynamic:
            bl_material_name += " <STATIC>"

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
            # Only warn once per FLVER material, not again for each of its variants.
            warn_missing_textures=is_first_variant and image_import_manager is not None,
            bl_materials_by_matdef_name=bl_materials_by_matdef_name,
        )

        bl_material_index = len(new_materials)
        new_materials.append(bl_material)
        mesh_bl_material_indices.append(bl_material_index)
        flver_material_variants[variant_key] = bl_material_index

        if matdef:
            uv_slot_tuple = matdef.get_uv_slot_tuple()
            bl_material_uv_layer_names.append(tuple(layer.name for layer in uv_slot_tuple))
        else:
            # UV layer names not known for this material. `MergedMesh` will just use index, which may cause
            # conflicting types of UV data to occupy the same Blender UV slot.
            bl_material_uv_layer_names.append(())

    return CreatedFLVERMaterials(
        tuple(new_materials), tuple(mesh_bl_material_indices), tuple(bl_material_uv_layer_names)
    )


def _get_varying_material_hashes(flver: FLVER, get_mesh_property: tp.Callable[[tp.Any], tp.Any]) -> set[int]:
    """Find the hashes of FLVER materials whose meshes do not all agree on `get_mesh_property(mesh)`."""
    hash_values = {}  # type: dict[int, set]
    for mesh in flver.meshes:
        hash_values.setdefault(hash_material(mesh.material), set()).add(get_mesh_property(mesh))
    return {material_hash for material_hash, values in hash_values.items() if len(values) > 1}


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
            mat_def_name = Path(mesh.material.mat_def_path).name
            try:
                matbin = matbinbnd.get_matbin(mat_def_name)
            except KeyError:
                pass  # missing
            else:
                mesh_texture_stems |= matbin.get_all_sampler_stems(lower=True)
        for texture in mesh.material.textures:
            if texture.path:
                # FLVER texture path can also override MATBIN path.
                mesh_texture_stems[texture.texture_type] = Path(texture.path).stem.lower()
        all_mesh_texture_names.append(mesh_texture_stems)

    return all_mesh_texture_names


def _load_texture_images(
    operator: LoggingOperator,
    context: bpy.types.Context,
    name: str,
    texture_stems: set[str],
    image_import_manager: ImageImportManager | None = None,
    texture_finders: tp.Sequence[pyre_flver.TextureFinder] = (),
) -> DDSTextureCollection:
    """Load texture images from PNG cache directory or TPFs found with `image_import_manager`.

    Will NEVER load an image that is already in Blender's data, regardless of image type (identified by stem only).
    Note that these stems ARE case-sensitive, as I don't want them to change when a FLVER is imported and exported
    without any other modifications. (The cached images are also case-sensitive.)
    """
    settings = operator.settings(context)
    mat_settings = context.scene.flver_material_settings

    # TODO: I was checking every Image in Blender's data to find 1x1 magenta dummy textures to replace, but that's
    #  super slow as more and more textures are loaded. Dummy textures will need to be manually replaced.
    bl_image_stems = {image_name.split(".")[0] for image_name in bpy.data.images.keys()}

    new_texture_collection = DDSTextureCollection()

    tpf_textures_to_load = {}  # type: dict[str, TPFTexture]
    image_cache_directory = mat_settings.get_game_image_cache_directory(context)
    if image_cache_directory:
        image_cache_directory.mkdir(parents=True, exist_ok=True)
    if mat_settings.cache_new_game_images and image_cache_directory:
        write_image_directory = image_cache_directory
    else:
        write_image_directory = None

    bl_image_format = mat_settings.bl_image_cache_format
    texture_finder_format = (
        pyre_flver.ImageFormat.PNG if bl_image_format == BlenderImageFormat.PNG else pyre_flver.ImageFormat.TGA
    )

    for texture_stem in texture_stems:
        if texture_stem in bl_image_stems:
            continue  # already loaded
        if image_import_manager and texture_stem in tpf_textures_to_load:
            continue  # already queued to load below

        if mat_settings.import_cached_images and image_cache_directory:
            cached_path = mat_settings.get_cached_image_path(context, texture_stem)
            if cached_path.is_file():
                # Found cached image.
                try:
                    dds_texture = DDSTexture.new_from_image_path(cached_path, mat_settings.pack_image_data)
                except Exception as ex:
                    operator.error(f"Failed to load cached image path '{cached_path}' into Blender. Error: {ex}")
                    bl_image_stems.add(texture_stem)  # don't try again
                    continue
                new_texture_collection.add(dds_texture)
                bl_image_stems.add(texture_stem)
                continue

        if texture_finders:
            for i, texture_finder in enumerate(texture_finders):
                # Searching for original texture is NOT case-sensitive.
                try:
                    # DDS parsing may still fail for a few textures (e.g. Demon's Souls).
                    image_data = texture_finder.get_texture_as(texture_stem, texture_finder_format, name)
                except Exception as ex:
                    operator.warning(
                        f"Could not convert DDS texture '{texture_stem}' with DirectX. Error: {ex}"
                    )
                    bl_image_stems.add(texture_stem)  # don't try again
                    continue  # try next TextureFinder or proceed to `else` below
                if not image_data:
                    continue  # try next TextureFinder or proceed to `else` below

                try:
                    dds_texture = DDSTexture.new_from_image_data(
                        name=texture_stem,
                        image_format=bl_image_format,
                        image_data=image_data,
                        image_cache_directory=write_image_directory,
                        replace_existing=False,  # not currently used
                        pack_image_data=mat_settings.pack_image_data,
                    )
                except SoulstructTypeError as ex:
                    operator.warning(f"Could not load '{texture_stem}' as DDS texture. Error: {ex}")
                    bl_image_stems.add(texture_stem)  # don't try again
                    continue  # try next TextureFinder or proceed to `else` below
                else:
                    # DDS loaded successfully.
                    new_texture_collection.add(dds_texture)
                    bl_image_stems.add(texture_stem)
                    break  # don't check more TextureFinders
            else:
                operator.warning(f"Could not find FLVER texture '{texture_stem}' with any TextureFinders.")

            continue  # go to next texture

        if image_import_manager:
            try:
                # Searching for original texture is NOT case-sensitive.
                texture = image_import_manager.get_flver_texture(texture_stem, name)
            except KeyError as ex:
                operator.warning(f"Could not find FLVER texture '{texture_stem}' with ImageImportManager. Error: {ex}")
            else:
                tpf_textures_to_load[texture_stem] = texture
                continue  # texture found, go to next texture

    # This section is only used by ImageImportManager, not TextureFinder.
    if tpf_textures_to_load:
        for texture_stem in tpf_textures_to_load:
            operator.debug(f"Loading texture into Blender: {texture_stem}")
        p = time.perf_counter()
        deswizzle_platform = settings.game_config.swizzle_platform

        if bl_image_format == BlenderImageFormat.TARGA:
            all_image_data = batch_get_tpf_texture_tga_data(
                list(tpf_textures_to_load.values()), deswizzle_platform
            )
        elif bl_image_format == BlenderImageFormat.PNG:
            all_image_data = batch_get_tpf_texture_png_data(
                list(tpf_textures_to_load.values()), deswizzle_platform, fmt="rgba"
            )
        else:
            raise ValueError(f"Unsupported image format for DDS conversion: {bl_image_format}")

        operator.debug(
            f"Converted DDS images to {bl_image_format.value} in {time.perf_counter() - p:.3f} s "
            f"(cached = {mat_settings.cache_new_game_images})"
        )

        for texture_stem, image_data in zip(tpf_textures_to_load.keys(), all_image_data):
            if image_data is None:
                continue  # failed to convert this texture
            try:
                dds_texture = DDSTexture.new_from_image_data(
                    name=texture_stem,
                    image_format=bl_image_format,
                    image_data=image_data,
                    image_cache_directory=write_image_directory,
                    replace_existing=False,  # not currently used
                    pack_image_data=mat_settings.pack_image_data,
                )
            except SoulstructTypeError as ex:
                operator.warning(f"Could not load as DDS texture: {texture_stem}. Error: {ex}")
                continue
            new_texture_collection.add(dds_texture)

    return new_texture_collection

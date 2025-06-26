from __future__ import annotations

__all__ = [
    "export_map_area_textures",
    "ExportTexturesIntoBinderOrTPF",
]

from pathlib import Path

import bpy
from soulstruct.containers import Binder
from soulstruct.containers.tpf import TPF
from soulstruct.dcx import DCXType
from soulstruct.blender.utilities import *
from .types import *


def export_map_area_textures(
    operator: LoggingOperator,
    context: bpy.types.Context,
    map_area: str,
    dds_textures: DDSTextureCollection,
) -> list[Path]:
    """Create and write map area TPFBHDs for all map stem keys and `DDSTexture` collections in `map_area_textures`.

    TODO: When to use 'mAA_9999.tpf.dcx'? Never?
    """
    settings = operator.settings(context)
    if not settings.is_game("DARK_SOULS_DSR"):
        operator.error("Map textures not exported: only supported for Dark Souls: Remastered.")
        return []

    # We don't pass `if_exist = True` to these calls. They will only be `None` if the corresponding root is `None`.
    # The directory paths themselves may not exist in the corresponding root.
    game_map_area_dir = settings.game_root and settings.game_root.get_dir_path(f"map/{map_area}")
    project_map_area_dir = settings.project_root and settings.project_root.get_dir_path(f"map/{map_area}")
    if not project_map_area_dir and not settings.also_export_to_game:
        # No possible export location. Should be caught by `settings.can_export` check in opreator poll, but making
        # extra sure here that any sort of TPFBHD export is possible before the expensive DDS conversion call below.
        operator.error(
            f"Map textures not exported for area {map_area}. "
            f"Project directory is not set and 'Also Export to Game' is disabled."
        )
        return []  # no point checking other areas

    # Collect existing TPFBHD paths from project and/or game directories.
    project_tpfbhd_paths = list(project_map_area_dir.glob("*.tpfbhd")) if is_path_and_dir(project_map_area_dir) else []
    game_tpfbhd_paths = list(game_map_area_dir.glob("*.tpfbhd")) if is_path_and_dir(game_map_area_dir) else []

    if not project_tpfbhd_paths and not game_tpfbhd_paths:
        # One or both roots are set, but neither directory exists AND contains initial TPFBHDs.
        operator.error(
            f"Map textures not exported for area {map_area}. "
            f"No initial TPFBHD Binders could be found to modify."
        )
        return []

    if is_path_and_dir(project_map_area_dir) and not project_tpfbhd_paths:
        # Log a helpful warning about empty project directory for this map area.
        operator.warning(
            f"Project map area directory '{project_map_area_dir}' exists, but is empty. Initial TPFBHD Binders from "
            f"game directory will be used."
        )

    # Logic from here is parallel to `SoulstructSettings.get_initial_binder()`, but for multiple TPFBHD Binders.

    if not project_tpfbhd_paths:
        # No project TPFBHDs. We use game TPFBHDs as initial Binders (they must exist, as per above check).
        map_area_dir = game_map_area_dir
    else:
        # We use the project TPFBHDs, but also log warnings if the game TPFBHDs are absent.
        map_area_dir = project_map_area_dir
        if not game_tpfbhd_paths:
            operator.warning(
                f"Project TPFBHDs ({len(project_tpfbhd_paths)} Binders) will be used as initial TPFBHDs for texture "
                f"export for area {map_area}. However, the game directory does not contain any TPFBHD Binders for this "
                f"area. This is unusual."
            )

    # This call does NOT write any TPFBHDs. It reads all existing textures from `map_area_dir`, exports collected DDS
    # textures into single-TPF entries, splits them into TPFBHDs, and returns those TPFBHDs for us to export.
    map_tpfbhds = dds_textures.into_map_area_tpfbhds(operator, context, map_area_dir)
    exported_paths = []
    for tpfbhd in map_tpfbhds:
        relative_tpfbhd_path = Path(f"map/{map_area}/{tpfbhd.path.name}")
        exported_paths += settings.export_file(operator, tpfbhd, relative_tpfbhd_path)
    return exported_paths


class ExportTexturesIntoBinderOrTPF(LoggingImportOperator):
    """
    TODO: Shelved for now. Will basically just be a glorified converter to DDS formats. Probably want a version that
     exports ONE selected texture node or Image Viewer texture to a loose DDS or TPF, and another that exports all
     textures in a selected material into separate TPFs (maps) or multi TPFs (characters, etc.) in an existing Binder,
     like this one currently sort of does.
    """

    bl_idname = "export_image.texture_binder_tpf"
    bl_label = "Export Textures Into Binder/TPF"
    bl_description = (
        "Export image textures from selected Image Texture node(s) into a FromSoftware TPF or TPF-containing Binder "
        "(BND/BHD)"
    )

    filter_glob: bpy.props.StringProperty(
        default="*.tpf;*.tpf.dcx;*.tpfbhd;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(options={'HIDDEN'})

    dcx_type: get_dcx_enum_property(
        description="Type of DCX compression to apply to any new TPF inside an uncompressed TPFBHD",
    )

    @classmethod
    def poll(cls, context) -> bool:
        try:
            # TODO: What if you just want to export an image from the Image Viewer? Different operator?
            sel_tex_nodes = [
                node for node in context.active_object.active_material.node_tree.nodes
                if node.select and node.bl_idname == "ShaderNodeTexImage"
            ]
            return bool(sel_tex_nodes)
        except (AttributeError, IndexError):
            return False

    def execute(self, context):
        self.info("Executing texture export...")

        # TODO: Should this operator really support export to multiple binders simultaneously (and they'd have to be in
        #  the same folder)?
        # noinspection PyTypeChecker
        sel_tex_nodes = [
            node for node in context.active_object.active_material.node_tree.nodes
            if node.select and node.bl_idname == "ShaderNodeTexImage"
        ]  # type: bpy.types.ShaderNodeTexImage

        if not sel_tex_nodes:
            return self.error("No Image Texture material node selected.")

        settings = self.settings(context)
        path = Path(self.filepath)

        dcx_type = DCXType.Null

        # Four possible cases to handle:
        #   - a single-texture TPF
        #   - a multi-texture TPF
        #   - a Binder with a single eponymous multi-texture TPF
        #   - a Binder with multiple single-texture TPFs
        try:
            if path.name.endswith(".tpf") or path.name.endswith(".tpf.dcx"):
                # Put texture into loose TPF.
                tpf = TPF.from_path(path)
                binder = None
                # No DCX.
            else:
                tpf = None
                binder = Binder.from_path(path)
                if binder.dcx_type == DCXType.Null:
                    # Apply appropriate TPF compression inside uncompressed Binder.
                    dcx_type = settings.resolve_dcx_type(self.dcx_type, "tpf")
        except Exception as ex:
            return self.error(f"Error occurred when trying to read '{path}' as a TPF or Binder:\n  {str(ex)}")

        for tex_node in sel_tex_nodes:

            if not tex_node.image:
                self.warning("Ignoring Image Texture node with no image assigned.")
                continue

            if len(tex_node.image.pixels) <= 4:
                self.warning("Ignoring Image Texture node with a placeholder 1x1 image assigned.")
                continue

            dds_texture = DDSTexture(tex_node.image)

            target_tpf = tpf  # could be None
            if binder is not None:
                for entry in binder.entries:
                    if entry.name.endswith((".tpf", ".tpf.dcx")):
                        if entry.minimal_stem == dds_texture.stem:
                            # Found a single-texture TPF matching this texture stem. Replace in entry.
                            new_tpf = dds_texture.to_single_texture_tpf(
                                self,
                                dcx_type,
                                lambda _stem: entry.to_binary_file(TPF).textures[0].get_dds().texconv_format,
                            )
                            entry.set_from_binary_file(new_tpf)
                            break
                        elif entry.minimal_stem == binder.path_minimal_stem:
                            # Found a multi-texture TPF. Treat as target TPF.
                            target_tpf = entry.to_binary_file(TPF)
                else:
                    # Create new single-texture TPF entry.
                    new_tpf = dds_texture.to_single_texture_tpf(
                        self,
                        dcx_type,
                        find_same_format=None,  # cannot resolve 'SAME' DDS format
                    )
                    # TODO

        return {"FINISHED"}

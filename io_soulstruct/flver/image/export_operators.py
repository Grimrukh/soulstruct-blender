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
from io_soulstruct.utilities import *
from .types import *


def export_map_area_textures(
    operator: LoggingOperator,
    context: bpy.types.Context,
    map_area: str,
    dds_textures: DDSTextureCollection,
):
    """Create and write map area TPFBHDs for all map stem keys and `DDSTexture` collections in `map_area_textures`.

    TODO: When to use 'mAA_9999.tpf.dcx'? Never?
    """
    settings = operator.settings(context)
    if not settings.is_game("DARK_SOULS_DSR"):
        operator.error("Map textures not exported: only supported for Dark Souls: Remastered.")
        return

    import_area_dir = settings.get_game_path(f"map/{map_area}")
    export_area_dir = settings.get_project_path(f"map/{map_area}")
    if not export_area_dir and not settings.also_export_to_game:
        # Should be caught by `settings.can_export` check in poll, but making extra sure here that any sort
        # of TPFBHD export is possible before the expensive DDS conversion call below.
        operator.error("Map textures not exported: game export path not set and export-to-import disabled.")
        return  # no point checking other areas
    if not (import_area_dir and import_area_dir.is_dir()) and not (
        export_area_dir and export_area_dir.is_dir()):
        operator.error(
            f"Textures not written. Cannot find map texture Binders to modify from either export "
            f"(preferred) or import (backup) map area directory: 'map/{map_area}"
        )
        return
    if export_area_dir and import_area_dir and import_area_dir.is_dir():
        # Copy initial TPFBHDs/BDTs from import directory (will not overwrite existing).
        # Will raise a `FileNotFoundError` if import file does not exist.
        for tpfbhd_path in import_area_dir.glob("*.tpfbhd"):
            settings.prepare_project_file(Path(f"map/{map_area}/{tpfbhd_path.name}"), False, True)
        for tpfbdt_path in import_area_dir.glob("*.tpfbdt"):
            settings.prepare_project_file(Path(f"map/{map_area}/{tpfbdt_path.name}"), False, True)

    # We prefer to start with the TPFBHDs from the export directory (potentially just copied from import).
    if export_area_dir and export_area_dir.is_dir():
        map_area_dir = export_area_dir
    else:
        map_area_dir = import_area_dir

    if not map_area_dir or not map_area_dir.is_dir():
        operator.error(
            f"Textures not written. Cannot load map texture Binders from missing map area directory: "
            f"{map_area_dir}"
        )
        return
    map_tpfbhds = dds_textures.into_map_area_tpfbhds(operator, context, map_area_dir)
    for tpfbhd in map_tpfbhds:
        relative_tpfbhd_path = Path(f"map/{map_area}/{tpfbhd.path.name}")
        settings.export_file(operator, tpfbhd, relative_tpfbhd_path)


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

    # ImportHelper mixin class uses this
    filename_ext = ".chrbnd"

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
    def poll(cls, context):
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
        sel_tex_nodes = [
            node for node in context.active_object.active_material.node_tree.nodes
            if node.select and node.bl_idname == "ShaderNodeTexImage"
        ]
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
            if self.filepath.endswith(".tpf") or self.filepath.endswith(".tpf.dcx"):
                # Put texture into loose TPF.
                tpf = TPF.from_path(self.filepath)
                binder = None
                # No DCX.
            else:
                tpf = None
                binder = Binder.from_path(self.filepath)
                if binder.dcx_type == DCXType.Null:
                    # Apply appropriate TPF compression inside uncompressed Binder.
                    dcx_type = settings.resolve_dcx_type(self.dcx_type, "tpf")
        except Exception as ex:
            return self.error(f"Error occurred when trying to read '{self.filepath}' as a TPF or Binder:\n  {str(ex)}")

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

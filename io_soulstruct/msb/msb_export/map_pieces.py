from __future__ import annotations

__all__ = [
    "ExportMSBMapPieces",
]

import traceback
import typing as tp
from pathlib import Path

from io_soulstruct.exceptions import *
from io_soulstruct.general.cached import get_cached_file
from io_soulstruct.utilities import *
from io_soulstruct.flver.model_export import FLVERExporter, FLVERExportSettings
from io_soulstruct.flver.textures.export_textures import export_map_area_textures
from io_soulstruct.flver.utilities import *
from .core import *
from .settings import *

if tp.TYPE_CHECKING:
    from io_soulstruct.type_checking import MSB_TYPING


class ExportMSBMapPieces(LoggingOperator):
    bl_idname = "export_scene.msb_map_piece_flver"
    bl_label = "Export Map Piece Parts"
    bl_description = (
        "Export transforms (to selected map MSB) and FLVER models (to selected map directory) of all selected Blender "
        "armatures/meshes. Model file names are detected from MSB part models"
    )

    @classmethod
    def poll(cls, context):
        """One or more 'm*' Armatures or Meshes selected."""
        return (
            len(context.selected_objects) > 0
            and all(
                obj.type in {"MESH", "ARMATURE"} and obj.name.startswith("m")
                for obj in context.selected_objects
            )
        )

    def execute(self, context):
        settings = self.settings(context)
        settings.save_settings()

        try:
            meshes_armatures = get_selected_flvers(context)
        except FLVERError as ex:
            return self.error(str(ex))

        # TODO: Later games (e.g. Elden Ring) use Binders like 'mapbnd' for map pieces, but this is not yet supported.
        #  This assumes loose FLVERs in the map folder. MAPBND support will require existing MAPBNDs, as the `.grass`
        #  files inside them will be left untouched.
        if not settings.map_stem and not settings.detect_map_from_collection:
            return self.error(
                "No map selected in Soulstruct settings and `Detect Map from Collection` is disabled."
            )

        flver_export_settings = context.scene.flver_export_settings  # type: FLVERExportSettings
        flver_dcx_type = settings.game.get_dcx_type("flver")
        msb_export_settings = context.scene.msb_export_settings  # type: MSBExportSettings

        self.to_object_mode()
        if msb_export_settings.export_model_files:
            exporter = FLVERExporter(self, context, settings)
        else:
            exporter = None

        active_object = context.active_object  # may be None

        # NOTE: Textures are NEVER exported if only MSB data is requested.
        map_area_textures = {}  # maps area stems 'mAA' to dictionaries of Blender images to export
        opened_msbs = {}  # type: dict[Path, MSB_TYPING]
        edited_part_names = {}  # type: dict[str, set[str]]  # keys are MSB stems (which may differ from 'map' stems)

        for mesh, armature in meshes_armatures:

            map_stem = settings.get_map_stem_for_export(armature or mesh, oldest=True)
            relative_map_path = Path(f"map/{map_stem}")

            # Get model file stem from MSB (must contain matching part).
            map_piece_part_name = get_default_flver_stem(mesh, armature, self)  # could be the same as the file stem

            relative_msb_path = settings.get_relative_msb_path(map_stem)  # will use latest MSB version
            msb_stem = relative_msb_path.stem

            if relative_msb_path not in opened_msbs:
                # Open new MSB. We start with the game MSB unless `Prefer Import from Project` is enabled.
                try:
                    msb_path = settings.prepare_project_file(relative_msb_path)
                except FileNotFoundError as ex:
                    self.error(
                        f"Could not find MSB file '{relative_msb_path}' for map '{map_stem}'. Error: {ex}"
                    )
                    continue
                opened_msbs[relative_msb_path] = get_cached_file(msb_path, settings.get_game_msb_class())

            msb = opened_msbs[relative_msb_path]  # type: MSB_TYPING

            edited_msb_part_names = edited_part_names.setdefault(msb_stem, set())
            if map_piece_part_name in edited_msb_part_names:
                self.warning(
                    f"Map Piece part '{map_piece_part_name}' was exported more than once in selected meshes."
                )
            edited_msb_part_names.add(map_piece_part_name)

            try:
                msb_part = msb.map_pieces.find_entry_name(map_piece_part_name)
            except KeyError:
                return self.error(
                    f"Map piece part '{map_piece_part_name}' not found in MSB '{msb_stem}'."
                )
            if not msb_part.model.name:
                return self.error(
                    f"Map piece part '{map_piece_part_name}' in MSB '{msb_stem}' has no model name."
                )

            model_name = find_model_name(self, armature or mesh, process_model_name_map_area(map_stem))
            msb_model_name = msb_part.model.get_model_file_stem(map_stem)
            if model_name != msb_model_name:
                # We update the MSB model name even if exporting MSB data only.
                self.warning(
                    f"Updating Map Piece model name of MSB part '{map_piece_part_name}' to '{model_name}'."
                )
                msb_part.model.set_name_from_model_file_stem(model_name)

            # Update part transform in MSB.
            obj_to_msb_entry_transform(armature or mesh, msb_part)

            if exporter:
                try:
                    flver = exporter.export_flver(
                        mesh,
                        armature,
                        dummy_material_prefix=model_name,  # TODO: annoying if this gets out of date?
                        dummy_prefix_must_match=False,  # Map Pieces export ALL dummy children
                        default_bone_name=model_name,  # Map Piece can omit Blender Armature/bones
                    )
                except Exception as ex:
                    traceback.print_exc()
                    return self.error(
                        f"Cannot get exported FLVER '{model_name}' from {mesh.name}. Error: {ex}"
                    )
                flver.dcx_type = flver_dcx_type
                # TODO: Elden Ring will need MAPBND export.
                settings.export_file(self, flver, relative_map_path / f"{model_name}.flver")

                if flver_export_settings.export_textures:
                    # Collect all Blender images for batched map area export.
                    area = settings.map_stem[:3]
                    area_textures = map_area_textures.setdefault(area, {})
                    area_textures |= exporter.collected_texture_images

        for relative_msb_path, msb in opened_msbs.items():
            # Write MSB.
            settings.export_file(self, msb, relative_msb_path)

        if map_area_textures:  # only non-empty if texture export enabled (and not only MSB data)
            export_map_area_textures(
                self,
                context,
                settings,
                map_area_textures,
            )

        # Select original active object.
        if active_object:
            context.view_layer.objects.active = active_object

        return {"FINISHED"}

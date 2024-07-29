__all__ = [
    "MSBImportExportPanel",
]

from .parts import *
from .regions import *

import bpy


class MSBImportExportPanel(bpy.types.Panel):
    """Panel for Soulstruct MSB import/export operators."""
    bl_label = "MSB Import/Export"
    bl_idname = "SCENE_PT_msb_import_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MSB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        ss_settings = context.scene.soulstruct_settings

        header, panel = self.layout.panel("Import Settings", default_closed=False)
        header.label(text="Import Settings")
        if panel:
            panel.label(text="Entry Name Match:")
            panel.prop(context.scene.msb_import_settings, "entry_name_match", text="")
            panel.label(text="Match Mode:")
            panel.prop(context.scene.msb_import_settings, "entry_name_match_mode", text="")
            panel.prop(context.scene.msb_import_settings, "include_pattern_in_parent_name")

        header, panel = self.layout.panel("Export Settings", default_closed=False)
        header.label(text="Export Settings")
        if panel:
            panel.prop(context.scene.soulstruct_settings, "detect_map_from_collection")
            panel.prop(context.scene.msb_export_settings, "model_export_mode")

        self.layout.label(text="Parts:")

        header, panel = self.layout.panel("Map Pieces", default_closed=True)
        header.label(text="Map Pieces")
        if panel:
            # We re-expose a selection of FLVER import settings for MSB map pieces here.
            flver_import_box = panel.box()
            flver_import_box.label(text="FLVER Import Settings")
            for prop in (
                "import_textures",
                "omit_default_bone",
                "material_blend_mode",
                "base_edit_bone_length",
            ):
                flver_import_box.prop(context.scene.flver_import_settings, prop)

            panel.operator(ImportMSBMapPiece.bl_idname)
            panel.operator(ImportAllMSBMapPieces.bl_idname)

            flver_export_box = panel.box()
            flver_export_box.label(text="FLVER Export Settings")
            for prop in (
                "export_textures",
                "create_lod_face_sets",
                "base_edit_bone_length",
                "allow_missing_textures",
                "allow_unknown_texture_types",
                "normal_tangent_dot_max",
            ):
                flver_export_box.prop(context.scene.flver_export_settings, prop)

            panel.operator(ExportMSBMapPieces.bl_idname)

        header, panel = self.layout.panel("Collisions", default_closed=True)
        header.label(text="Collision Import Settings")
        # TODO: Hiding collision submesh split option. Too annoying with MSB Part instances.
        self.panel_import_export_operators(
            panel, [ImportMSBMapCollision, ImportAllMSBMapCollisions], [ExportMSBCollisions],
        )

        header, panel = self.layout.panel("Navmeshes", default_closed=True)
        header.label(text="Navmeshes")
        self.panel_import_export_operators(
            panel, [ImportMSBNavmesh, ImportAllMSBNavmeshes], [ExportMSBNavmeshes, ExportMSBNavmeshCollection],
        )

        header, panel = self.layout.panel("Characters", default_closed=True)
        header.label(text="Characters")
        self.panel_import_export_operators(
            panel, [ImportMSBCharacter, ImportAllMSBCharacters], [ExportMSBCharacters],
        )

        if ss_settings.is_game("ELDEN_RING"):
            header, panel = self.layout.panel("Assets", default_closed=True)
            header.label(text="Assets")
            self.panel_import_export_operators(
                panel, [ImportMSBAsset, ImportAllMSBAssets], [],
            )
        else:
            header, panel = self.layout.panel("Objects", default_closed=True)
            header.label(text="Objects")
            self.panel_import_export_operators(
                panel, [ImportMSBObject, ImportAllMSBObjects], [ExportMSBObjects],
            )

        header, panel = self.layout.panel("Connect Collisions", default_closed=True)
        header.label(text="Connect Collisions")
        self.panel_import_export_operators(
            panel, [ImportMSBConnectCollision, ImportAllMSBConnectCollisions], [ExportMSBConnectCollisions],
        )

        self.layout.label(text="Regions:")

        header, panel = self.layout.panel("Point Regions", default_closed=True)
        header.label(text="Point Regions")
        if panel:
            panel.operator(ImportMSBPoint.bl_idname)
            panel.operator(ImportAllMSBPoints.bl_idname)
        header, panel = self.layout.panel("Volume Regions", default_closed=True)
        header.label(text="Volume Regions")
        if panel:
            panel.operator(ImportMSBVolume.bl_idname)
            panel.operator(ImportAllMSBVolumes.bl_idname)

    @staticmethod
    def panel_import_export_operators(
        panel: bpy.types.UILayout,
        import_operators: list[type[bpy.types.Operator]],
        export_operators: list[type[bpy.types.Operator]],
    ):
        if not panel:
            return  # closed
        if import_operators:
            import_box = panel.box()
            for operator_type in import_operators:
                import_box.operator(operator_type.bl_idname)
        if export_operators:
            export_box = panel.box()
            for operator_type in export_operators:
                export_box.operator(operator_type.bl_idname)

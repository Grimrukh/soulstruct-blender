from __future__ import annotations

__all__ = [
    "EnableSelectedNames",
    "DisableSelectedNames",
    "CreateMSBPart",
    "DuplicateMSBPartModel",
    "FindEntityID",
    "ColorMSBEvents",
]

import bpy

from io_soulstruct.exceptions import FLVERError
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.operator_config import BLENDER_MSB_PART_TYPES
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from .properties import MSBPartSubtype


class EnableSelectedNames(LoggingOperator):

    bl_idname = "object.enable_selected_names"
    bl_label = "Enable Selected Names"
    bl_description = "Enable name display for all selected objects"

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            obj.show_name = True
        return {"FINISHED"}


class DisableSelectedNames(LoggingOperator):

    bl_idname = "object.disable_selected_names"
    bl_label = "Disable Selected Names"
    bl_description = "Disable name display for all selected objects"

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            obj.show_name = False
        return {"FINISHED"}


class CreateMSBPart(LoggingOperator):

    bl_idname = "object.create_msb_part"
    bl_label = "Create MSB Part"
    bl_description = ("Create a new MSB Part instance from the selected Mesh model (FLVER, Collision, Navmesh, etc.) "
                      "and set its location to the 3D cursor")

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and context.active_object
            and context.active_object.soulstruct_type in {
                SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH
            }
        )

    def execute(self, context):

        settings = self.settings(context)

        obj = context.active_object
        if obj.soulstruct_type == SoulstructType.FLVER:
            # Use name to detect Part subtype.
            name = obj.name.lower()
            if name[0] == "m":
                part_subtype = MSBPartSubtype.MapPiece
            elif name[0] == "o":
                part_subtype = MSBPartSubtype.Object
            elif name[0] == "c":
                part_subtype = MSBPartSubtype.Character
            elif name[:3] == "aeg":
                part_subtype = MSBPartSubtype.Asset
            else:
                return self.error(
                    f"Cannot guess MSB Part subtype (Map Piece, Object/Asset, or Character) from FLVER name '{name}'."
                )
        elif obj.soulstruct_type == SoulstructType.COLLISION:
            # TODO: Another operator to create Connect Collision parts from Collision parts.
            part_subtype = MSBPartSubtype.Collision
        elif obj.soulstruct_type == SoulstructType.NAVMESH:
            part_subtype = MSBPartSubtype.Navmesh
        else:
            return self.error(f"Cannot create MSB Part from model object with Soulstruct type '{obj.soulstruct_type}'.")

        try:
            bl_part_type = BLENDER_MSB_PART_TYPES[settings.game][part_subtype]
        except KeyError:
            return self.error(
                f"Cannot import MSB Part subtype `{part_subtype.value}` for game {settings.game.name}."
            )

        model_stem = get_bl_obj_tight_name(obj)
        part_collection = get_or_create_collection(
            context.scene.collection,
            f"{settings.map_stem} Parts"
            f"{settings.map_stem} {part_subtype.get_nice_name()} Parts"
        )

        try:
            bl_part = bl_part_type.new_from_model_mesh(obj, f"{model_stem} Part", part_collection)
            # No properties (other than `model`) are changed from defaults.
        except FLVERError as ex:
            return self.error(f"Could not create `{part_subtype}` MSB Part from model object '{obj.name}': {ex}")

        # Set location to cursor.
        bl_part.obj.location = context.scene.cursor.location

        return {"FINISHED"}


class DuplicateMSBPartModel(LoggingOperator):

    bl_idname = "object.duplicate_part_model"
    bl_label = "Single-User Model"
    bl_description = (
        "Duplicate model of selected MSB Part to a new model with given name (or text before first underscore in Part "
        "name by default). Bone poses will also be copied if this is a Map Piece Part. Must be in Object Mode"
    )

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT" or not context.active_object:
            return False
        return context.active_object.soulstruct_type == SoulstructType.MSB_PART

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select an MSB Part in Object Mode.")

        settings = self.settings(context)
        part = context.active_object

        old_model = part.MSB_PART.model
        if old_model is None:
            return self.error("Active MSB Part does not have a model object reference.")

        part_subtype = part.MSB_PART.part_subtype
        old_part_name = part.name

        if not settings.new_model_name:
            new_model_name = old_part_name.split("_")[0]
            rename_part = False
            self.info(f"No name for new model specified. Using current prefix of Part name: '{new_model_name}'")
        else:
            new_model_name = settings.new_model_name
            rename_part = True

        # Check that name is available.
        if new_model_name in bpy.data.objects:
            return self.error(
                f"Blender object with name '{new_model_name}' already exists. Please choose a unique name for new "
                f"model."
            )

        # Find all collections containing source model.
        source_collections = old_model.users_collection

        if part_subtype in {
            MSBPartSubtype.MapPiece, MSBPartSubtype.Object, MSBPartSubtype.Character, MSBPartSubtype.Asset
        }:
            # Model is a FLVER.
            old_bl_flver = BlenderFLVER(old_model)
            old_model_name = old_bl_flver.name  # get from root object
            # TODO: Move below to a `BlenderFLVER.duplicate()` method.
            #  Then add methods for Collision and Navmeshes (easy, just Mesh data).
            self.info(f"Duplicating FLVER model '{old_bl_flver.name}' to '{new_model_name}'.")
            new_bl_flver = old_bl_flver.duplicate(
                new_model_name,
                collections=source_collections,
                copy_pose=part_subtype == MSBPartSubtype.MapPiece,
            )
            new_bl_flver.rename(new_model_name)
            new_model = new_bl_flver.mesh
        elif part_subtype == MSBPartSubtype.Collision:
            old_model_name = old_model.name
            new_model = new_mesh_object(new_model_name, old_model.data.copy())
            copy_obj_property_group(old_model, new_model, "hkx_map_collision")
        elif part_subtype == MSBPartSubtype.Navmesh:
            old_model_name = old_model.name
            new_model = new_mesh_object(new_model_name, old_model.data.copy())
            copy_obj_property_group(old_model, new_model, "nvm")
        else:
            return self.error(f"Cannot yet duplicate model of MSB Part subtype: {part_subtype}")

        # Update MSB Part model reference. (`model.update` will update Part data-block.)
        part.MSB_PART.model = new_model

        if rename_part:
            # New model created successfully. Now we update the MSB Part's name to reflect it, and use its name.
            # The Part name may just be part of the full old model name, so we find the overlap size and update from
            # that much of the new model name, e.g. 'm2000B0_0000_SUFFIX' * 'm2000B0A10' = 'm2000B0'.
            for i, (a, b) in enumerate(zip(old_part_name, old_model_name)):
                if a != b:
                    new_part_prefix = new_model_name[:i]  # take same length prefix from new model name
                    new_part_suffix = old_part_name[i:]  # keep old Part suffix ('_0000', '_CASTLE', whatever).
                    part.name = f"{new_part_prefix}{new_part_suffix}"
                    break
            # No need for `else` because part name cannot have been identical to model name in Blender!

        return {"FINISHED"}


class FindEntityID(LoggingOperator):

    bl_idname = "object.find_msb_entity_id"
    bl_label = "Find Entity ID"
    bl_description = "Find and select the first MSB entry in the scene with the input entity ID"

    entity_id: bpy.props.IntProperty(
        name="Entity ID",
        description="Entity ID to search for",
        default=1000000,
        min=1,
        max=999999999,
    )

    active_collection_only: bpy.props.BoolProperty(
        name="Active Collection Only",
        description="Only search for MSB entries in the active collection and its children",
        default=False,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        self.deselect_all()

        entity_id = self.entity_id
        collection = context.collection if self.active_collection_only else context.scene.collection
        hits = 0
        for obj in collection.all_objects:
            if obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entity_id == entity_id:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                hits += 1
            if obj.soulstruct_type == SoulstructType.MSB_EVENT and obj.MSB_EVENT.entity_id == entity_id:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                hits += 1
            if obj.soulstruct_type == SoulstructType.MSB_REGION and obj.MSB_REGION.entity_id == entity_id:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                hits += 1

        if hits == 0:
            return self.error(f"No MSB entries with Entity ID {entity_id} found.")
        if hits > 1:
            return self.warning(f"Multiple MSB entries with Entity ID {entity_id} found and selected.")

        # Ideal: one object selected and active
        bpy.ops.view3d.view_selected()
        return {"FINISHED"}


class ColorMSBEvents(LoggingOperator):

    bl_idname = "object.color_msb_events"
    bl_label = "Color MSB Events"
    bl_description = ("Color MSB Event objects of the chosen type(s), and their parent Regions or Parts, in viewport. "
                      "Viewport Wire Color mode should be set to 'Object' to see these colors")

    # Settings are in `MSBToolSettings`.

    def execute(self, context):
        tool_settings = context.scene.msb_tool_settings

        # Find all MSB Event objects to color.
        if tool_settings.event_color_active_collection_only:
            objects = context.collection.all_objects
        else:
            objects = context.scene.collection.all_objects

        if tool_settings.event_color_type != "ALL":
            objects = [
                obj for obj in objects
                if obj.soulstruct_type == SoulstructType.MSB_EVENT
                and obj.MSB_EVENT.event_subtype == tool_settings.event_color_type  # enums are identical except for ALL
            ]
        else:
            objects = [
                obj for obj in objects
                if obj.soulstruct_type == SoulstructType.MSB_EVENT
            ]  # all subtypes

        for event in objects:
            event.color = tool_settings.event_color
            if event.parent:
                event.parent.color = tool_settings.event_color

        self.info(f"Colored {len(objects)} MSB Event objects and their parents.")

        return {"FINISHED"}

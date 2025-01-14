from __future__ import annotations

__all__ = [
    "EnableAllImportModels",
    "DisableAllImportModels",
    "EnableSelectedNames",
    "DisableSelectedNames",
    "CreateMSBPart",
    "CreateMSBRegion",
    "DuplicateMSBPartModel",
    "ApplyPartTransformToModel",
    "CreateConnectCollision",
    "FindEntityID",
    "ColorMSBEvents",
]

import typing as tp

import bpy
from mathutils import Matrix

from soulstruct.games import DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR

from io_soulstruct.exceptions import FLVERError
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.operator_config import BLENDER_MSB_PART_TYPES
from io_soulstruct.types import SoulstructType
from io_soulstruct.utilities import *
from .properties import MSBPartSubtype
from .utilities import primitive_cube

if tp.TYPE_CHECKING:
    from .types import IBlenderMSBPart


class EnableAllImportModels(LoggingOperator):

    bl_idname = "object.msb_enable_all_import_models"
    bl_label = "Enable All Import Models"
    bl_description = "Enable all MSB model import options"

    def execute(self, context):
        import_settings = context.scene.msb_import_settings
        import_settings.import_map_piece_models = True
        import_settings.import_collision_models = True
        import_settings.import_navmesh_models = True
        import_settings.import_object_models = True
        import_settings.import_character_models = True
        return {"FINISHED"}


class DisableAllImportModels(LoggingOperator):

    bl_idname = "object.msb_disable_all_import_models"
    bl_label = "Disable All Import Models"
    bl_description = "Disable all MSB model import options"

    def execute(self, context):
        import_settings = context.scene.msb_import_settings
        import_settings.import_map_piece_models = False
        import_settings.import_collision_models = False
        import_settings.import_navmesh_models = False
        import_settings.import_object_models = False
        import_settings.import_character_models = False
        return {"FINISHED"}


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

        # noinspection PyTypeChecker
        model_obj = context.active_object  # type: bpy.types.MeshObject
        if model_obj.type != "MESH":
            return self.error("Selected object must be a Mesh object (FLVER, Collision, or Navmesh model).")

        if model_obj.soulstruct_type == SoulstructType.FLVER:
            # Use start of name to detect Part subtype.
            name = model_obj.name.lower()
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
        elif model_obj.soulstruct_type == SoulstructType.COLLISION:
            # TODO: Another operator to create Connect Collision parts from Collision parts.
            part_subtype = MSBPartSubtype.Collision
        elif model_obj.soulstruct_type == SoulstructType.NAVMESH:
            part_subtype = MSBPartSubtype.Navmesh
        else:
            return self.error(
                f"Cannot create MSB Part from Blender object with Soulstruct type '{model_obj.soulstruct_type}'. "
                f"Must be a FLVER, Collision, or Navmesh model object."
            )

        try:
            bl_part_type = BLENDER_MSB_PART_TYPES[settings.game][part_subtype]  # type: type[IBlenderMSBPart]
        except KeyError:
            return self.error(
                f"Cannot import MSB Part subtype `{part_subtype.value}` for game {settings.game.name}."
            )

        model_stem = get_bl_obj_tight_name(model_obj)
        part_collection = get_or_create_collection(
            context.scene.collection,
            f"{settings.map_stem} MSB",
            f"{settings.map_stem} Parts",
            f"{settings.map_stem} {part_subtype.get_nice_name()} Parts",
        )

        try:
            # TODO: Won't create Armature parent for Parts that require it (Map Pieces).
            bl_part = bl_part_type.new(f"{model_stem} Part", model_obj.data, collection=part_collection)
            # No properties (other than `model`) are changed from defaults.
        except FLVERError as ex:
            return self.error(f"Could not create `{part_subtype}` MSB Part from model object '{model_obj.name}': {ex}")

        # Set location to cursor (Armature parent if present).
        obj = bl_part.armature or bl_part.obj
        obj.location = context.scene.cursor.location

        return {"FINISHED"}


class CreateMSBRegion(LoggingOperator):

    bl_idname = "object.create_msb_region"
    bl_label = "Create MSB Region (Box)"
    bl_description = "Create a new MSB Region instance with a box shape and set its location to the 3D cursor"

    def execute(self, context):
        settings = self.settings(context)
        if settings.game not in {DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR}:
            return self.error(f"Cannot create MSB Region for game {settings.game.name}.")

        region_collection = get_or_create_collection(
            context.scene.collection,
            f"{settings.map_stem} MSB",
            f"{settings.map_stem} Regions/Events",
        )

        region_mesh = bpy.data.meshes.new(f"{settings.map_stem}_Region")
        primitive_cube(region_mesh)
        region_obj = bpy.data.objects.new(f"{settings.map_stem}_Region", region_mesh)
        region_obj.display_type = "WIRE"
        region_obj.soulstruct_type = SoulstructType.MSB_REGION
        region_obj.MSB_REGION.region_subtype = "ALL"
        region_obj.MSB_REGION.shape_type = "Box"

        region_obj.location = context.scene.cursor.location
        region_collection.objects.link(region_obj)

        # Set as active and only selected object.
        context.view_layer.objects.active = region_obj
        self.deselect_all()
        region_obj.select_set(True)

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
        """Select at least one MSB Part."""
        if not context.selected_objects:
            return False
        if not all(obj.soulstruct_type == SoulstructType.MSB_PART for obj in context.selected_objects):
            return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select an MSB Part in Object Mode.")

        # Basic validation of selected objects:
        for obj in context.selected_objects:
            if obj.soulstruct_type != SoulstructType.MSB_PART:
                return self.error(f"Selected object '{obj.name}' is not an MSB Part. No models created.")
            if obj.MSB_PART.model is None:
                return self.error(
                    f"Selected MSB Part '{obj.name}' does not have a model object reference. No models created."
                )
            # Any other errors occur during duplication. We ignore them individually.

        success_count = 0
        for obj in context.selected_objects:
            try:
                self._duplicate_part_model(context, obj)
            except Exception as ex:
                self.error(f"Failed to duplicate model of MSB Part '{obj.name}': {ex}")
            else:
                success_count += 1

        if success_count == 0:
            return self.error("Failed to duplicate any models of selected MSB Parts.")

        self.info(
            f"Duplicated models of {success_count} / {len(context.selected_objects)} "
            f"MSB Part{'s' if success_count > 1 else ''}."
        )
        return {"FINISHED"}

    def _duplicate_part_model(self, context, part: bpy.types.Object):
        settings = self.settings(context)

        old_model = part.MSB_PART.model  # already validated
        # Find all collections containing source model.
        source_collections = old_model.users_collection

        part_subtype = part.MSB_PART.part_subtype
        old_part_name = part.name

        if not settings.new_model_name:
            new_model_name = self.get_auto_name(part, settings)
            rename_part = False
        else:
            new_model_name = settings.new_model_name
            rename_part = True

        # Check that name is available.
        if new_model_name in bpy.data.objects:
            return self.error(
                f"Blender object with name '{new_model_name}' already exists. Please choose a unique name for new "
                f"model."
            )

        if part_subtype in {
            MSBPartSubtype.MapPiece, MSBPartSubtype.Object, MSBPartSubtype.Character, MSBPartSubtype.Asset
        }:
            # Model is a FLVER.
            old_bl_flver = BlenderFLVER(old_model)
            old_model_name = old_bl_flver.name  # get from root object
            self.info(f"Duplicating FLVER model '{old_bl_flver.name}' to '{new_model_name}'.")
            new_bl_flver = old_bl_flver.duplicate(
                new_model_name,
                collections=source_collections,
                make_materials_single_user=True,
                copy_pose=part_subtype == MSBPartSubtype.MapPiece,
            )
            # Do a deep renaming of FLVER.
            new_bl_flver.deep_rename(new_model_name, old_model_name)
            new_model = new_bl_flver.mesh
        elif part_subtype == MSBPartSubtype.Collision:
            # TODO: Add as Collision `duplicate()` method.
            old_model_name = old_model.name
            new_model = new_mesh_object(new_model_name, old_model.data.copy())
            new_model.soulstruct_type = SoulstructType.COLLISION
            new_model.data.name = new_model_name
            copy_obj_property_group(old_model, new_model, "COLLISION")
            for collection in source_collections:
                collection.objects.link(new_model)
        elif part_subtype == MSBPartSubtype.Navmesh:
            # TODO: Add as NVM `duplicate()` method.
            old_model_name = old_model.name
            new_model = new_mesh_object(new_model_name, old_model.data.copy())
            new_model.soulstruct_type = SoulstructType.NAVMESH
            new_model.data.name = new_model_name
            # No NVM properties to copy.
            for collection in source_collections:
                collection.objects.link(new_model)

            # Copy any NVM Event Entity children of old model.
            for child in old_model.children:
                if child.soulstruct_type == SoulstructType.NVM_EVENT_ENTITY:
                    new_child = child.copy()  # empty object, no data to copy
                    new_child.name = child.name.replace(old_model_name, new_model_name)  # usually a prefix
                    new_child.parent = new_model
                    for collection in source_collections:
                        collection.objects.link(new_child)
        else:
            # No early game types left here.
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
            # No need for `else` because part name cannot have been identical to model name in Blender! And if we
            # exhausted one of the strings (probably the old model name) without finding a difference, the new Part
            # name will be identical anyway.

        return {"FINISHED"}

    def get_auto_name(self, part: bpy.types.Object, settings: SoulstructSettings) -> str:
        new_model_name = part.name.split("_")[0]

        if settings.is_game_ds1() and len(new_model_name) == 7:
            # Add 'A##' area suffix automatically, for convenience.
            try:
                map_stem = get_collection_map_stem(part)
            except ValueError:
                self.info(f"Automatic new model name (failed to detect 'A##' area suffix): '{new_model_name}'")
            else:
                new_model_name += f"A{map_stem[1:3]}"
                self.info(f"Automatic new model name with detected 'A##' area suffix: '{new_model_name}'")
        else:
            self.info(f"Automatic new model name: '{new_model_name}'")

        return new_model_name


class ApplyPartTransformToModel(LoggingOperator):

    bl_idname = "object.apply_part_transform_to_model"
    bl_label = "Apply Part Transform to Model"
    bl_description = ("For each selected Part, apply its local (NOT world) transform to its model data, then reset the "
                      "Part's transform to identity. This will cause the model to move to the Part's current location "
                      "unless any further parent transforms are being applied to the Part. Only useable for geometry "
                      "Parts (Map Pieces, Collisions, Navmeshes, Connect Collisions), for safety.")

    @classmethod
    def poll(cls, context):
        """Select at least one MSB Part."""
        if not context.selected_objects:
            return False
        valid_subtypes = {
            MSBPartSubtype.MapPiece,
            MSBPartSubtype.Collision,
            MSBPartSubtype.Navmesh,
            MSBPartSubtype.ConnectCollision,
        }
        if not all(
            obj.type == "MESH" and obj.soulstruct_type == SoulstructType.MSB_PART
            and obj.MSB_PART.part_subtype in valid_subtypes
            for obj in context.selected_objects
        ):
            return False
        return True

    def execute(self, context):
        if not self.poll(context):
            return self.error("Must select an MSB Part in Object Mode.")

        success_count = 0
        for obj in context.selected_objects:
            obj: bpy.types.MeshObject
            try:
                self._apply_part_transform(obj)
            except Exception as ex:
                self.error(f"Failed to apply transform of MSB Part '{obj.name}' to model: {ex}")
            else:
                success_count += 1

        if success_count == 0:
            return self.error("Failed to apply transform to any models of selected MSB Parts.")

        self.info(
            f"Applied transform to {success_count} / {len(context.selected_objects)} "
            f"MSB Part{'s' if success_count > 1 else ''}."
        )
        return {"FINISHED"}

    @staticmethod
    def _apply_part_transform(part: bpy.types.MeshObject):
        mesh = part.data
        local_transform = part.matrix_local.copy()
        mesh.transform(local_transform)  # applies to mesh data
        part.matrix_local = Matrix.Identity(4)  # reset to identity


class CreateConnectCollision(LoggingOperator):
    bl_idname = "object.create_connect_collision"
    bl_label = "Create Connect Collision"
    bl_description = ("Create a new Connect Collision instance from the selected MSB Collision part and adds it to the "
                      "Connect Collisions collection in the same MSB. Connects to map m00_00_00_00 initially.")

    @classmethod
    def poll(cls, context):
        settings = cls.settings(context)
        if not settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR):
            return False
        obj = context.active_object
        if not obj:
            return False
        return obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.part_subtype == MSBPartSubtype.Collision

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.active_object  # type: bpy.types.MeshObject

        settings = self.settings(context)
        if settings.is_game_ds1():
            from .darksouls1ptde.parts.msb_connect_collision import BlenderMSBConnectCollision
        elif settings.is_game(DEMONS_SOULS):
            from .demonssouls.parts.msb_connect_collision import BlenderMSBConnectCollision
        else:
            return self.error(f"Connect Collision creation not supported for game {settings.game.name}.")

        map_stem = get_collection_map_stem(obj)

        collection = get_or_create_collection(
            context.scene.collection,
            f"{map_stem} MSB",
            f"{map_stem} Parts",
            f"{map_stem} Connect Collision Parts"
        )

        if "_" in obj.name:
            prefix, suffix = obj.name.split("_", maxsplit=1)
            connect_collision_name = f"{prefix}_[00_00]_{suffix}"
        else:
            connect_collision_name = f"{obj.name}_[00_00]"

        bl_connect_collision = BlenderMSBConnectCollision.new(
            name=connect_collision_name,
            data=obj.data,
            collection=collection,
        )
        bl_connect_collision.collision = obj
        bl_connect_collision.model = obj.MSB_PART.model

        self.info(f"Created Connect Collision '{connect_collision_name}'.")

        # Select and view new object.
        context.view_layer.objects.active = bl_connect_collision.obj
        bl_connect_collision.obj.select_set(True)
        bpy.ops.view3d.view_selected()

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

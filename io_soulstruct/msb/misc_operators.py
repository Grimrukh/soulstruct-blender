from __future__ import annotations

__all__ = [
    "EnableAllImportModels",
    "DisableAllImportModels",
    "EnableSelectedNames",
    "DisableSelectedNames",
    "MSBPartCreationTemplates",
    "CreateMSBPart",
    "CreateMSBRegion",
    "CreateMSBEnvironmentEvent",
    "DuplicateMSBPartModel",
    "BatchSetPartGroups",
    "CopyDrawGroups",
    "ApplyPartTransformToModel",
    "CreateConnectCollision",
    "MSBFindPartsPointer",
    "FindMSBParts",
    "FindEntityID",
    "ColorMSBEvents",
]

import ast
import typing as tp

import bpy
from mathutils import Matrix

from soulstruct.base.maps.msb.region_shapes import RegionShapeType
from soulstruct.games import DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR

from io_soulstruct.exceptions import FLVERError
from io_soulstruct.general import SoulstructSettings
from io_soulstruct.collision.types import BlenderMapCollision
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.operator_config import BLENDER_MSB_PART_CLASSES
from io_soulstruct.msb.properties.parts import MSBPartArmatureMode
from io_soulstruct.navmesh.nvm.types import BlenderNVM
from io_soulstruct.utilities import *
from .properties import BlenderMSBPartSubtype
from .utilities import primitive_cube

if tp.TYPE_CHECKING:
    from .types.base import *


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
    def poll(cls, context) -> bool:
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
    def poll(cls, context) -> bool:
        return bool(context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            obj.show_name = False
        return {"FINISHED"}


def _is_map_piece_part(_, obj: bpy.types.Object) -> bool:
    return (
        obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.MapPiece
    )


def _is_object_part(_, obj: bpy.types.Object) -> bool:
    return (
        obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.Object
    )


def _is_character_part(_, obj: bpy.types.Object) -> bool:
    return (
        obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.Character
    )


def _is_collision_part(_, obj: bpy.types.Object) -> bool:
    return (
        obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.Collision
    )


def _is_navmesh_part(_, obj: bpy.types.Object) -> bool:
    return (
        obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.entry_subtype == BlenderMSBPartSubtype.Navmesh
    )


class MSBPartCreationTemplates(bpy.types.PropertyGroup):
    """Template pointers for `CreateMSBPart` operator (pointer properties cannot be used by operators)."""

    template_map_piece: bpy.props.PointerProperty(
        name="Template Map Piece",
        description="MSB Map Piece to copy fields from for the new Map Piece",
        type=bpy.types.Object,
        poll=_is_map_piece_part,
    )
    template_object: bpy.props.PointerProperty(
        name="Template Object",
        description="MSB Object to copy fields from for the new Object",
        type=bpy.types.Object,
        poll=_is_object_part,
    )
    template_character: bpy.props.PointerProperty(
        name="Template Character",
        description="MSB Character to copy fields from for the new Character",
        type=bpy.types.Object,
        poll=_is_character_part,
    )
    # TODO: `template_asset` when Elden Ring MSB is supported.
    template_collision: bpy.props.PointerProperty(
        name="Template Collision",
        description="MSB Collision to copy fields from for the new Collision",
        type=bpy.types.Object,
        poll=_is_collision_part,
    )
    template_navmesh: bpy.props.PointerProperty(
        name="Template Navmesh",
        description="MSB Navmesh to copy fields from for the new Navmesh",
        type=bpy.types.Object,
        poll=_is_navmesh_part,
    )


class CreateMSBPart(LoggingOperator):

    bl_idname = "object.create_msb_part"
    bl_label = "Create MSB Part"
    bl_description = (
        "Create a new MSB Part instance from the selected Mesh model (FLVER, Collision, or NVM Navmesh). The Part "
        "for FLVER models is detected from the model prefix ('m', 'o', 'c', or 'aeg'). Its location can be optionally "
        "set to the 3D cursor or otherwise left at origin. An existing Part can also be chosen as a template, with "
        "Draw/Display/Navmesh group override options. NOTE: This cannot create Connect Collision parts. Use the "
        "operator to create one from an existing Collision part instead"
    )

    msb_map_stem: bpy.props.StringProperty(
        name="MSB Map Stem",
        description="Map stem of MSB in which to create new MSB Part",
        default="",  # `invoke()` will set default for geo vs. non-geo
    )

    part_subtype: bpy.props.StringProperty(
        name="Part Subtype",
        description="Type of MSB Part to create",
        default="",
        options={"HIDDEN"},
    )

    part_name: bpy.props.StringProperty(
        name="Part Name",
        description="Name for the new MSB Part",
        default="",
    )
    move_to_cursor: bpy.props.BoolProperty(
        name="Move to Cursor",
        description="Move the new Part to the 3D cursor location (rather than leaving at origin)",
        default=False,
    )

    part_armature_mode: bpy.props.EnumProperty(
        name="Part Armature Mode",
        description="How to handle armatures for MSB Parts that use FLVER models",
        items=[
            (MSBPartArmatureMode.NEVER, "Never", "Never create armatures for FLVER MSB Parts"),
            (
                MSBPartArmatureMode.CUSTOM_ONLY,
                "Custom Only",
                "Only create armatures for FLVER MSB Parts for FLVER models that use Custom bone data",
            ),
            (
                MSBPartArmatureMode.IF_PRESENT,
                "If Present",
                "Create armatures for FLVER MSB Parts for FLVER models that have an armature",
            ),
            (MSBPartArmatureMode.ALWAYS, "Always", "Always create armatures for FLVER MSB Parts"),
        ],
        default=MSBPartArmatureMode.CUSTOM_ONLY,
    )

    draw_groups: bpy.props.StringProperty(
        name="Draw Groups",
        description="Exact draw group indices to assign to the new Part. Example: '[0, 37, 50]'. Leave blank to use "
                    "template Part's draw groups, or set to '[]' to clear all draw groups",
        default="",
    )
    display_groups: bpy.props.StringProperty(
        name="Display Groups",
        description="Exact display group indices to assign to the new Part. Example: '[0, 37, 50]'. Leave blank to use "
                    "template Part's display groups, or set to '[]' to clear all display groups",
        default="",
    )
    navmesh_groups: bpy.props.StringProperty(
        name="Navmesh Groups",
        description="Exact navmesh group indices to assign to the new Part. Example: '[0, 37, 50]'. Leave blank to use "
                    "template Part's navmesh groups, or set to '[]' to clear all navmesh groups",
        default="",
    )

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.mode == "OBJECT"
            and context.active_object
            and context.active_object.type == ObjectType.MESH
            and context.active_object.soulstruct_type in {
                SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH
            }
        )

    def invoke(self, context, event):
        # noinspection PyTypeChecker
        model_obj = context.active_object  # type: bpy.types.MeshObject

        try:
            part_subtype = self._get_part_subtype(model_obj)
        except ValueError as ex:
            return self.error(str(ex))

        if part_subtype in {
            BlenderMSBPartSubtype.MapPiece,
            BlenderMSBPartSubtype.Collision,
            BlenderMSBPartSubtype.Navmesh,
        }:
            try:
                self.msb_map_stem = get_collection_map_stem(model_obj)
            except ValueError:
                self.msb_map_stem = ""
        else:
            # Characters, Objects, Assets, Player Starts.
            self.msb_map_stem = context.scene.soulstruct_settings.map_stem

        # For `draw()` call.
        self.part_subtype = part_subtype.value
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context):

        templates = context.scene.msb_part_creation_templates

        if self.part_subtype == BlenderMSBPartSubtype.MapPiece:
            self.layout.prop(self, "msb_map_stem")
            self.layout.prop(self, "part_name")
            self.layout.prop(templates, "template_map_piece")
            self.layout.prop(self, "draw_groups")
        elif self.part_subtype == BlenderMSBPartSubtype.Object:
            self.layout.prop(self, "msb_map_stem")
            self.layout.prop(self, "part_name")
            self.layout.prop(templates, "template_object")
            self.layout.prop(self, "draw_groups")
        elif self.part_subtype == BlenderMSBPartSubtype.Character:
            self.layout.prop(self, "msb_map_stem")
            self.layout.prop(self, "part_name")
            self.layout.prop(templates, "template_character")
            self.layout.prop(self, "draw_groups")
        elif self.part_subtype == BlenderMSBPartSubtype.Collision:
            self.layout.prop(self, "msb_map_stem")
            self.layout.prop(self, "part_name")
            self.layout.prop(templates, "template_collision")
            self.layout.prop(self, "draw_groups")
            self.layout.prop(self, "display_groups")
            self.layout.prop(self, "navmesh_groups")
        elif self.part_subtype == BlenderMSBPartSubtype.Navmesh:
            self.layout.prop(self, "msb_map_stem")
            self.layout.prop(self, "part_name")
            self.layout.prop(templates, "template_navmesh")
            self.layout.prop(self, "navmesh_groups")
        else:
            self.layout.label(text=f"Invalid MSB Part subtype: {self.part_subtype}")

    @staticmethod
    def _get_part_subtype(model_obj: bpy.types.MeshObject) -> BlenderMSBPartSubtype:
        """Detect Part subtype that given model object should be used for.

        Uses prefix of FLVER model name to resolve FLVER part subtype.
        """
        if model_obj is None:
            raise ValueError("No model object selected.")

        if model_obj.soulstruct_type == SoulstructType.FLVER:
            # Use start of name to detect Part subtype.
            name = model_obj.name.lower()
            if name[0] == "m":
                return BlenderMSBPartSubtype.MapPiece
            elif name[0] == "o":
                return BlenderMSBPartSubtype.Object
            elif name[0] == "c":
                return BlenderMSBPartSubtype.Character
            elif name[:3] == "aeg":
                return BlenderMSBPartSubtype.Asset
            raise ValueError(
                f"Cannot guess MSB Part subtype (Map Piece, Object/Asset, or Character) from FLVER name '{name}'."
            )

        if model_obj.soulstruct_type == SoulstructType.COLLISION:
            # NOTE: There is a better operator to create Connect Collision parts from Collision parts.
            return BlenderMSBPartSubtype.Collision
        elif model_obj.soulstruct_type == SoulstructType.NAVMESH:
            return BlenderMSBPartSubtype.Navmesh

        raise ValueError(
            f"Cannot create MSB Part from Blender object with Soulstruct type '{model_obj.soulstruct_type}'. "
            f"Must be a FLVER, Collision, or Navmesh model object."
        )

    def execute(self, context):

        # noinspection PyTypeChecker
        model_obj = context.active_object  # type: bpy.types.MeshObject

        game = self.settings(context).game
        map_stem = self.msb_map_stem
        templates = context.scene.msb_part_creation_templates

        try:
            part_subtype = self._get_part_subtype(model_obj)
        except ValueError as ex:
            return self.error(str(ex))

        if part_subtype == BlenderMSBPartSubtype.MapPiece:
            template_part = templates.template_map_piece
            set_groups = (True, False, False)
        elif part_subtype == BlenderMSBPartSubtype.Object:
            template_part = templates.template_object
            set_groups = (True, False, False)
        elif part_subtype == BlenderMSBPartSubtype.Character:
            template_part = templates.template_character
            set_groups = (True, False, False)
        elif part_subtype == BlenderMSBPartSubtype.Collision:
            template_part = templates.template_collision
            set_groups = (True, True, True)
        elif part_subtype == BlenderMSBPartSubtype.Navmesh:
            template_part = templates.template_navmesh
            set_groups = (False, False, True)
        else:
            template_part = None
            set_groups = (False, False, False)

        draw_groups = display_groups = navmesh_groups = None
        try:
            if set_groups[0] and self.draw_groups:  # Draw
                _eval_draw_groups = ast.literal_eval(self.draw_groups)
                if isinstance(_eval_draw_groups, (list, tuple, set)):
                    draw_groups = set(_eval_draw_groups)
            if set_groups[1] and self.display_groups:  # Display
                _eval_display_groups = ast.literal_eval(self.display_groups)
                if isinstance(_eval_display_groups, (list, tuple, set)):
                    display_groups = set(_eval_display_groups)
            if set_groups[2] and self.navmesh_groups:  # Navmesh
                _eval_navmesh_groups = ast.literal_eval(self.navmesh_groups)
                if isinstance(_eval_navmesh_groups, (list, tuple, set)):
                    navmesh_groups = set(_eval_navmesh_groups)
        except SyntaxError as ex:
            return self.error(f"Failed to parse group indices: {ex}")

        name = self.part_name or f"{get_model_name(model_obj.name)} Part"

        try:
            bl_part_class = BLENDER_MSB_PART_CLASSES[game][part_subtype]  # type: type[BaseBlenderMSBPart]
        except KeyError:
            return self.error(
                f"Cannot import MSB Part subtype `{part_subtype.value}` for game {game.name}."
            )

        # TODO: Detect map stem from part! Don't just use global setting.
        #   - Operator setting can default to model's collection (for geo) or selected map stem (for non-geo).

        part_collection = get_or_create_collection(
            context.scene.collection,
            f"{map_stem} MSB",
            f"{map_stem} Parts",
            f"{map_stem} {part_subtype.get_nice_name()} Parts",
        )

        try:
            bl_part = bl_part_class.new(name, model_obj.data, collection=part_collection)
            # No properties (other than `model`) are changed from defaults.
        except FLVERError as ex:
            return self.error(f"Could not create `{part_subtype}` MSB Part from model object '{model_obj.name}': {ex}")
        bl_part.model = model_obj

        if part_subtype == BlenderMSBPartSubtype.MapPiece:
            # Create a duplicated parent Armature for the Part if present, so Map Piece static posing is visible.
            if model_obj.soulstruct_type == SoulstructType.MSB_MODEL_PLACEHOLDER:
                # Create Armature
                bl_part.duplicate_flver_model_armature(self, context, mode=MSBPartArmatureMode.IF_PRESENT)
        elif part_subtype == BlenderMSBPartSubtype.Navmesh:
            # Enable wireframe for Navmesh part.
            bl_part.obj.show_wire = True

        if self.move_to_cursor:
            # Set location to cursor (Armature parent if present).
            obj = bl_part.armature or bl_part.obj
            obj.location = context.scene.cursor.location

        if template_part:
            try:
                bl_part.copy_type_properties_from(template_part, self._prop_filter_func)
            except Exception as ex:
                self.error(
                    f"Failed to copy properties from template Part '{template_part.name}'. Part still created.\n"
                    f"Error: {ex}"
                )

        # Apply overrides for groups.
        try:
            bit_set_type = bl_part.SOULSTRUCT_CLASS.BIT_SET_TYPE
            if draw_groups is not None:
                bl_part.draw_groups = bit_set_type(draw_groups)
            if display_groups is not None:
                bl_part.display_groups = bit_set_type(display_groups)
            if navmesh_groups is not None:
                bl_part.navmesh_groups = bit_set_type(navmesh_groups)
        except Exception as ex:
            self.error(
                f"Failed to set some/all group bits on MSB Part. Part still created.\n"
                f"Error: {ex}"
            )

        return {"FINISHED"}

    @staticmethod
    def _prop_filter_func(prop_name: str) -> bool:
        """We don't copy `model` from template, but do copy everything else."""
        return prop_name != "model"


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
        region_obj.MSB_REGION.entry_subtype = "ALL"
        region_obj.MSB_REGION.shape_type = "Box"

        region_obj.location = context.scene.cursor.location
        region_collection.objects.link(region_obj)

        # Set as active and only selected object.
        context.view_layer.objects.active = region_obj
        self.deselect_all()
        region_obj.select_set(True)

        return {"FINISHED"}


class CreateMSBEnvironmentEvent(LoggingOperator):

    bl_idname = "object.create_msb_environment_event"
    bl_label = "Create MSB Env. Event"
    bl_description = (
        "For every selected MSB Collision part, create a new MSB Environment Event at the cursor location (with a "
        "Region point parent) attached to that Collision (which also attaches to the event). DS1 only. Does not "
        "actually generate the cubemap textures at these points. Will complain if the event already exists"
    )

    cubemap_index: bpy.props.IntProperty(
        name="Cubemap Index",
        description="Index of cubemap that combines with map stem to find GIEL texture in area TPF. Stored in 'Entity "
                    "ID' field of MSB Event",
        default=0,
    )

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if not settings.is_game_ds1():
            return False
        return all(
            obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.is_subtype(BlenderMSBPartSubtype.Collision)
            for obj in context.selected_objects
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        from .types.darksouls1ptde.parts import BlenderMSBCollision
        from .types.darksouls1ptde.events import BlenderMSBEnvironmentEvent
        from .types.darksouls1ptde.regions import BlenderMSBRegion

        settings = self.settings(context)
        if not settings.is_game_ds1():
            return self.error(f"Cannot create MSB Environment Events for game {settings.game.name}.")

        for obj in context.selected_objects:
            msb_stem = get_collection_map_stem(obj)
            bl_msb_collision = BlenderMSBCollision(obj)
            env_event_name = f"GIEL_{bl_msb_collision.game_name}"  # ' <Environment>' suffix added automatically
            if env_event_name + " <Environment>" in bpy.data.objects or env_event_name in bpy.data.objects:
                self.error(f"Environment Event '{env_event_name}' already exists. Skipping MSB Collision {obj.name}.")
                continue
            env_region_name = f"EnvironmentEvent_GIEL_{bl_msb_collision.game_name}"
            if env_region_name in bpy.data.objects:
                self.error(f"Region Point '{env_region_name}' already exists. Skipping MSB Collision {obj.name}.")
                continue

            regions_events_collection = get_or_create_collection(
                context.scene.collection,
                f"{msb_stem} MSB",
                f"{msb_stem} Regions/Events",
            )

            bl_region = BlenderMSBRegion.new_from_shape_type(
                self,
                context,
                RegionShapeType.Point,
                name=env_region_name,
                collection=regions_events_collection,
            )
            bl_event = BlenderMSBEnvironmentEvent.new(
                env_event_name,
                data=None,
                collection=regions_events_collection,
            )
            bl_event.obj.parent = bl_region.obj
            bl_event.entity_id = self.cubemap_index
            bl_event.attached_part = obj
            bl_event.attached_region = bl_region.obj
            # Leave other Environment unknown fields as they are.

            # Move region to cursor.
            bl_region.obj.location = context.scene.cursor.location

            # Attach event to collision (more important I believe).
            obj.MSB_COLLISION.environment_event = bl_event.obj

        return {"FINISHED"}


class DuplicateMSBPartModel(LoggingOperator):

    bl_idname = "object.duplicate_part_model"
    bl_label = "Single-User Model"
    bl_description = (
        "Duplicate model of selected MSB Part to a new model with given name (or text before first underscore in Part "
        "name by default). Bone poses will also be copied if this is a Map Piece Part. Must be in Object Mode"
    )

    new_model_name: bpy.props.StringProperty(
        name="New Model Name",
        description="Name for new model object. Leave blank to use text before first underscore in Part name",
        default="",
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Select at least one MSB Part."""
        if not context.selected_objects:
            return False
        if not all(obj.soulstruct_type == SoulstructType.MSB_PART for obj in context.selected_objects):
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

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

        old_model = part.MSB_PART.model  # type: bpy.types.MeshObject  # already validated
        # Find all collections containing source model.
        source_collections = old_model.users_collection

        part_subtype = part.MSB_PART.entry_subtype

        if not self.new_model_name:
            new_model_name = self.get_auto_name(part, settings)
            rename_part = False
        else:
            new_model_name = self.new_model_name
            rename_part = True

        # Check that name is available.
        if new_model_name in bpy.data.objects:
            return self.error(
                f"Blender object with name '{new_model_name}' already exists. Please choose a unique name for new "
                f"model."
            )

        if part_subtype in {
            BlenderMSBPartSubtype.MapPiece,
            BlenderMSBPartSubtype.Object,
            BlenderMSBPartSubtype.Character,
            BlenderMSBPartSubtype.Asset,
        }:
            # Model is a FLVER.
            old_bl_flver = BlenderFLVER(old_model)
            old_model_name = old_bl_flver.name  # get from root object
            self.info(f"Duplicating FLVER model '{old_bl_flver.name}' to '{new_model_name}'.")
            new_bl_flver = old_bl_flver.duplicate(
                context=context,
                collections=source_collections,
                make_materials_single_user=True,
                copy_pose=True,  # copy pose immediately (not batched)
            )
            # Do a deep renaming of FLVER.
            new_bl_flver.deep_rename(new_model_name, old_model_name)
            new_model = new_bl_flver.mesh

        elif part_subtype == BlenderMSBPartSubtype.Collision:
            # Model is a Collision.
            old_bl_collision = BlenderMapCollision(old_model)
            new_bl_collision = old_bl_collision.duplicate(source_collections)
            old_model_name = old_model.name
            new_bl_collision.rename(new_model_name)
            new_model = new_bl_collision.obj

        elif part_subtype == BlenderMSBPartSubtype.Navmesh:
            # Model is a Navmesh.
            old_bl_nvm = BlenderNVM(old_model)
            new_bl_nvm = old_bl_nvm.duplicate(source_collections)
            old_model_name = old_model.name
            new_bl_nvm.rename(new_model_name)
            new_model = new_bl_nvm.obj

        else:
            # No early game types left here.
            return self.error(f"Cannot yet duplicate model of MSB Part subtype: {part_subtype}")

        # Update MSB Part model reference. (`model.update` will update Part data-block.)
        part.MSB_PART.model = new_model

        if rename_part:
            # New model created successfully. Now we update the MSB Part's name to reflect it, and use its name.
            # The Part name may just be part of the full old model name, so we find the overlap size and update from
            # that much of the new model name, e.g. 'm2000B0_0000_SUFFIX' * 'm2000B0A10' = 'm2000B0'.
            part.name = replace_shared_prefix(old_model_name, new_model_name, part.name)

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


class BatchSetPartGroups(LoggingOperator):

    bl_idname = "object.batch_set_part_groups"
    bl_label = "Batch Set Part Groups"
    bl_description = (
        "Set, add, or remove draw, display, and/or navmesh groups for all selected MSB Parts from list syntax, e.g. "
        "'[0, 37, 50]'. Set empty list/set '[]' to clear all groups. Leave empty to ignore that group type. All "
        "selected Parts must have the same Part subtype, to assist in avoiding easy mistakes"
    )

    operation: bpy.props.EnumProperty(
        name="Operation",
        description="Operation to perform on groups",
        items=(
            ("SET", "Set", "Set groups to those specified"),
            ("ADD", "Add", "Add groups to existing groups"),
            ("REMOVE", "Remove", "Remove groups from existing groups"),
        ),
        default="SET",
    )

    draw_groups: bpy.props.StringProperty(
        name="Draw Groups",
        description="Draw groups to set for selected MSB Parts",
        default="",
    )
    display_groups: bpy.props.StringProperty(
        name="Display Groups",
        description="Display groups to set for selected MSB Parts",
        default="",
    )
    navmesh_groups: bpy.props.StringProperty(
        name="Navmesh Groups",
        description="Navmesh groups to set for selected MSB Collision/Navmesh Parts",
        default="",
    )

    @classmethod
    def poll(cls, context) -> bool:
        part_subtypes = set()
        for obj in context.selected_objects:
            if obj.soulstruct_type != SoulstructType.MSB_PART:
                return False
            part_subtypes.add(obj.MSB_PART.entry_subtype)
        if len(part_subtypes) == 1:
            return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Only shows appropriate groups."""
        self.layout.prop(self, "operation")
        self.layout.prop(self, "draw_groups")
        self.layout.prop(self, "display_groups")
        if context.selected_objects[0].MSB_PART.entry_subtype in {
            BlenderMSBPartSubtype.Collision, BlenderMSBPartSubtype.Navmesh
        }:
            self.layout.prop(self, "navmesh_groups")

    def execute(self, context):
        settings = self.settings(context)
        # We already checked that all selected objects have the same MSB Part subtype.
        part_subtype = context.selected_objects[0].MSB_PART.entry_subtype
        bl_part_class = BLENDER_MSB_PART_CLASSES[settings.game][part_subtype]  # type: type[BaseBlenderMSBPart]
        has_navmesh_groups = part_subtype in {BlenderMSBPartSubtype.Collision, BlenderMSBPartSubtype.Navmesh}

        draw_groups = display_groups = navmesh_groups = None
        try:
            if self.draw_groups:  # Draw
                _eval_draw_groups = ast.literal_eval(self.draw_groups)
                if isinstance(_eval_draw_groups, (list, tuple, set)):
                    draw_groups = set(_eval_draw_groups)
            if self.display_groups:  # Display
                _eval_display_groups = ast.literal_eval(self.display_groups)
                if isinstance(_eval_display_groups, (list, tuple, set)):
                    display_groups = set(_eval_display_groups)
            if self.navmesh_groups and has_navmesh_groups:
                _eval_navmesh_groups = ast.literal_eval(self.navmesh_groups)
                if isinstance(_eval_navmesh_groups, (list, tuple, set)):
                    navmesh_groups = set(_eval_navmesh_groups)
        except SyntaxError as ex:
            return self.error(f"Failed to parse group indices: {ex}")

        counts = [0, 0, 0]

        for obj in context.selected_objects:
            bl_part = bl_part_class(obj)
            bit_set_type = bl_part_class.SOULSTRUCT_CLASS.BIT_SET_TYPE
            if draw_groups is not None:
                if self.operation == "SET":
                    bl_part.draw_groups = bit_set_type(draw_groups)
                elif self.operation == "ADD":
                    bl_part.draw_groups |= bit_set_type(draw_groups)
                elif self.operation == "REMOVE":
                    bl_part.draw_groups -= bit_set_type(draw_groups)
                counts[0] += 1
            if display_groups is not None:
                if self.operation == "SET":
                    bl_part.display_groups = bit_set_type(display_groups)
                elif self.operation == "ADD":
                    bl_part.display_groups |= bit_set_type(display_groups)
                elif self.operation == "REMOVE":
                    bl_part.display_groups -= bit_set_type(display_groups)
                counts[1] += 1
            if navmesh_groups is not None and has_navmesh_groups:
                if self.operation == "SET":
                    bl_part.navmesh_groups = bit_set_type(navmesh_groups)
                elif self.operation == "ADD":
                    bl_part.navmesh_groups |= bit_set_type(navmesh_groups)
                elif self.operation == "REMOVE":
                    bl_part.navmesh_groups -= bit_set_type(navmesh_groups)
                counts[2] += 1

        self.info(
            f"Set draw groups for {counts[0]} Part{'s' if counts[0] > 1 else ''}, "
            f"display groups for {counts[1]} Part{'s' if counts[1] > 1 else ''}, "
            f"and navmesh groups for {counts[2]} Part{'s' if counts[2] > 1 else ''}."
        )

        return {"FINISHED"}


class CopyDrawGroups(LoggingOperator):

    bl_idname = "object.copy_draw_groups"
    bl_label = "Copy Draw Groups"
    bl_description = (
        "Copy exact Draw Groups from the active MSB Part to all selected MSB Parts. All selected Parts must be MSB "
        "Parts of any subtype"
    )

    @classmethod
    def poll(cls, context) -> bool:
        if len(context.selected_objects) < 2 or not context.active_object:
            return False
        return all(obj.soulstruct_type == SoulstructType.MSB_PART for obj in context.selected_objects)

    def execute(self, context):
        settings = self.settings(context)
        active_part = context.active_object
        active_part_subtype = active_part.MSB_PART.entry_subtype
        bl_part_class = BLENDER_MSB_PART_CLASSES[settings.game][active_part_subtype]  # type: type[BaseBlenderMSBPart]
        bl_active_part = bl_part_class(active_part)
        # noinspection PyUnresolvedReferences
        active_draw_groups = bl_active_part.draw_groups

        count = 0
        for part in context.selected_objects:
            if part is active_part:
                continue
            part_subtype = part.MSB_PART.entry_subtype
            bl_part = BLENDER_MSB_PART_CLASSES[settings.game][part_subtype](part)
            bl_part.draw_groups = active_draw_groups
            count += 1

        self.info(f"Copied draw groups from active Part to {count} other selected Parts.")
        return {"FINISHED"}


class ApplyPartTransformToModel(LoggingOperator):

    bl_idname = "object.apply_part_transform_to_model"
    bl_label = "Apply Part Transform to Model"
    bl_description = (
        "For each selected Part, apply its local (NOT world) transform to its model data, then reset the Part's "
        "transform to identity. This will cause the model to move to the Part's current location unless any further "
        "parent transforms are being applied to the Part. Gets around Blender's usual 'no multi user' constraint for "
        "applying an object transform to its Mesh. Only useable for geometry Parts (Map Pieces, Collisions, Navmeshes, "
        "Connect Collisions) for safety."
    )

    @classmethod
    def poll(cls, context) -> bool:
        """Select at least one MSB Part."""
        if not context.selected_objects:
            return False
        valid_subtypes = {
            BlenderMSBPartSubtype.MapPiece,
            BlenderMSBPartSubtype.Collision,
            BlenderMSBPartSubtype.Navmesh,
            BlenderMSBPartSubtype.ConnectCollision,
        }
        if not all(
            obj.type == ObjectType.MESH and obj.soulstruct_type == SoulstructType.MSB_PART
            and obj.MSB_PART.entry_subtype in valid_subtypes
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
                self._apply_matrix_local_to_mesh(obj)
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
    def _apply_matrix_local_to_mesh(part: bpy.types.MeshObject):
        mesh = part.data
        local_transform = part.matrix_local.copy()
        mesh.transform(local_transform)  # applies to mesh data
        part.matrix_local = Matrix.Identity(4)  # reset to identity


class CreateConnectCollision(LoggingOperator):
    bl_idname = "object.create_connect_collision"
    bl_label = "Create Connect Collision"
    bl_description = (
        "Create a new MSB Connect Collision instance for each selected MSB Collision part, connecting to the given map "
        "stem, and add the new Parts to the collection of Connect Collisions in the same MSB. Map stem must have "
        "format 'mAA_BB_CC_DD' (e.g. 'm10_00_00_00'). If CC and DD are both zero, tag '[AA_BB]' will be added to the "
        "name after the first underscore. Otherwise, the full '[AA_BB_CC_DD]' tag will be added. For simplicity, the "
        "draw and display groups of the Connect Collisions are controlled as just one (identical) integer, which is "
        "standard for Connect Collisions (I don't believe the draw groups are even used)"
    )

    connected_map_stem: bpy.props.StringProperty(
        name="Connected Map Stem",
        description="Map stem of the map this Connect Collision connects to, e.g. 'm10_00_00_00'",
        default="m00_00_00_00",
    )
    connected_display_group: bpy.props.IntProperty(
        name="Connected Display Group",
        description="Group in the connected map to display. If you want more, add them after creation",
        default=0,
        min=0,
        max=127,  # TODO: DS1 max, currently
    )

    @classmethod
    def poll(cls, context) -> bool:
        settings = cls.settings(context)
        if not settings.is_game(DEMONS_SOULS, DARK_SOULS_PTDE, DARK_SOULS_DSR):
            return False
        if not context.selected_objects:
            return False
        for obj in context.selected_objects:
            if obj.soulstruct_type != SoulstructType.MSB_PART:
                return False
            if obj.MSB_PART.entry_subtype != BlenderMSBPartSubtype.Collision:
                return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        settings = self.settings(context)
        if settings.is_game(DARK_SOULS_PTDE):
            from .types.darksouls1ptde import BlenderMSBConnectCollision
        elif settings.is_game(DARK_SOULS_DSR):
            from .types.darksouls1r import BlenderMSBConnectCollision
        elif settings.is_game(DEMONS_SOULS):
            from .types.demonssouls import BlenderMSBConnectCollision
        else:
            return self.error(f"Connect Collision creation not supported for game {settings.game.name}.")

        connected_match = MAP_STEM_RE.match(self.connected_map_stem)
        if not connected_match:
            return self.error(
                f"Connected map stem '{self.connected_map_stem}' does not match required format 'mAA_BB_CC_DD'."
            )
        connected_map_id = tuple(int(g) for g in connected_match.groups())
        area, block, cc, dd = connected_map_id
        if cc == 0 and dd == 0:
            tag = f"[{area:02d}_{block:02d}]"
        else:
            tag = f"[{area:02d}_{block:02d}_{cc:02d}_{dd:02d}]"  # full tag required

        bl_connect_collisions = []
        for collision_part_obj in context.selected_objects:
            collision_part_obj: bpy.types.MeshObject

            map_stem = get_collection_map_stem(collision_part_obj)

            collection = get_or_create_collection(
                context.scene.collection,
                f"{map_stem} MSB",
                f"{map_stem} Parts",
                f"{map_stem} Connect Collision Parts"
            )

            connect_collision_name = f"{collision_part_obj.name}_{tag}"

            bl_connect_collision = BlenderMSBConnectCollision.new(
                name=connect_collision_name,
                data=collision_part_obj.data,
                collection=collection,
            )
            bl_connect_collision.collision = collision_part_obj
            bl_connect_collision.model = collision_part_obj.MSB_PART.model
            bl_connect_collision.draw_groups = {self.connected_display_group}
            bl_connect_collision.display_groups = {self.connected_display_group}
            bl_connect_collision.connected_map_id = connected_map_id

            self.info(f"Created Connect Collision '{connect_collision_name}'.")
            bl_connect_collisions.append(bl_connect_collision)

        self.deselect_all()
        if bl_connect_collisions:
            for bl_connect_collision in bl_connect_collisions:
                bl_connect_collision.obj.select_set(True)
            context.view_layer.objects.active = bl_connect_collisions[0].obj

        getattr(bpy.ops.view3d, "view_selected_distance_zero")()

        return {"FINISHED"}


def _is_user_of_active_model(_, obj):
    return (
        bpy.context.active_object
        and obj.soulstruct_type == SoulstructType.MSB_PART
        and obj.MSB_PART.model == bpy.context.active_object
    )


class MSBFindPartsPointer(bpy.types.PropertyGroup):

    part: bpy.props.PointerProperty(
        name="Part",
        description="MSB Part that uses the active model object",
        type=bpy.types.Object,
        poll=_is_user_of_active_model,
    )


class FindMSBParts(LoggingOperator):

    bl_idname = "object.find_msb_parts"
    bl_label = "Go to MSB Part"
    bl_description = (
        "Select an MSB Part that uses the active model object, make it active, and frame it in 3D View if visible"
    )

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.active_object
            and context.active_object.soulstruct_type in {
                SoulstructType.FLVER, SoulstructType.COLLISION, SoulstructType.NAVMESH
            }
        )

    def invoke(self, context, event):
        """If only one Part exists, use that. Otherwise, offer list."""
        for obj in context.scene.objects:
            if obj.soulstruct_type == SoulstructType.MSB_PART and obj.MSB_PART.model == context.active_object:
                context.scene.find_msb_parts_pointer.part = obj
                return self.execute(context)
        # Draw props dialog.
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(context.scene.find_msb_parts_pointer, "part")

    def execute(self, context):
        part_obj = context.scene.find_msb_parts_pointer.part
        if not part_obj:
            return self.error("No MSB Part found that uses the active model object.")

        self.deselect_all()
        part_obj.select_set(True)
        context.view_layer.objects.active = part_obj
        getattr(bpy.ops.view3d, "view_selected_distance_zero")()
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
                if (
                    obj.soulstruct_type == SoulstructType.MSB_EVENT
                    and obj.MSB_EVENT.entry_subtype == tool_settings.event_color_type  # enums are same except for ALL
                )
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

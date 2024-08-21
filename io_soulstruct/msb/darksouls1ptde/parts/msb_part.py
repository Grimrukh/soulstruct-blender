from __future__ import annotations

__all__ = [
    "BlenderMSBPart",
]

import abc
import typing as tp

import bpy
from io_soulstruct.exceptions import *
from io_soulstruct.flver.models import BlenderFLVER
from io_soulstruct.msb.properties import MSBPartSubtype, MSBPartProps
from io_soulstruct.types import *
from io_soulstruct.types import SOULSTRUCT_T
from io_soulstruct.utilities import *
from soulstruct.base.maps.msb.utils import GroupBitSet128
from soulstruct.darksouls1ptde.maps.msb import MSBPart, MSBModel

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb import MSBEntry
    from soulstruct.darksouls1ptde.maps.msb import MSB


PART_T = tp.TypeVar("PART_T", bound=MSBPart)
SUBTYPE_PROPS_T = tp.TypeVar("SUBTYPE_PROPS_T", bound=bpy.types.PropertyGroup)


class BlenderMSBPart(SoulstructObject[MSBPart, MSBPartProps], tp.Generic[PART_T, SUBTYPE_PROPS_T]):
    """Mesh-only MSB Part instance of a FLVER model of the corresponding Part subtype (Map Piece, Character, etc.).

    FLVER model Armatures and Dummies are NOT instantiated for FLVER parts -- strictly Meshes (or Empties for Player
    Starts).
    """

    TYPE = SoulstructType.MSB_PART
    # OBJ_DATA_TYPE is subtype-dependent.
    SOULSTRUCT_CLASS: tp.ClassVar[type[MSBPart]]
    SOULSTRUCT_MODEL_CLASS: tp.ClassVar[type[MSBModel]]
    EXPORT_TIGHT_NAME: tp.ClassVar[bool] = True  # for MSB parts, we always use tight names
    PART_SUBTYPE: tp.ClassVar[MSBPartSubtype]
    MODEL_SUBTYPES: tp.ClassVar[list[str]]  # for `MSB` model search on export
    MODEL_USES_LATEST_MAP: tp.ClassVar[bool] = False  # which map version folder to look for model in

    __slots__ = []
    obj: bpy.types.MeshObject
    # All Parts are Meshes.
    data: bpy.types.Mesh

    AUTO_PART_PROPS: tp.ClassVar[list[str]] = [
        "entity_id",
        "ambient_light_id",
        "fog_id",
        "scattered_light_id",
        "lens_flare_id",
        "shadow_id",
        "dof_id",
        "tone_map_id",
        "point_light_id",
        "tone_correction_id",
        "lod_id",
        "is_shadow_source",
        "is_shadow_destination",
        "is_shadow_only",
        "draw_by_reflect_cam",
        "draw_only_reflect_cam",
        "use_depth_bias_float",
        "disable_point_light_effect",
    ]

    entity_id: int
    ambient_light_id: int
    fog_id: int
    scattered_light_id: int
    lens_flare_id: int
    shadow_id: int
    dof_id: int
    tone_map_id: int
    point_light_id: int
    tone_correction_id: int
    lod_id: int
    is_shadow_source: bool
    is_shadow_destination: bool
    is_shadow_only: bool
    draw_by_reflect_cam: bool
    draw_only_reflect_cam: bool
    use_depth_bias_float: bool
    disable_point_light_effect: bool

    @property
    def armature(self) -> bpy.types.ArmatureObject | None:
        """Detect parent Armature of wrapped Mesh object. Rarely present for Parts. Must be overridden to enable."""
        raise TypeError(f"MSB {self.PART_SUBTYPE} parts cannot have Armatures.")

    @property
    def subtype_properties(self) -> SUBTYPE_PROPS_T:
        return getattr(self.obj, self.PART_SUBTYPE)

    @property
    def model(self) -> bpy.types.MeshObject | None:
        return self.type_properties.model

    @model.setter
    def model(self, value: bpy.types.MeshObject | None):
        self.type_properties.model = value

    @staticmethod
    def _get_groups_bit_set(props: list[bpy.props.BoolVectorProperty]):
        groups = GroupBitSet128.all_off()
        for i in range(4):
            for j in range(32):
                if props[i][j]:
                    groups.add(i * 32 + j)
        return groups

    @staticmethod
    def _set_groups_bit_set(props: list[bpy.props.BoolVectorProperty], enabled_bits: set[int]):
        for i in range(4):
            for j in range(32):
                props[i][j] = (i * 32 + j) in enabled_bits

    @property
    def draw_groups(self) -> GroupBitSet128:
        return self._get_groups_bit_set(self.type_properties.get_draw_groups_props_128())

    @draw_groups.setter
    def draw_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.type_properties.get_draw_groups_props_128(), value)

    @property
    def display_groups(self) -> GroupBitSet128:
        return self._get_groups_bit_set(self.type_properties.get_display_groups_props_128())

    @display_groups.setter
    def display_groups(self, value: set[int] | GroupBitSet128):
        if isinstance(value, GroupBitSet128):
            value = value.enabled_bits
        self._set_groups_bit_set(self.type_properties.get_display_groups_props_128(), value)

    def set_bl_obj_transform(self, part: MSBPart):
        game_transform = Transform.from_msb_entry(part)
        self.obj.location = game_transform.bl_translate
        self.obj.rotation_euler = game_transform.bl_rotate
        self.obj.scale = game_transform.bl_scale

    def set_part_transform(self, part: MSBPart, use_world_transform=False):
        bl_transform = BlenderTransform.from_bl_obj(self.obj, use_world_transform)
        part.translate = bl_transform.game_translate
        part.rotate = bl_transform.game_rotate_deg
        part.scale = bl_transform.game_scale

    @staticmethod
    def entry_ref_to_bl_obj(
        operator: LoggingOperator,
        part: MSBPart,
        prop_name: str,
        ref_entry: MSBEntry | None,
        ref_soulstruct_type: SoulstructType,
        missing_collection_name="Missing MSB References",
    ) -> bpy.types.Object | None:
        if not ref_entry:
            return None

        was_missing, pointer_obj = find_obj_or_create_empty(
            ref_entry.name,
            find_stem=True,
            soulstruct_type=ref_soulstruct_type,
            missing_collection_name=missing_collection_name,
        )
        if was_missing:
            operator.warning(
                f"Referenced MSB entry '{ref_entry.name}' in field '{prop_name}' of MSB part '{part.name}' not "
                f"found in Blender data. Creating empty reference."
            )
        return pointer_obj

    @staticmethod
    def bl_obj_to_entry_ref(
        msb: MSB,
        prop_name: str,
        bl_obj: bpy.types.Object | None,
        part: MSBPart,
        entry_subtype: str = None
    ) -> MSBEntry | None:

        if not bl_obj:
            return None  # leave part field as `None`
        if entry_subtype:
            subtypes = (entry_subtype,)
        else:
            subtypes = ()

        try:
            if bl_obj.soulstruct_type == SoulstructType.MSB_PART:
                msb_entry = msb.find_part_name(get_bl_obj_tight_name(bl_obj), subtypes=subtypes)
            elif bl_obj.soulstruct_type == SoulstructType.MSB_REGION:
                msb_entry = msb.find_region_name(bl_obj.name, subtypes=subtypes)  # full name
            elif bl_obj.soulstruct_type == SoulstructType.MSB_EVENT:
                msb_entry = msb.find_event_name(bl_obj.name, subtypes=subtypes)  # full name
            else:
                raise SoulstructTypeError(f"Blender object '{bl_obj.name}' is not an MSB Part, Region, or Event.")
            return msb_entry
        except KeyError:
            raise MissingMSBEntryError(
                f"MSB entry '{bl_obj.name}' referenced in field '{prop_name}' of part '{part.name}' "
                f"not found in MSB."
            )

    @classmethod
    def model_ref_to_bl_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        part: MSBPart,
        map_stem: str,
        try_import_model: bool,
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject | None:
        """Similar to resolving entry reference, but we have the ability to import models if requested."""

        if not part.model:
            operator.warning(f"MSB Part '{part.name}' has no model set in the MSB.")
            return None

        model_name = part.model.get_model_file_stem(map_stem)
        return cls.find_or_import_model_mesh(
            operator, context, model_name, map_stem, try_import_model, model_collection
        )

    def set_msb_model(
        self,
        operator: LoggingOperator,
        msb: MSB,
        part: MSBPart,
        map_stem: str,
    ) -> None:
        """Detect `model` name and call `msb.auto_model()` to find or create the MSB model entry of matching subtype.

        Model is assigned to `part` automatically and is not returned here.
        """

        if not self.model:
            operator.warning(f"MSB Part '{part.name}' has no model set in Blender.")
            return None  # leave part field as `None`

        # We use the `MSBModel` subclass to determine what name to look for.
        msb_model_name = self.SOULSTRUCT_MODEL_CLASS.model_file_stem_to_model_name(get_bl_obj_tight_name(self.model))
        msb.auto_model(part, msb_model_name, map_stem)

    @classmethod
    def batch_import_models(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        parts: list[PART_T],
        map_stem: str,
    ):
        """Import all models for a batch of MSB Parts, as needed, in parallel as much as possible.

        Not available by defailt.
        """
        raise BatchOperationUnsupportedError(f"Cannot batch import MSB Part subtype: {cls.PART_SUBTYPE}")

    @classmethod
    def new(
        cls,
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        bl_part = super().new(name, data, collection)  # type: tp.Self
        bl_part.obj.MSB_PART.part_subtype = cls.PART_SUBTYPE
        return bl_part

    @classmethod
    def find_or_import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # not required by all subtypes
        try_import_model: bool,
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Find or create actual Blender model mesh. Not necessarily a FLVER mesh!"""
        try:
            return cls.find_model_mesh(model_name, map_stem)
        except MissingPartModelError:
            if try_import_model:
                model = cls.import_model_mesh(operator, context, model_name, map_stem, model_collection)
            else:
                # Find any Mesh object with model's name and MSB_MODEL_PLACEHOLDER property, or create empty icosphere.
                try:
                    model = bpy.data.objects[model_name]
                    if not model.get("MSB_MODEL_PLACEHOLDER"):
                        raise KeyError
                except KeyError:
                    # Create PLACEHOLDER icosphere.
                    mesh = bpy.data.meshes.new(model_name)
                    cls.primitive_icosphere(mesh)
                    model = bpy.data.objects.new(model_name, mesh)
                    model["MSB_MODEL_PLACEHOLDER"] = True  # some models are genuinely empty, so we need a way to tell
                    placeholder_model_collection = get_or_create_collection(
                        context.scene.collection,
                        "Placeholder Models",
                        hide_viewport=context.scene.msb_import_settings.hide_model_collections,
                    )
                    placeholder_model_collection.objects.link(model)
            return model

    @classmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: PART_T,
        name: str,
        collection: bpy.types.Collection = None,
        map_stem="",
        try_import_model=True,
        model_collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Create a fully-represented MSB Part linked to a source model in Blender.

        Subclasses will override this to set additional Part-specific properties, or even a Part Armature if needed for
        those annoying old Map Pieces with "pre-posed vertices".
        """
        model = cls.model_ref_to_bl_obj(
            operator, context, soulstruct_obj, map_stem, try_import_model, model_collection
        )
        model_mesh = model.data if model else bpy.data.meshes.new(name)
        bl_part = cls.new(name, model_mesh, collection)  # type: tp.Self
        bl_part.set_bl_obj_transform(soulstruct_obj)
        bl_part.model = model
        bl_part.draw_groups = soulstruct_obj.draw_groups
        bl_part.display_groups = soulstruct_obj.display_groups
        for name in cls.AUTO_PART_PROPS:
            setattr(bl_part, name, getattr(soulstruct_obj, name))

        return bl_part

    def duplicate_flver_model_armature(self, context: bpy.types.Context):
        """Duplicate FLVER model's Armature parent to being the parent of this part Mesh.

        Only works for FLVER-based Parts, obviously (Map Pieces, Objects, Assets, Characters). Those classes will also
        expose an `armature` property to retrieve the Mesh parent.

        If the model parent does not have an Armature, the implicit default one will be created for the Part, though
        this is unlikely to be useful for such models (i.e., static Map Pieces).
        """
        if not self.model:
            raise ValueError("Cannot duplicate model armature for MSB Part without a model.")
        if not self.model.soulstruct_type == SoulstructType.FLVER:
            raise TypeError(f"MSB {self.PART_SUBTYPE} parts do not have FLVER model armatures to duplicate.")
        bl_flver = BlenderFLVER(self.model)
        if not bl_flver.armature:
            # This FLVER model doesn't have an Armature, implying the FLVER has only one default bone. We create that
            # for this Part, without assigning it to the FLVER.
            BlenderFLVER.create_default_armature_parent(context, self.export_name, self.obj)
        else:
            # Duplicate model's Armature. This handles parenting, rigging, etc. We only copy pose for Map Pieces.
            bl_flver.duplicate_armature(context, self.obj, copy_pose=self.PART_SUBTYPE == MSBPartSubtype.MapPiece)
            # Rename new modifier for clarity.
            self.obj.modifiers["FLVER Armature"].name = "Part Armature"

    def _create_soulstruct_obj(self) -> SOULSTRUCT_T:
        """Create a new MSB Part instance of the appropriate subtype. Args are supplied automatically."""
        # noinspection PyArgumentList
        return self.SOULSTRUCT_CLASS(name=self.export_name)

    def to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        map_stem="",
        msb: MSB = None,
    ) -> PART_T:
        if msb is None:
            raise ValueError("MSB must be provided to resolve Blender MSB references into real MSB entries.")

        # Creation can be overridden (e.g. to make 'Dummy' versions of entry types).
        part = self._create_soulstruct_obj()  # type: PART_T

        part.set_auto_sib_path(map_stem)
        use_world_transform = context.scene.msb_export_settings.use_world_transforms
        self.set_part_transform(part, use_world_transform=use_world_transform)
        self.set_msb_model(operator, msb, part, map_stem)
        part.draw_groups = self.draw_groups
        part.display_groups = self.display_groups
        for name in self.AUTO_PART_PROPS:
            setattr(part, name, getattr(self, name))

        return part

    @classmethod
    @abc.abstractmethod
    def find_model_mesh(
        cls,
        model_name: str,
        map_stem: str,  # not required by all subtypes
    ) -> bpy.types.MeshObject:
        """Find the given model in the current scene. Used on Blender Part creation to avoid re-importing models.

        Should raise `MissingPartModelError` if not found.
        """

    @classmethod
    @abc.abstractmethod
    def import_model_mesh(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        model_name: str,
        map_stem: str,  # not required by all subtypes
        model_collection: bpy.types.Collection = None,
    ) -> bpy.types.MeshObject:
        """Use other Soulstruct for Blender submodules to import model for this MSB Part."""

    @classmethod
    def add_auto_subtype_props(cls, *names):
        for prop_name in names:
            # `prop_name` must be baked in to each closure!
            setattr(
                cls, prop_name, property(
                    lambda self, pn=prop_name: getattr(self.subtype_properties, pn),
                    lambda self, value, pn=prop_name: setattr(self.subtype_properties, pn, value),
                )
            )

    @staticmethod
    def primitive_icosphere(mesh: bpy.types.Mesh):
        """Used as a dummy mesh for non-imported Part models."""
        vertices = [
            (0.0000, 0.0000, -1.0000),
            (0.7236, -0.5257, -0.4472),
            (-0.2764, -0.8506, -0.4472),
            (-0.8944, 0.0000, -0.4472),
            (-0.2764, 0.8506, -0.4472),
            (0.7236, 0.5257, -0.4472),
            (0.2764, -0.8506, 0.4472),
            (-0.7236, -0.5257, 0.4472),
            (-0.7236, 0.5257, 0.4472),
            (0.2764, 0.8506, 0.4472),
            (0.8944, 0.0000, 0.4472),
            (0.0000, 0.0000, 1.0000),
        ]
        faces = [
            (0, 1, 2),
            (1, 0, 5),
            (0, 2, 3),
            (0, 3, 4),
            (0, 4, 5),
            (1, 5, 10),
            (2, 1, 6),
            (3, 2, 7),
            (4, 3, 8),
            (5, 4, 9),
            (1, 10, 6),
            (2, 6, 7),
            (3, 7, 8),
            (4, 8, 9),
            (5, 9, 10),
            (6, 10, 11),
            (7, 6, 11),
            (8, 7, 11),
            (9, 8, 11),
            (10, 9, 11),
        ]
        mesh.clear_geometry()
        mesh.from_pydata(vertices, [], faces)
        mesh.update()


BlenderMSBPart.add_auto_type_props(*BlenderMSBPart.AUTO_PART_PROPS)
# Subtype props added by subclasses.

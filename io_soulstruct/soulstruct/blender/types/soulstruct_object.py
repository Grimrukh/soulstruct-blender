from __future__ import annotations

__all__ = [
    "BaseBlenderSoulstructObject",
    "SOULSTRUCT_T",
    "TYPE_PROPS_T",
]

import abc
import typing as tp

import bpy
from mathutils import Vector, Euler

from soulstruct.utilities.text import natural_keys

from soulstruct.blender.exceptions import SoulstructTypeError
from soulstruct.blender.utilities import LoggingOperator, remove_dupe_suffix
from soulstruct.blender.utilities.bpy_data import copy_obj_property_group
from soulstruct.blender.utilities.bpy_types import ObjectType, SoulstructType

from .field_adapters import FieldAdapter


SOULSTRUCT_T = tp.TypeVar("SOULSTRUCT_T", bound=object)  # does not have to be a `GameFile` (e.g. `MSBMapPiece`)
TYPE_PROPS_T = tp.TypeVar("TYPE_PROPS_T", bound=bpy.types.PropertyGroup)  # corresponding to `SOULSTRUCT_T`

# TODO: Workaround for PyCharm `tp.Self` bug with generic classes. Needed even when IDE doesn't explicitly complain.
SELF_T = tp.TypeVar("SELF_T", bound="BaseBlenderSoulstructObject")


class BaseBlenderSoulstructObject(abc.ABC, tp.Generic[SOULSTRUCT_T, TYPE_PROPS_T]):
    """Base class for Blender objects wrapped with implicit Soulstruct 'types'."""

    __slots__ = ["obj"]

    TYPE: tp.ClassVar[SoulstructType]
    BL_OBJ_TYPE: tp.ClassVar[ObjectType]
    SOULSTRUCT_CLASS: tp.ClassVar[type]
    TYPE_FIELDS: tp.ClassVar[tuple[FieldAdapter, ...]]
    SUBTYPE_FIELDS: tp.ClassVar[tuple[FieldAdapter, ...]] = ()  # optional, for subclasses with subtypes

    obj: bpy.types.Object

    def __init__(self, obj: bpy.types.Object):
        if obj.soulstruct_type != self.TYPE:
            raise SoulstructTypeError(f"Object '{obj.name}' is not a {self.TYPE} Soulstruct object.")
        if obj.type != self.BL_OBJ_TYPE:
            raise SoulstructTypeError(f"Object '{obj.name}' is not a {self.BL_OBJ_TYPE} Blender object.")
        self.obj = obj

    # region Object Import/Creation Methods

    @classmethod
    def new(
        cls: type[SELF_T],
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> SELF_T:
        """Create a default instance of this Blender/Soulstruct object type.

        `type_properties` property values will use their defaults in the Blender property group.
        """
        match cls.BL_OBJ_TYPE:
            case ObjectType.EMPTY:
                if data is not None:
                    raise SoulstructTypeError(f"Cannot create an EMPTY object with data.")
                obj = bpy.data.objects.new(name, None)
            case ObjectType.MESH:
                # NOT permitted to be initialized as Empty.
                if not isinstance(data, bpy.types.Mesh):
                    raise SoulstructTypeError(f"Data for MESH object must be a Mesh, not {type(data).__name__}.")
                obj = bpy.data.objects.new(name, data)
            case _:
                raise SoulstructTypeError(f"Unsupported Soulstruct BL_OBJ_TYPE '{cls.BL_OBJ_TYPE}'.")
        obj.soulstruct_type = cls.TYPE
        (collection or bpy.context.scene.collection).objects.link(obj)
        return cls(obj)

    @classmethod
    def new_from_soulstruct_obj(
        cls: type[SELF_T],
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
        name: str,
        collection: bpy.types.Collection = None,
    ) -> SELF_T:
        """Create a new Blender object from Soulstruct object.

        Operator and context are both required for logging, global settings, and context management.

        Calls all `TYPE_FIELDS` adapters by default, and does nothing more. Subclasses may need to override this if they
        cannot rely on the adapters alone (e.g. resolving references to other Soulstruct/Blender objects).
        """
        if not isinstance(soulstruct_obj, cls.SOULSTRUCT_CLASS):
            raise TypeError(
                f"Given `soulstruct_obj` is not of type {cls.SOULSTRUCT_CLASS.__name__}: {soulstruct_obj.cls_name}"
            )
        bl_obj = cls.new(name, data=None, collection=collection)
        bl_obj._read_props_from_soulstruct_obj(operator, context, soulstruct_obj)
        bl_obj._post_new_from_soulstruct_obj(operator, context, soulstruct_obj)
        return bl_obj

    def _read_props_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
    ):
        """Use class `TYPE_FIELDS` adapters to convert Soulstruct field values to Blender property values."""
        for field in self.TYPE_FIELDS:
            field.soulstruct_to_blender(operator, context, soulstruct_obj, self)

    def _post_new_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
    ):
        """Optional additional processing on a Blender object after it has been created from a Soulstruct object,
        without the hassle of having to override the entire `new_from_soulstruct_obj` method."""
        pass

    # endregion

    # region Object Export Methods

    def to_soulstruct_obj(self, operator: LoggingOperator, context: bpy.types.Context) -> SOULSTRUCT_T:
        """Create a new Soulstruct type of appropriate subclass from this Blender object.

        By default, we just process `TYPE_FIELDS`.
        """
        soulstruct_obj = self._create_soulstruct_obj()
        self._write_props_to_soulstruct_obj(operator, context, soulstruct_obj)
        return soulstruct_obj

    def _create_soulstruct_obj(self, *args, **kwargs) -> SOULSTRUCT_T:
        """By default, will pass args and kwargs into Soulstruct class. Note that subtypes may supply their own args."""
        return self.SOULSTRUCT_CLASS(*args, **kwargs)

    def _write_props_to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
    ):
        """By default, we just process all `TYPE_FIELDS`."""
        for field in self.TYPE_FIELDS:
            field.blender_to_soulstruct(operator, context, self, soulstruct_obj)

    # endregion

    # region Properties

    @property
    def data(self) -> bpy.types.ID:
        """NOTE: Subclasses define wrapper properties such as `mesh` or `armature` when data type is known/enforced."""
        return self.obj.data

    @property
    def type_properties(self) -> TYPE_PROPS_T:
        """Properties of corresponding `SoulstructType` in Blender.

        Subclasses may wrap (and properties dispatch to) additional 'subtype' properties.
        """
        return getattr(self.obj, self.TYPE)

    @property
    def name(self):
        return self.obj.name

    @name.setter
    def name(self, value: str):
        self.obj.name = value

    @property
    def game_name(self) -> str:
        """Just removes Blender dupe suffix by default (if present), but subclasses may be more aggressive.

        Model types, for example, will finish at the first space or periods (as will MSB Parts).
        """
        return remove_dupe_suffix(self.obj.name).strip()

    @property
    def parent(self) -> bpy.types.Object | None:
        return self.obj.parent

    @parent.setter
    def parent(self, value: bpy.types.Object | None):
        self.obj.parent = value

    @property
    def location(self) -> Vector:
        return self.obj.location

    @location.setter
    def location(self, value: Vector):
        self.obj.location = value

    @property
    def rotation_euler(self) -> Euler:
        return self.obj.rotation_euler

    @rotation_euler.setter
    def rotation_euler(self, value: Euler):
        self.obj.rotation_euler = value

    @property
    def scale(self) -> Vector:
        return self.obj.scale

    @scale.setter
    def scale(self, value: Vector):
        self.obj.scale = value

    def copy_type_properties_from(
        self,
        source_obj: bpy.types.Object | BaseBlenderSoulstructObject,
        filter_func: tp.Callable[[str], bool] | None = None,
    ):
        """Use annotations of to copy properties to `self.properties`."""
        if isinstance(source_obj, BaseBlenderSoulstructObject):
            source_obj = source_obj.obj
        if source_obj.soulstruct_type != self.TYPE:
            raise SoulstructTypeError(f"Source object '{source_obj.name}' is not a {self.TYPE} Soulstruct object.")
        copy_obj_property_group(source_obj, self.obj, self.TYPE, filter_func=filter_func)

    def copy_type_properties_to(
        self,
        dest_obj: bpy.types.Object | BaseBlenderSoulstructObject,
        filter_func: tp.Callable[[str], bool] | None = None,
    ):
        """Use annotations to copy properties to `dest_obj`."""
        if isinstance(dest_obj, BaseBlenderSoulstructObject):
            dest_obj = dest_obj.obj
        if dest_obj.soulstruct_type != self.TYPE:
            raise SoulstructTypeError(f"Dest object '{dest_obj.name}' is not a {self.TYPE} Soulstruct object.")
        copy_obj_property_group(self.obj, dest_obj, self.TYPE, filter_func=filter_func)

    # endregion

    # region Dunder Methods

    def __getitem__(self, item: str):
        """Wraps Blender object custom properties."""
        return self.obj.__getitem__(item)

    def __setitem__(self, item: str, value: tp.Any):
        """Wraps Blender object custom properties."""
        self.obj.__setitem__(item, value)

    # endregion

    # region Utility Class Methods

    @classmethod
    def is_obj_type(cls, obj: bpy.types.Object) -> bool:
        """Tries to load this Blender `obj` as this `cls`. Returns `False` if it fails."""
        if not obj:
            return False
        try:
            cls(obj)
        except SoulstructTypeError:
            return False
        return True

    @classmethod
    def is_active_obj_type(cls, context: bpy.types.Context) -> bool:
        """Tries to load the active object as this `cls`. Returns `False` if it fails."""
        return cls.is_obj_type(context.active_object)

    @classmethod
    def find_in_data(cls: type[SELF_T], name: str, only_in_collections: list[bpy.types.Collection]) -> SELF_T:
        # TODO: Should be able to provide a name-matching callback, e.g. `get_part_game_name`.
        try:
            obj = bpy.data.objects[name]
        except KeyError:
            raise KeyError(f"No Blender object named '{name}' found.")
        if only_in_collections:
            for collection in obj.users_collection:
                if collection in only_in_collections:
                    break
            else:
                raise ValueError(f"Blender object '{name}' is not in any of the specified collections.")
        if obj.soulstruct_type != cls.TYPE:
            raise SoulstructTypeError(
                f"Found Blender object '{name}', but it is not a {cls.TYPE} Soulstruct object."
            )
        return cls(obj)

    @classmethod
    def from_active_object(cls: type[SELF_T], context: bpy.types.Context) -> SELF_T:
        obj = context.active_object
        if obj is None:
            raise SoulstructTypeError(f"No active object to become a {cls.TYPE} Soulstruct object.")
        if obj.soulstruct_type != cls.TYPE:
            raise SoulstructTypeError(f"Active object '{obj}' is not a {cls.TYPE} Soulstruct object.")
        return cls(obj)

    @classmethod
    def from_selected_object(cls: type[SELF_T], context: bpy.types.Context) -> SELF_T:
        if not context.selected_objects:
            raise SoulstructTypeError(f"No selected object to become a {cls.TYPE} Soulstruct object.")
        if len(context.selected_objects) > 1:
            raise SoulstructTypeError(f"More than one object selected; expected only one.")
        obj = context.selected_objects[0]
        if obj.soulstruct_type != cls.TYPE:
            raise SoulstructTypeError(f"Selected object '{obj}' is not a {cls.TYPE} Soulstruct object.")
        return cls(obj)

    @classmethod
    def from_selected_objects(
        cls: type[SELF_T],
        context: bpy.types.Context,
        sort=True,
    ) -> list[SELF_T]:
        if not context.selected_objects:
            raise SoulstructTypeError(f"No selected objects to become {cls.TYPE} Soulstruct objects.")
        selfs = []
        for obj in context.selected_objects:
            if obj.soulstruct_type != cls.TYPE:
                raise SoulstructTypeError(f"Selected object '{obj}' is not a {cls.TYPE} Soulstruct object.")
            selfs.append(cls(obj))
        if sort:  # sort by Blender name to match Outliner order
            selfs = sorted(selfs, key=lambda o: natural_keys(o.obj.name))
        return selfs

    @classmethod
    def from_collection_objects(
        cls, collection: bpy.types.Collection, sort_alphabetical=True
    ) -> list[tp.Self]:
        """NOTE: ALL objects in collection must be of given type. Not recursive.

        Raises a ValueError if there are no objects of this type in the collection.
        """
        selfs = []
        objects = sorted(collection.objects, key=lambda o: o.name) if sort_alphabetical else collection.objects
        for obj in objects:
            if obj.soulstruct_type != cls.TYPE:
                raise SoulstructTypeError(f"Object '{obj}' in collection is not a {cls.TYPE} Soulstruct object.")
            selfs.append(cls(obj))
        if not selfs:
            raise SoulstructTypeError(f"No {cls.TYPE} objects found in collection '{collection.name}'.")
        return selfs

    # endregion

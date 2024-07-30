from __future__ import annotations

__all__ = [
    "SoulstructType",
    "SoulstructDataType",
    "SoulstructObject",
]

import abc
import typing as tp

import bpy
from mathutils import Vector, Euler
from soulstruct.utilities.future import StrEnum
from .exceptions import SoulstructTypeError

if tp.TYPE_CHECKING:
    from io_soulstruct.utilities import LoggingOperator, copy_obj_property_group


class SoulstructType(StrEnum):
    """Set on Blender `Object` instances to indicate what kind of Soulstruct 'subtype' they represent.

    Matches the name of `PropertyGroup` direct properties on `Object` as well (except "NONE").
    """
    NONE = "NONE"  # default; not a Soulstruct object

    FLVER = "FLVER"
    FLVER_DUMMY = "FLVER_DUMMY"

    COLLISION = "COLLISION"

    NAVMESH = "NAVMESH"
    NVM_EVENT_ENTITY = "NVM_EVENT_ENTITY"
    MCG = "MCG"
    MCG_NODE = "MCG_NODE"
    MCG_EDGE = "MCG_EDGE"

    MSB_PART = "MSB_PART"
    MSB_REGION = "MSB_REGION"
    MSB_EVENT = "MSB_EVENT"


class SoulstructDataType(StrEnum):
    """Only two types of Soulstruct data are supported for now."""
    EMPTY = "EMPTY"
    MESH = "MESH"


SOULSTRUCT_T = tp.TypeVar("SOULSTRUCT_T", bound=object)  # does not have to be a `GameFile` (e.g. `MSBMapPiece`)
SOULSTRUCT_PROPS_T = tp.TypeVar("SOULSTRUCT_PROPS_T", bound=bpy.types.PropertyGroup)  # corresponding to `SOULSTRUCT_T`


class SoulstructObject(abc.ABC, tp.Generic[SOULSTRUCT_T, SOULSTRUCT_PROPS_T]):
    """Base class for Blender objects wrapped with implicit Soulstruct 'types'."""

    __slots__ = ["obj"]

    TYPE: tp.ClassVar[SoulstructType]
    OBJ_DATA_TYPE: tp.ClassVar[SoulstructDataType]
    SOULSTRUCT_CLASS: tp.ClassVar[type]

    # Subclasses may define their own further type hierarchies, like `SUBTYPE_NAME`.

    obj: bpy.types.Object

    # Subclasses will wrap all properties with their own instance attributes. Properties will be copied between objects
    # (import) and real `GameFile` instances (export) by matching up all fields of `GameFile` (which is a dataclass) and
    # all annotations here (not a dataclass), except for `obj`.

    def __init__(self, obj: bpy.types.Object):
        if obj.soulstruct_type != self.TYPE:
            raise SoulstructTypeError(f"Object '{obj.name}' is not a {self.TYPE} Soulstruct object.")
        if obj.type != self.OBJ_DATA_TYPE:
            raise SoulstructTypeError(f"Object '{obj.name}' is not a {self.OBJ_DATA_TYPE} Blender object.")
        self.obj = obj

    @property
    def data(self) -> bpy.types.ID:
        return self.obj.data

    @classmethod
    def new(
        cls,
        name: str,
        data: bpy.types.Mesh | None,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        match cls.OBJ_DATA_TYPE:
            case SoulstructDataType.EMPTY:
                if data is not None:
                    raise SoulstructTypeError(f"Cannot create an EMPTY object with data.")
                obj = bpy.data.objects.new(name, None)
            case SoulstructDataType.MESH:
                # NOT permitted to be initialized as Empty.
                if not isinstance(data, bpy.types.Mesh):
                    raise SoulstructTypeError(f"Data for MESH object must be a Mesh, not {type(data).__name__}.")
                obj = bpy.data.objects.new(name, data)
            case _:
                raise SoulstructTypeError(f"Unsupported Soulstruct OBJ_DATA_TYPE '{cls.OBJ_DATA_TYPE}'.")
        obj.soulstruct_type = cls.TYPE
        (collection or bpy.context.scene.collection).objects.link(obj)
        return cls(obj)

    @classmethod
    @abc.abstractmethod
    def new_from_soulstruct_obj(
        cls,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
        name: str,
        collection: bpy.types.Collection = None,
    ) -> tp.Self:
        """Create a new Blender object from Soulstruct object.

        Operator and context are both required for logging, global settings, and context management.

        Subclasses must override this to transfer properties.
        """
        if not isinstance(soulstruct_obj, cls.SOULSTRUCT_CLASS):
            raise TypeError(
                f"Given `soulstruct_obj` is not of type {cls.SOULSTRUCT_CLASS.__name__}: {soulstruct_obj.cls_name}"
            )
        return cls.new(name, data=None, collection=collection)  # type: tp.Self

    @classmethod
    def find_in_data(cls, name: str) -> tp.Self:
        try:
            obj = bpy.data.objects[name]
        except KeyError:
            raise KeyError(f"No Blender object named '{name}' found.")
        if obj.soulstruct_type != cls.TYPE:
            raise SoulstructTypeError(f"Found Blender object '{name}', but it is not a {cls.TYPE} Soulstruct object.")
        return cls(obj)

    def create_soulstruct_obj(self, *args, **kwargs) -> SOULSTRUCT_T:
        return self.SOULSTRUCT_CLASS(*args, **kwargs)

    @abc.abstractmethod
    def to_soulstruct_obj(self, operator: LoggingOperator, context: bpy.types.Context) -> SOULSTRUCT_T:
        """Create a new Soulstruct type of appropriate subclass from this Blender object."""

    @property
    def type_properties(self) -> SOULSTRUCT_PROPS_T:
        """Properties of 'supertype'. Subclasses may have additional 'subtype' properties."""
        return getattr(self.obj, self.TYPE)

    def copy_type_properties_from(self, source_obj: bpy.types.Object | SoulstructObject):
        """Use annotations of to copy properties to `self.properties`."""
        if isinstance(source_obj, SoulstructObject):
            source_obj = source_obj.obj
        if source_obj.soulstruct_type != self.TYPE:
            raise SoulstructTypeError(f"Source object '{source_obj.name}' is not a {self.TYPE} Soulstruct object.")
        copy_obj_property_group(source_obj, self.obj, self.TYPE)

    def copy_type_properties_to(self, dest_obj: bpy.types.Object | SoulstructObject):
        """Use annotations to copy properties to `dest_obj`."""
        if isinstance(dest_obj, SoulstructObject):
            dest_obj = dest_obj.obj
        if dest_obj.soulstruct_type != self.TYPE:
            raise SoulstructTypeError(f"Dest object '{dest_obj.name}' is not a {self.TYPE} Soulstruct object.")
        copy_obj_property_group(self.obj, dest_obj, self.TYPE)

    @property
    def name(self):
        return self.obj.name

    @name.setter
    def name(self, value: str):
        self.obj.name = value

    @property
    def tight_name(self):
        """Get the name of the object before the first space and/or dot. Used when exporting some game types."""
        return self.name.split(".")[0].split(" ")[0]

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

    def __getitem__(self, item: str):
        """Wraps Blender object custom properties."""
        return self.obj.__getitem__(item)

    def __setitem__(self, key: str, value: tp.Any):
        """Wraps Blender object custom properties."""
        self.obj.__setitem__(key, value)

    @classmethod
    def from_active_object(cls, context: bpy.types.Context) -> tp.Self:
        obj = context.active_object
        if obj is None:
            raise SoulstructTypeError(f"No active object to become a {cls.TYPE} Soulstruct object.")
        if obj.soulstruct_type != cls.TYPE:
            raise SoulstructTypeError(f"Active object '{obj}' is not a {cls.TYPE} Soulstruct object.")
        return cls(obj)

    @classmethod
    def from_selected_object(cls, context: bpy.types.Context) -> tp.Self:
        if not context.selected_objects:
            raise SoulstructTypeError(f"No selected object to become a {cls.TYPE} Soulstruct object.")
        if len(context.selected_objects) > 1:
            raise SoulstructTypeError(f"More than one object selected; expected only one.")
        obj = context.selected_objects[0]
        if obj.soulstruct_type != cls.TYPE:
            raise SoulstructTypeError(f"Selected object '{obj}' is not a {cls.TYPE} Soulstruct object.")
        return cls(obj)

    @classmethod
    def from_selected_objects(cls, context: bpy.types.Context) -> list[tp.Self]:
        if not context.selected_objects:
            raise SoulstructTypeError(f"No selected objects to become {cls.TYPE} Soulstruct objects.")
        selfs = []
        for obj in context.selected_objects:
            if obj.soulstruct_type != cls.TYPE:
                raise SoulstructTypeError(f"Selected object '{obj}' is not a {cls.TYPE} Soulstruct object.")
            selfs.append(cls(obj))
        return selfs

    @classmethod
    def from_collection_objects(cls, collection: bpy.types.Collection) -> list[tp.Self]:
        """NOTE: ALL objects in collection must be of given type. Not recursive."""
        selfs = []
        for obj in collection.objects:
            if obj.soulstruct_type != cls.TYPE:
                raise SoulstructTypeError(f"Object '{obj}' in collection is not a {cls.TYPE} Soulstruct object.")
            selfs.append(cls(obj))
        if not selfs:
            raise SoulstructTypeError(f"No {cls.TYPE} objects found in collection '{collection.name}'.")
        return selfs

    @classmethod
    def add_auto_type_props(cls, *names):
        for prop_name in names:
            setattr(
                cls, prop_name, property(
                    lambda self, pn=prop_name: getattr(self.type_properties, pn),
                    lambda self, value, pn=prop_name: setattr(self.type_properties, pn, value),
                )
            )

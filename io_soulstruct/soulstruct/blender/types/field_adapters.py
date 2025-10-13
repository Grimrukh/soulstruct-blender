from __future__ import annotations

__all__ = [
    "FieldAdapter",
    "CustomFieldAdapter",
    "SpatialVectorFieldAdapter",
    "EulerAnglesFieldAdapter",
    "soulstruct_adapter",
]

import typing as tp
from dataclasses import dataclass, KW_ONLY

import bpy

from soulstruct.utilities.maths import EulerDeg

from soulstruct.blender.utilities.operators import LoggingOperator
from soulstruct.blender.utilities.conversion import *

if tp.TYPE_CHECKING:
    from .soulstruct_object import BaseBlenderSoulstructObject, SOULSTRUCT_T, TYPE_PROPS_T
    SOULSTRUCT_OBJECT_T = tp.TypeVar("SOULSTRUCT_OBJECT_T", bound=BaseBlenderSoulstructObject)


@dataclass(slots=True, frozen=True)
class FieldAdapter:
    soulstruct_field_name: str
    _: KW_ONLY
    bl_prop_name: str = None  # defaults to `soulstruct_field_name`
    auto_prop: bool = True  # create `type_properties` wrapper property (getter/setter) after class creation

    def __post_init__(self):
        if self.bl_prop_name is None:
            object.__setattr__(self, "bl_prop_name", self.soulstruct_field_name)

    def soulstruct_to_blender(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
    ):
        """Convert a property from Soulstruct to Blender's wrapper.

        Base method does not use `operator` or `context`, but subclasses may do so.
        """
        bl_value = getattr(soulstruct_obj, self.soulstruct_field_name)
        setattr(bl_obj, self.bl_prop_name, bl_value)

    def blender_to_soulstruct(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
        soulstruct_obj: SOULSTRUCT_T,
    ):
        """Convert a property from Blender's wrapper to Soulstruct.

        Base method does not use `operator` or `context`, but subclasses may do so.
        """
        soulstruct_value = getattr(bl_obj, self.bl_prop_name)
        setattr(soulstruct_obj, self.soulstruct_field_name, soulstruct_value)

    def getter(self, bl_obj: BaseBlenderSoulstructObject, is_subtype=False) -> tp.Any:
        """Inherently supports use of subtype properties rather than type properties."""
        props = getattr(bl_obj, "subtype_properties" if is_subtype else "type_properties")
        return getattr(props, self.bl_prop_name)

    def setter(self, bl_obj: BaseBlenderSoulstructObject, value: tp.Any, is_subtype=False) -> None:
        """Inherently supports use of subtype properties rather than type properties."""
        props = getattr(bl_obj, "subtype_properties" if is_subtype else "type_properties")
        setattr(props, self.bl_prop_name, value)


@dataclass(slots=True, frozen=True)
class CustomFieldAdapter(FieldAdapter):
    """Simple extension that modifies the `getattr` values (in both directions) before setting them.

    NOTE: Property getter/setter are unchanged. The read/write functions are only used on import and export of
    the corresponding Soulstruct type. If the `BaseBlenderSoulstructObject` wrapper's property type differs from its
    underlying property group, then you should set `auto_prop=False` and define the appropriate property on the
    `BaseBlenderSoulstructObject`.
    """
    _: KW_ONLY
    read_func: tp.Callable[[tp.Any], tp.Any] = None  # converts Soulstruct value to Blender value
    write_func: tp.Callable[[tp.Any], tp.Any] = None  # converts Blender value to Soulstruct value

    def __post_init__(self):
        super(CustomFieldAdapter, self).__post_init__()
        if self.read_func is None:
            object.__setattr__(self, "read_func", lambda x: x)
        if self.write_func is None:
            object.__setattr__(self, "write_func", lambda x: x)

    def soulstruct_to_blender(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
    ):
        bl_value = self.read_func(getattr(soulstruct_obj, self.soulstruct_field_name))
        setattr(bl_obj, self.bl_prop_name, bl_value)

    def blender_to_soulstruct(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
        soulstruct_obj: SOULSTRUCT_T,
    ):
        soulstruct_value = self.write_func(getattr(bl_obj, self.bl_prop_name))
        setattr(soulstruct_obj, self.soulstruct_field_name, soulstruct_value)


@dataclass(slots=True, frozen=True)
class SpatialVectorFieldAdapter(FieldAdapter):
    """Convert spatial vector (e.g. translate/scale) between Blender and Soulstruct coordinates."""

    def soulstruct_to_blender(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
    ):
        bl_value = to_blender(getattr(soulstruct_obj, self.soulstruct_field_name))
        setattr(bl_obj, self.bl_prop_name, bl_value)

    def blender_to_soulstruct(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
        soulstruct_obj: SOULSTRUCT_T,
    ):
        soulstruct_value = to_game(getattr(bl_obj, self.bl_prop_name))
        setattr(soulstruct_obj, self.soulstruct_field_name, soulstruct_value)


@dataclass(slots=True, frozen=True)
class EulerAnglesFieldAdapter(FieldAdapter):
    """Convert Euler rotation angles between Blender (radians) and Soulstruct (degrees)."""

    def soulstruct_to_blender(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: SOULSTRUCT_T,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
    ):
        game_euler_deg = getattr(soulstruct_obj, self.soulstruct_field_name)
        if not isinstance(game_euler_deg, EulerDeg):
            raise TypeError(f"Soulstruct field '{self.soulstruct_field_name}' is not an EulerDeg.")
        bl_value = to_blender(game_euler_deg.to_rad())  # `to_blender()` would also convert, but we are explicit
        setattr(bl_obj, self.bl_prop_name, bl_value)

    def blender_to_soulstruct(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
        soulstruct_obj: SOULSTRUCT_T,
    ):
        game_euler_deg = to_game(getattr(bl_obj, self.bl_prop_name)).to_deg()
        setattr(soulstruct_obj, self.soulstruct_field_name, game_euler_deg)


def soulstruct_adapter(cls: type[SOULSTRUCT_OBJECT_T]) -> type[SOULSTRUCT_OBJECT_T]:
    """Decorator that creates properties for each `SoulstructFieldAdapter` (if requested) in `cls.TYPE_FIELDS`.

    Should decorate every concrete subclass of `BaseBlenderSoulstructObject` (unless a narrower version of this
    decorator is appropriate). You will quickly run into attribute errors on object creation if you forget to do this.
    """

    for fields, is_subtype in [(cls.TYPE_FIELDS, False), (cls.SUBTYPE_FIELDS, True)]:
        for field in fields:
            if not field.auto_prop:
                continue
            setattr(
                cls, field.bl_prop_name, property(
                    lambda self, f=field, s=is_subtype: f.getter(self, is_subtype=s),
                    lambda self, value, f=field, s=is_subtype: f.setter(self, value, is_subtype=s),
                )
            )

    return cls

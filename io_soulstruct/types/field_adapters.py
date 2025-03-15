from __future__ import annotations

__all__ = [
    "SoulstructFieldAdapter",
    "CustomSoulstructFieldAdapter",
    "create_field_adapter_properties",
]

import typing as tp
from dataclasses import dataclass, KW_ONLY

from io_soulstruct.utilities.operators import LoggingOperator

if tp.TYPE_CHECKING:
    from .soulstruct_object import BaseBlenderSoulstructObject, SOULSTRUCT_T, TYPE_PROPS_T
    SOULSTRUCT_OBJECT_T = tp.TypeVar("SOULSTRUCT_OBJECT_T", bound=BaseBlenderSoulstructObject)


@dataclass(slots=True, frozen=True)
class SoulstructFieldAdapter:
    soulstruct_field_name: str
    _: KW_ONLY
    bl_prop_name: str = None  # defaults to `soulstruct_field_name`
    auto_prop: bool = True  # create `type_properties` wrapper property (getter/setter) after class creation

    def __post_init__(self):
        if self.bl_prop_name is None:
            super().__setattr__(self, "bl_prop_name", self.soulstruct_field_name)

    def read_prop_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        soulstruct_obj: SOULSTRUCT_T,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
    ):
        bl_value = getattr(soulstruct_obj, self.soulstruct_field_name)
        setattr(bl_obj, self.bl_prop_name, bl_value)

    def write_prop_to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
        soulstruct_obj: SOULSTRUCT_T,
    ):
        soulstruct_value = getattr(bl_obj, self.bl_prop_name)
        setattr(soulstruct_obj, self.soulstruct_field_name, soulstruct_value)

    def getter(self, bl_obj: BaseBlenderSoulstructObject) -> tp.Any:
        return getattr(bl_obj.type_properties, self.bl_prop_name)

    def setter(self, bl_obj: BaseBlenderSoulstructObject, value: tp.Any) -> None:
        setattr(bl_obj.type_properties, self.bl_prop_name, value)


@dataclass(slots=True, frozen=True)
class CustomSoulstructFieldAdapter(SoulstructFieldAdapter):
    """Simple extension that modifies the `getattr` values (in both directions) before setting them.

    Property getter/setter are unchanged.
    """
    read_func: tp.Callable[[tp.Any], tp.Any] = None  # converts Soulstruct value to Blender value
    write_func: tp.Callable[[tp.Any], tp.Any] = None  # converts Blender value to Soulstruct value

    def __post_init__(self):
        super().__post_init__()
        if self.read_func is None:
            super().__setattr__(self, "read_func", lambda x: x)
        if self.write_func is None:
            super().__setattr__(self, "write_func", lambda x: x)

    def read_prop_from_soulstruct_obj(
        self,
        operator: LoggingOperator,
        soulstruct_obj: SOULSTRUCT_T,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
    ):
        bl_value = self.read_func(getattr(soulstruct_obj, self.soulstruct_field_name))
        setattr(bl_obj, self.bl_prop_name, bl_value)

    def write_prop_to_soulstruct_obj(
        self,
        operator: LoggingOperator,
        bl_obj: BaseBlenderSoulstructObject[SOULSTRUCT_T, TYPE_PROPS_T],
        soulstruct_obj: SOULSTRUCT_T,
    ):
        soulstruct_value = self.write_func(getattr(bl_obj, self.bl_prop_name))
        setattr(soulstruct_obj, self.soulstruct_field_name, soulstruct_value)


def create_field_adapter_properties(cls: type[SOULSTRUCT_OBJECT_T]) -> type[SOULSTRUCT_OBJECT_T]:
    """Decorator that creates properties for each `SoulstructFieldAdapter` (if requested) in `cls.TYPE_FIELDS`.

    Should decorate every concrete subclass of `BaseBlenderSoulstructObject` (unless a narrower version of this
    decorator is appropriate). You will quickly run into attribute errors on object creation if you forget to do this.
    """

    for field in cls.TYPE_FIELDS:
        if not field.auto_prop:
            continue
        # Create property for each prop in `cls.TYPE_FIELDS`, baking in `field` argument.
        setattr(
            cls, field.bl_prop_name, property(
                lambda self, f=field: f.getter(self),
                lambda self, value, f=field: f.setter(self, value),
            )
        )

    return cls

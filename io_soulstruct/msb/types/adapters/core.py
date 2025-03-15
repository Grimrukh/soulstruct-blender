from __future__ import annotations

__all__ = [
    "create_msb_entry_field_adapter_properties",
]

import typing as tp

from .reference import MSBReferenceFieldAdapter

if tp.TYPE_CHECKING:
    from ..base import BaseBlenderMSBEntry
    BL_ENTRY_T = tp.TypeVar("BL_ENTRY_T", bound=BaseBlenderMSBEntry)


def create_msb_entry_field_adapter_properties(cls: type[BL_ENTRY_T]) -> type[BL_ENTRY_T]:
    """Decorator that creates properties for each `MSBEntryProp` (if requested) in `cls.MSB_ENTRY_PROPS`.

    Should decorate every concrete subclass of `BaseBlenderMSBEntry`. (You will quickly run into attribute errors on
    MSB import if you forget to do this.)
    """

    for fields, is_subtype in [(cls.TYPE_FIELDS, True), (cls.SUBTYPE_FIELDS, False)]:
        for field in fields:
            if not field.auto_prop:
                continue
            # `prop` and (for reference fields) `is_subtype` are baked into the lambda functions.
            if isinstance(field, MSBReferenceFieldAdapter):
                # Property with subtype.
                setattr(
                    cls, field.bl_prop_name, property(
                        lambda self, f=field, s=is_subtype: f.getter(self, is_subtype=s),
                        lambda self, value, f=field, s=is_subtype: f.setter(self, value, is_subtype=s),
                    )
                )
            else:
                # Basic property.
                setattr(
                    cls, field.bl_prop_name, property(
                        lambda self, f=field: f.getter(self),
                        lambda self, value, f=field: f.setter(self, value),
                    )
                )

    return cls

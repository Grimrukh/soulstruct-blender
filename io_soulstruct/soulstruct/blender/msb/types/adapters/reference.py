from __future__ import annotations

__all__ = [
    "MSBReferenceFieldAdapter",
]

import typing as tp
from dataclasses import dataclass

import bpy

from soulstruct.blender.exceptions import MissingMSBEntryError, SoulstructTypeError
from soulstruct.blender.msb.types.adapters.names import *
from soulstruct.blender.types import ObjectType, SoulstructType
from soulstruct.blender.types.field_adapters import FieldAdapter
from soulstruct.blender.utilities.bpy_data import find_obj_or_create_empty
from soulstruct.blender.utilities.operators import LoggingOperator

if tp.TYPE_CHECKING:
    from soulstruct.base.maps.msb import MSB as BaseMSB
    from soulstruct.base.maps.msb.msb_entry import MSBEntry
    from soulstruct.blender.msb.types.base import BaseBlenderMSBEntry, ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T
    REF_TYPING = tp.Literal[SoulstructType.MSB_PART, SoulstructType.MSB_REGION, SoulstructType.MSB_EVENT]


@dataclass(slots=True, frozen=True)
class MSBReferenceFieldAdapter(FieldAdapter):
    """Wraps an `MSBEntry` property that references another `MSBEntry`, which we handle in Blender.

    Property getter/setter is overridden to handle array indices.

    These properties are written to exported MSB entries AFTER all MSB entries are created.
    """

    # `create_prop` parent property ignored (always False).
    ref_type: REF_TYPING = None
    ref_subtype: str | None = None  # optional
    array_count: int = 0  # 0 means single reference, otherwise number of references in array

    _NAME_FUNCS: tp.ClassVar[dict[SoulstructType, tp.Callable[[str], str]]] = {
        SoulstructType.MSB_PART: get_part_game_name,
        SoulstructType.MSB_REGION: get_region_game_name,
        SoulstructType.MSB_EVENT: get_event_game_name,
    }

    def __post_init__(self):
        super(MSBReferenceFieldAdapter, self).__post_init__()
        if self.ref_type not in {SoulstructType.MSB_PART, SoulstructType.MSB_REGION, SoulstructType.MSB_EVENT}:
            raise ValueError("MSBReferenceFieldAdapter( must reference an MSB Part, Region, or Event.")
        if self.array_count < 0:
            raise ValueError("`array_count` must be non-negative.")

    @property
    def obj_type(self) -> ObjectType:
        """Just switches on `ref_type`."""
        return ObjectType.EMPTY if self.ref_type == SoulstructType.MSB_EVENT else ObjectType.MESH

    def soulstruct_to_blender(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        soulstruct_obj: ENTRY_T,
        bl_obj: BaseBlenderMSBEntry[ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T],
        *,
        missing_reference_callback: tp.Callable[[bpy.types.Object], None] = None,
        msb_objects: tp.Iterable[bpy.types.Object] = None,
    ):
        if not missing_reference_callback:
            raise ValueError(
                "Missing reference callback must be given to convert MSB Entry references to Blender object "
                "references, in case a reference is missing and needs to be created and linked to a collection."
            )
        if msb_objects is None:
            raise ValueError(
                "MSB objects must be given to convert MSB Entry references to Blender object references, in case "
                "an object in a different loaded map has the same name."
            )

        if self.array_count >= 1:
            # Blender property groups store array references in separate properties, but have `property` wrappers for
            # getting/setting them all at once.
            bl_value = [
                self._msb_entry_ref_to_bl_entry_ref(
                    operator,
                    soulstruct_obj,
                    ref_entry=getattr(soulstruct_obj, self.soulstruct_field_name)[i],
                    msb_objects=msb_objects,
                    missing_reference_callback=missing_reference_callback,
                    array_index=i,  # only needed for error message
                )
                for i in range(self.array_count)
            ]
        else:
            bl_value = self._msb_entry_ref_to_bl_entry_ref(
                operator,
                soulstruct_obj,
                ref_entry=getattr(soulstruct_obj, self.soulstruct_field_name),
                msb_objects=msb_objects,
                missing_reference_callback=missing_reference_callback,
            )

        setattr(bl_obj, self.bl_prop_name, bl_value)

    def blender_to_soulstruct(
        self,
        operator: LoggingOperator,
        context: bpy.types.Context,
        bl_obj: BaseBlenderMSBEntry[ENTRY_T, TYPE_PROPS_T, SUBTYPE_PROPS_T, MSB_T],
        soulstruct_obj: ENTRY_T,
        msb: MSB_T = None,
    ):
        if msb is None:
            raise ValueError("MSB must be given to convert Blender object references to MSB Entry references.")

        if self.array_count >= 1:
            # Blender property groups store array references in separate properties, but have `property` wrappers for
            # getting/setting them all at once.
            bl_values = getattr(bl_obj, self.bl_prop_name)  # type: list[bpy.types.Object | None]
            entry_value = [
                self._bl_entry_ref_to_msb_entry_ref(
                    msb,
                    soulstruct_obj,
                    bl_obj=bl_values[i],
                    array_index=i,  # only needed for error message
                )
                for i in range(self.array_count)
            ]
        else:
            bl_value = getattr(bl_obj, self.bl_prop_name)  # type: bpy.types.Object | None
            entry_value = self._bl_entry_ref_to_msb_entry_ref(
                msb,
                soulstruct_obj,
                bl_obj=bl_value,
            )

        setattr(soulstruct_obj, self.soulstruct_field_name, entry_value)

    def getter(self, bl_obj: BaseBlenderMSBEntry, is_subtype=False):
        props = bl_obj.subtype_properties if is_subtype else bl_obj.type_properties
        if self.array_count > 0:
            return [getattr(props, f"{self.bl_prop_name}_{i}") for i in range(self.array_count)]
        return getattr(props, self.bl_prop_name)

    def setter(self, bl_obj: BaseBlenderMSBEntry, value: tp.Any, is_subtype=False):
        props = bl_obj.subtype_properties if is_subtype else bl_obj.type_properties
        if self.array_count > 0:
            if len(value) > self.array_count:
                raise ValueError(
                    f"Cannot set more than {self.array_count} {self.ref_subtype or self.ref_type} "
                    f"references to field '{self.bl_prop_name}'."
                )
            for i, v in enumerate(value):
                setattr(props, f"{self.bl_prop_name}_{i}", v)
        else:
            setattr(props, self.bl_prop_name, value)

    def _msb_entry_ref_to_bl_entry_ref(
        self,
        operator: LoggingOperator,
        entry: MSBEntry,
        ref_entry: MSBEntry | None,
        msb_objects: tp.Iterable[bpy.types.Object],
        missing_reference_callback: tp.Callable[[bpy.types.Object], None],
        array_index: int = None,
    ) -> bpy.types.Object | None:
        """Convert MSB entry reference to Blender object reference (may be a created Empty added now to
        `missing_collection_name`).

        Note that we don't need overloads for this, as an `Object` is always returned whose `soulstruct_type` tags the
        wrapped Soulstruct type.
        """
        if not ref_entry:
            return None

        bl_name_func = self._NAME_FUNCS[self.ref_type]

        was_missing, pointer_obj = find_obj_or_create_empty(
            ref_entry.name,
            object_type=self.obj_type,
            soulstruct_type=self.ref_type,
            bl_name_func=bl_name_func,
            objects=msb_objects,
            process_new_object=missing_reference_callback,
        )
        if was_missing:
            prop_name_i = f"{self.bl_prop_name}[{array_index}]" if array_index is not None else self.bl_prop_name
            operator.warning(
                f"Referenced MSB entry '{ref_entry.name}' in field '{prop_name_i}' of MSB entry '{entry.name}' not "
                f"found in Blender data. Creating empty reference."
            )
        return pointer_obj

    def _bl_entry_ref_to_msb_entry_ref(
        self,
        msb: BaseMSB,
        referrer_entry: MSBEntry,
        bl_obj: bpy.types.Object | None,
        array_index: int = None,
    ) -> MSBEntry | None:
        """Convert Blender object reference to MSB entry reference.

        Has wrappers for Part, Event, and Region references. Model references use a separate method.
        """

        if not bl_obj:
            # Blender reference is null. Leave MSB Entry field as `None`.
            return None

        subtypes = (self.ref_subtype,) if self.ref_subtype else ()
        entry_name = self._NAME_FUNCS[self.ref_type](bl_obj.name)

        try:
            if self.ref_type == SoulstructType.MSB_PART:
                if bl_obj.soulstruct_type != SoulstructType.MSB_PART:
                    raise SoulstructTypeError(f"Referenced Blender object '{bl_obj.name}' is not an MSB Part.")
                msb_entry = msb.find_part_name(entry_name, subtypes=subtypes)
            elif self.ref_type == SoulstructType.MSB_REGION:
                if bl_obj.soulstruct_type != SoulstructType.MSB_REGION:
                    raise SoulstructTypeError(f"Referenced Blender object '{bl_obj.name}' is not an MSB Region.")
                msb_entry = msb.find_region_name(entry_name, subtypes=subtypes)
            elif self.ref_type == SoulstructType.MSB_EVENT:
                # Never observed.
                if bl_obj.soulstruct_type != SoulstructType.MSB_EVENT:
                    raise SoulstructTypeError(f"Referenced Blender object '{bl_obj.name}' is not an MSB Event.")
                msb_entry = msb.find_event_name(entry_name, subtypes=subtypes)
            else:
                raise SoulstructTypeError(f"Blender object '{bl_obj.name}' is not an MSB Part, Region, or Event.")
            return msb_entry
        except KeyError:
            prop_name_i = f"{self.bl_prop_name}[{array_index}]" if array_index is not None else self.bl_prop_name
            raise MissingMSBEntryError(
                f"MSB entry '{bl_obj.name}' referenced in field '{prop_name_i}' of MSB entry '{referrer_entry.name}' "
                f"not found in MSB (under name '{entry_name}')."
            )

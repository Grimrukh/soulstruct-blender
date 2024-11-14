import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .id_override_library_property_operation import IDOverrideLibraryPropertyOperation
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class IDOverrideLibraryPropertyOperations(
    bpy_prop_collection[IDOverrideLibraryPropertyOperation], bpy_struct
):
    """Collection of override operations"""

    def add(
        self,
        operation: str | None,
        use_id: bool | typing.Any | None = False,
        subitem_reference_name: str | typing.Any = "",
        subitem_local_name: str | typing.Any = "",
        subitem_reference_id: ID | None = None,
        subitem_local_id: ID | None = None,
        subitem_reference_index: typing.Any | None = -1,
        subitem_local_index: typing.Any | None = -1,
    ) -> IDOverrideLibraryPropertyOperation:
        """Add a new operation

                :param operation: Operation, What override operation is performed

        NOOP
        No-Op -- Does nothing, prevents adding actual overrides (NOT USED).

        REPLACE
        Replace -- Replace value of reference by overriding one.

        DIFF_ADD
        Differential -- Stores and apply difference between reference and local value (NOT USED).

        DIFF_SUB
        Differential -- Stores and apply difference between reference and local value (NOT USED).

        FACT_MULTIPLY
        Factor -- Stores and apply multiplication factor between reference and local value (NOT USED).

        INSERT_AFTER
        Insert After -- Insert a new item into collection after the one referenced in subitem_reference_name/_id or _index.

        INSERT_BEFORE
        Insert Before -- Insert a new item into collection before the one referenced in subitem_reference_name/_id or _index (NOT USED).
                :type operation: str | None
                :param use_id: Use ID Pointer Subitem, Whether the found or created liboverride operation should use ID pointers or not
                :type use_id: bool | typing.Any | None
                :param subitem_reference_name: Subitem Reference Name, Used to handle insertions or ID replacements into collection
                :type subitem_reference_name: str | typing.Any
                :param subitem_local_name: Subitem Local Name, Used to handle insertions or ID replacements into collection
                :type subitem_local_name: str | typing.Any
                :param subitem_reference_id: Subitem Reference ID, Used to handle ID replacements into collection
                :type subitem_reference_id: ID | None
                :param subitem_local_id: Subitem Local ID, Used to handle ID replacements into collection
                :type subitem_local_id: ID | None
                :param subitem_reference_index: Subitem Reference Index, Used to handle insertions or ID replacements into collection
                :type subitem_reference_index: typing.Any | None
                :param subitem_local_index: Subitem Local Index, Used to handle insertions or ID replacements into collection
                :type subitem_local_index: typing.Any | None
                :return: New Operation, Created operation
                :rtype: IDOverrideLibraryPropertyOperation
        """
        ...

    def remove(self, operation: IDOverrideLibraryPropertyOperation | None):
        """Remove and delete an operation

        :param operation: Operation, Override operation to be deleted
        :type operation: IDOverrideLibraryPropertyOperation | None
        """
        ...

    @classmethod
    def bl_rna_get_subclass(cls, id: str | None, default=None) -> Struct:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The RNA type or default when not found.
        :rtype: Struct
        """
        ...

    @classmethod
    def bl_rna_get_subclass_py(cls, id: str | None, default=None) -> typing.Any:
        """

        :param id: The RNA type identifier.
        :type id: str | None
        :param default:
        :return: The class or default when not found.
        :rtype: typing.Any
        """
        ...

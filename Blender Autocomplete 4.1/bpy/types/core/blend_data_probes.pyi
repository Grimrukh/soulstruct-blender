import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .light_probe import LightProbe
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataProbes(bpy_prop_collection[LightProbe], bpy_struct):
    """Collection of light probes"""

    def new(self, name: str | typing.Any, type: str | None) -> LightProbe:
        """Add a new light probe to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :param type: Type, The type of light probe to add
        :type type: str | None
        :return: New light probe data-block
        :rtype: LightProbe
        """
        ...

    def remove(
        self,
        lightprobe: LightProbe,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a light probe from the current blendfile

        :param lightprobe: Light probe to remove
        :type lightprobe: LightProbe
        :param do_unlink: Unlink all usages of this light probe before deleting it (WARNING: will also delete objects instancing that light probe data)
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this light probe
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this light probe
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
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

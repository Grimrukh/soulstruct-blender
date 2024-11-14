import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .shader_fx import ShaderFx

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ObjectShaderFx(bpy_prop_collection[ShaderFx], bpy_struct):
    """Collection of object effects"""

    def new(self, name: str | typing.Any, type: str | None) -> ShaderFx:
        """Add a new shader fx

        :param name: New name for the effect
        :type name: str | typing.Any
        :param type: Effect type to add
        :type type: str | None
        :return: Newly created effect
        :rtype: ShaderFx
        """
        ...

    def remove(self, shader_fx: ShaderFx):
        """Remove an existing effect from the object

        :param shader_fx: Effect to remove
        :type shader_fx: ShaderFx
        """
        ...

    def clear(self):
        """Remove all effects from the object"""
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

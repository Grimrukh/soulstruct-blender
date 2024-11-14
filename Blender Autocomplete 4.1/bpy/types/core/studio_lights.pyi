import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .studio_light import StudioLight

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class StudioLights(bpy_prop_collection[StudioLight], bpy_struct):
    """Collection of studio lights"""

    def load(self, path: str | typing.Any, type: str | None) -> StudioLight:
        """Load studiolight from file

        :param path: File Path, File path where the studio light file can be found
        :type path: str | typing.Any
        :param type: Type, The type for the new studio light
        :type type: str | None
        :return: Newly created StudioLight
        :rtype: StudioLight
        """
        ...

    def new(self, path: str | typing.Any) -> StudioLight:
        """Create studiolight from default lighting

        :param path: Path, Path to the file that will contain the lighting info (without extension)
        :type path: str | typing.Any
        :return: Newly created StudioLight
        :rtype: StudioLight
        """
        ...

    def remove(self, studio_light: StudioLight):
        """Remove a studio light

        :param studio_light: The studio light to remove
        :type studio_light: StudioLight
        """
        ...

    def refresh(self):
        """Refresh Studio Lights from disk"""
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

import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MaterialLineArt(bpy_struct):
    intersection_priority: int
    """ The intersection line will be included into the object with the higher intersection priority value

    :type: int
    """

    mat_occlusion: int
    """ Faces with this material will behave as if it has set number of layers in occlusion

    :type: int
    """

    use_intersection_priority_override: bool
    """ Override object and collection intersection priority value

    :type: bool
    """

    use_material_mask: bool
    """ Use material masks to filter out occluded strokes

    :type: bool
    """

    use_material_mask_bits: list[bool]
    """ 

    :type: list[bool]
    """

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

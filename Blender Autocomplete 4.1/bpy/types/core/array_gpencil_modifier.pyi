import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .object import Object
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ArrayGpencilModifier(GpencilModifier, bpy_struct):
    """Create grid of duplicate instances"""

    constant_offset: mathutils.Vector
    """ Value for the distance between items

    :type: mathutils.Vector
    """

    count: int
    """ Number of items

    :type: int
    """

    invert_layer_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_layers: bool
    """ Inverse filter

    :type: bool
    """

    invert_material_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_materials: bool
    """ Inverse filter

    :type: bool
    """

    layer: str
    """ Layer name

    :type: str
    """

    layer_pass: int
    """ Layer pass index

    :type: int
    """

    material: Material
    """ Material used for filtering effect

    :type: Material
    """

    offset_object: Object
    """ Use the location and rotation of another object to determine the distance and rotational change between arrayed items

    :type: Object
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    random_offset: mathutils.Vector
    """ Value for changes in location

    :type: mathutils.Vector
    """

    random_rotation: mathutils.Euler
    """ Value for changes in rotation

    :type: mathutils.Euler
    """

    random_scale: mathutils.Vector
    """ Value for changes in scale

    :type: mathutils.Vector
    """

    relative_offset: mathutils.Vector
    """ The size of the geometry will determine the distance between arrayed items

    :type: mathutils.Vector
    """

    replace_material: int
    """ Index of the material used for generated strokes (0 keep original material)

    :type: int
    """

    seed: int
    """ Random seed

    :type: int
    """

    use_constant_offset: bool
    """ Enable offset

    :type: bool
    """

    use_object_offset: bool
    """ Enable object offset

    :type: bool
    """

    use_relative_offset: bool
    """ Enable shift

    :type: bool
    """

    use_uniform_random_scale: bool
    """ Use the same random seed for each scale axis for a uniform scale

    :type: bool
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

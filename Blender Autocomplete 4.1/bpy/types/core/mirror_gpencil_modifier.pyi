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


class MirrorGpencilModifier(GpencilModifier, bpy_struct):
    """Create mirroring strokes"""

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

    object: Object
    """ Object used as center

    :type: Object
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    use_axis_x: bool
    """ Mirror the X axis

    :type: bool
    """

    use_axis_y: bool
    """ Mirror the Y axis

    :type: bool
    """

    use_axis_z: bool
    """ Mirror the Z axis

    :type: bool
    """

    use_clip: bool
    """ Clip points

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

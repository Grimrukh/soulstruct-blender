import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GreasePencilMirrorModifier(Modifier, bpy_struct):
    invert_layer_filter: bool
    """ Invert layer filter

    :type: bool
    """

    invert_layer_pass_filter: bool
    """ Invert layer pass filter

    :type: bool
    """

    invert_material_filter: bool
    """ Invert material filter

    :type: bool
    """

    invert_material_pass_filter: bool
    """ Invert material pass filter

    :type: bool
    """

    layer_filter: str
    """ Layer name

    :type: str
    """

    layer_pass_filter: int
    """ Layer pass filter

    :type: int
    """

    material_filter: Material
    """ Material used for filtering

    :type: Material
    """

    material_pass_filter: int
    """ Material pass

    :type: int
    """

    object: Object
    """ Object used as center

    :type: Object
    """

    open_influence_panel: bool
    """ 

    :type: bool
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

    use_layer_pass_filter: bool
    """ Use layer pass filter

    :type: bool
    """

    use_material_pass_filter: bool
    """ Use material pass filter

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

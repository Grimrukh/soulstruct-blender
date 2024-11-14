import typing
import collections.abc
import mathutils
from .line_style_color_modifier import LineStyleColorModifier
from .struct import Struct
from .bpy_struct import bpy_struct
from .color_ramp import ColorRamp
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleColorModifier_Material(
    LineStyleColorModifier, LineStyleModifier, bpy_struct
):
    """Change line color based on a material attribute"""

    blend: str
    """ Specify how the modifier value is blended into the base value

    :type: str
    """

    color_ramp: ColorRamp
    """ Color ramp used to change line color

    :type: ColorRamp
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    influence: float
    """ Influence factor by which the modifier changes the property

    :type: float
    """

    material_attribute: str
    """ Specify which material attribute is used

    :type: str
    """

    type: str
    """ Type of the modifier

    :type: str
    """

    use: bool
    """ Enable or disable this modifier during stroke rendering

    :type: bool
    """

    use_ramp: bool
    """ Use color ramp to map the BW average into an RGB color

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

import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .line_style_thickness_modifier import LineStyleThicknessModifier
from .line_style_modifier import LineStyleModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class LineStyleThicknessModifier_Calligraphy(
    LineStyleThicknessModifier, LineStyleModifier, bpy_struct
):
    """Change line thickness so that stroke looks like made with a calligraphic pen"""

    blend: str
    """ Specify how the modifier value is blended into the base value

    :type: str
    """

    expanded: bool
    """ True if the modifier tab is expanded

    :type: bool
    """

    influence: float
    """ Influence factor by which the modifier changes the property

    :type: float
    """

    orientation: float
    """ Angle of the main direction

    :type: float
    """

    thickness_max: float
    """ Maximum thickness in the main direction

    :type: float
    """

    thickness_min: float
    """ Minimum thickness in the direction perpendicular to the main direction

    :type: float
    """

    type: str
    """ Type of the modifier

    :type: str
    """

    use: bool
    """ Enable or disable this modifier during stroke rendering

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

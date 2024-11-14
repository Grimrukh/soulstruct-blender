import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .curve_mapping import CurveMapping

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ColorManagedViewSettings(bpy_struct):
    """Color management settings used for displaying images on the display"""

    curve_mapping: CurveMapping
    """ Color curve mapping applied before display transform

    :type: CurveMapping
    """

    exposure: float
    """ Exposure (stops) applied before display transform

    :type: float
    """

    gamma: float
    """ Amount of gamma modification applied after display transform

    :type: float
    """

    look: str
    """ Additional transform applied before view transform for artistic needs

    :type: str
    """

    use_curve_mapping: bool
    """ Use RGB curved for pre-display transformation

    :type: bool
    """

    use_hdr_view: bool
    """ Enable high dynamic range display in rendered viewport, uncapping display brightness. This requires a monitor with HDR support and a view transform designed for HDR. 'Filmic' and 'AgX' do not generate HDR colors

    :type: bool
    """

    view_transform: str
    """ View used when converting image to a display space

    :type: str
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

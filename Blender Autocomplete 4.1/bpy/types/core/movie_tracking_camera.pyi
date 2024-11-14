import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MovieTrackingCamera(bpy_struct):
    """Match-moving camera data for tracking"""

    brown_k1: float
    """ First coefficient of fourth order Brown-Conrady radial distortion

    :type: float
    """

    brown_k2: float
    """ Second coefficient of fourth order Brown-Conrady radial distortion

    :type: float
    """

    brown_k3: float
    """ Third coefficient of fourth order Brown-Conrady radial distortion

    :type: float
    """

    brown_k4: float
    """ Fourth coefficient of fourth order Brown-Conrady radial distortion

    :type: float
    """

    brown_p1: float
    """ First coefficient of second order Brown-Conrady tangential distortion

    :type: float
    """

    brown_p2: float
    """ Second coefficient of second order Brown-Conrady tangential distortion

    :type: float
    """

    distortion_model: str
    """ Distortion model used for camera lenses

    :type: str
    """

    division_k1: float
    """ First coefficient of second order division distortion

    :type: float
    """

    division_k2: float
    """ Second coefficient of second order division distortion

    :type: float
    """

    focal_length: float
    """ Camera's focal length

    :type: float
    """

    focal_length_pixels: float
    """ Camera's focal length

    :type: float
    """

    k1: float
    """ First coefficient of third order polynomial radial distortion

    :type: float
    """

    k2: float
    """ Second coefficient of third order polynomial radial distortion

    :type: float
    """

    k3: float
    """ Third coefficient of third order polynomial radial distortion

    :type: float
    """

    nuke_k1: float
    """ First coefficient of second order Nuke distortion

    :type: float
    """

    nuke_k2: float
    """ Second coefficient of second order Nuke distortion

    :type: float
    """

    pixel_aspect: float
    """ Pixel aspect ratio

    :type: float
    """

    principal_point: bpy_prop_array[float]
    """ Optical center of lens

    :type: bpy_prop_array[float]
    """

    principal_point_pixels: bpy_prop_array[float]
    """ Optical center of lens in pixels

    :type: bpy_prop_array[float]
    """

    sensor_width: float
    """ Width of CCD sensor in millimeters

    :type: float
    """

    units: str
    """ Units used for camera focal length

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

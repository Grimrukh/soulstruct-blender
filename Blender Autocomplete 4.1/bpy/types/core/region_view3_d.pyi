import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RegionView3D(bpy_struct):
    """3D View region data"""

    clip_planes: list[list[float]] | tuple[
        tuple[float, float, float, float, float, float],
        tuple[float, float, float, float, float, float],
        tuple[float, float, float, float, float, float],
        tuple[float, float, float, float, float, float],
    ]
    """ 

    :type: list[list[float]] | tuple[tuple[float, float, float, float, float, float], tuple[float, float, float, float, float, float], tuple[float, float, float, float, float, float], tuple[float, float, float, float, float, float]]
    """

    is_orthographic_side_view: bool
    """ Whether the current view is aligned to an axis (does not check whether the view is orthographic, use "is_perspective" for that). Setting this will rotate the view to the closest axis

    :type: bool
    """

    is_perspective: bool
    """ 

    :type: bool
    """

    lock_rotation: bool
    """ Lock view rotation of side views to Top/Front/Right

    :type: bool
    """

    perspective_matrix: mathutils.Matrix
    """ Current perspective matrix (window_matrix * view_matrix)

    :type: mathutils.Matrix
    """

    show_sync_view: bool
    """ Sync view position between side views

    :type: bool
    """

    use_box_clip: bool
    """ Clip view contents based on what is visible in other side views

    :type: bool
    """

    use_clip_planes: bool
    """ 

    :type: bool
    """

    view_camera_offset: bpy_prop_array[float]
    """ View shift in camera view

    :type: bpy_prop_array[float]
    """

    view_camera_zoom: float
    """ Zoom factor in camera view

    :type: float
    """

    view_distance: float
    """ Distance to the view location

    :type: float
    """

    view_location: mathutils.Vector
    """ View pivot location

    :type: mathutils.Vector
    """

    view_matrix: mathutils.Matrix
    """ Current view matrix

    :type: mathutils.Matrix
    """

    view_perspective: str
    """ View Perspective

    :type: str
    """

    view_rotation: mathutils.Quaternion
    """ Rotation in quaternions (keep normalized)

    :type: mathutils.Quaternion
    """

    window_matrix: mathutils.Matrix
    """ Current window matrix

    :type: mathutils.Matrix
    """

    def update(self):
        """Recalculate the view matrices"""
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

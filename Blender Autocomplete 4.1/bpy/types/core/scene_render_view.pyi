import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SceneRenderView(bpy_struct):
    """Render viewpoint for 3D stereo and multiview rendering"""

    camera_suffix: str
    """ Suffix to identify the cameras to use, and added to the render images for this view

    :type: str
    """

    file_suffix: str
    """ Suffix added to the render images for this view

    :type: str
    """

    name: str
    """ Render view name

    :type: str
    """

    use: bool
    """ Disable or enable the render view

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

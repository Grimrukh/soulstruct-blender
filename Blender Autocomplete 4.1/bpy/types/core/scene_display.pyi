import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .view3_d_shading import View3DShading

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SceneDisplay(bpy_struct):
    """Scene display settings for 3D viewport"""

    light_direction: mathutils.Vector
    """ Direction of the light for shadows and highlights

    :type: mathutils.Vector
    """

    matcap_ssao_attenuation: float
    """ Attenuation constant

    :type: float
    """

    matcap_ssao_distance: float
    """ Distance of object that contribute to the Cavity/Edge effect

    :type: float
    """

    matcap_ssao_samples: int
    """ Number of samples

    :type: int
    """

    render_aa: str
    """ Method of anti-aliasing when rendering final image

    :type: str
    """

    shading: View3DShading
    """ Shading settings for OpenGL render engine

    :type: View3DShading
    """

    shadow_focus: float
    """ Shadow factor hardness

    :type: float
    """

    shadow_shift: float
    """ Shadow termination angle

    :type: float
    """

    viewport_aa: str
    """ Method of anti-aliasing when rendering 3d viewport

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

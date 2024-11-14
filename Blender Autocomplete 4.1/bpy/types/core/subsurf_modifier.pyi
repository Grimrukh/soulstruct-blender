import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SubsurfModifier(Modifier, bpy_struct):
    """Subdivision surface modifier"""

    boundary_smooth: str
    """ Controls how open boundaries are smoothed

    :type: str
    """

    levels: int
    """ Number of subdivisions to perform

    :type: int
    """

    quality: int
    """ Accuracy of vertex positions, lower value is faster but less precise

    :type: int
    """

    render_levels: int
    """ Number of subdivisions to perform when rendering

    :type: int
    """

    show_only_control_edges: bool
    """ Skip displaying interior subdivided edges

    :type: bool
    """

    subdivision_type: str
    """ Select type of subdivision algorithm

    :type: str
    """

    use_creases: bool
    """ Use mesh crease information to sharpen edges or corners

    :type: bool
    """

    use_custom_normals: bool
    """ Interpolates existing custom normals to resulting mesh

    :type: bool
    """

    use_limit_surface: bool
    """ Place vertices at the surface that would be produced with infinite levels of subdivision (smoothest possible shape)

    :type: bool
    """

    uv_smooth: str
    """ Controls how smoothing is applied to UVs

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

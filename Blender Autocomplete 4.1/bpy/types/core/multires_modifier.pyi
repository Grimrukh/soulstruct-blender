import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MultiresModifier(Modifier, bpy_struct):
    """Multiresolution mesh modifier"""

    boundary_smooth: str
    """ Controls how open boundaries are smoothed

    :type: str
    """

    filepath: str
    """ Path to external displacements file

    :type: str
    """

    is_external: bool
    """ Store multires displacements outside the .blend file, to save memory

    :type: bool
    """

    levels: int
    """ Number of subdivisions to use in the viewport

    :type: int
    """

    quality: int
    """ Accuracy of vertex positions, lower value is faster but less precise

    :type: int
    """

    render_levels: int
    """ The subdivision level visible at render time

    :type: int
    """

    sculpt_levels: int
    """ Number of subdivisions to use in sculpt mode

    :type: int
    """

    show_only_control_edges: bool
    """ Skip drawing/rendering of interior subdivided edges

    :type: bool
    """

    total_levels: int
    """ Number of subdivisions for which displacements are stored

    :type: int
    """

    use_creases: bool
    """ Use mesh crease information to sharpen edges or corners

    :type: bool
    """

    use_custom_normals: bool
    """ Interpolates existing custom normals to resulting mesh

    :type: bool
    """

    use_sculpt_base_mesh: bool
    """ Make Sculpt Mode tools deform the base mesh while previewing the displacement of higher subdivision levels

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

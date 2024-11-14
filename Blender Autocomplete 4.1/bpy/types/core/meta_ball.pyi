import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .meta_ball_elements import MetaBallElements
from .anim_data import AnimData
from .id import ID
from .id_materials import IDMaterials

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MetaBall(ID, bpy_struct):
    """Metaball data-block to define blobby surfaces"""

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    cycles: typing.Any
    """ Cycles mesh settings

    :type: typing.Any
    """

    elements: MetaBallElements
    """ Metaball elements

    :type: MetaBallElements
    """

    is_editmode: bool
    """ True when used in editmode

    :type: bool
    """

    materials: IDMaterials
    """ 

    :type: IDMaterials
    """

    render_resolution: float
    """ Polygonization resolution in rendering

    :type: float
    """

    resolution: float
    """ Polygonization resolution in the 3D viewport

    :type: float
    """

    texspace_location: mathutils.Vector
    """ Texture space location

    :type: mathutils.Vector
    """

    texspace_size: mathutils.Vector
    """ Texture space size

    :type: mathutils.Vector
    """

    threshold: float
    """ Influence of metaball elements

    :type: float
    """

    update_method: str
    """ Metaball edit update behavior

    :type: str
    """

    use_auto_texspace: bool
    """ Adjust active object's texture space automatically when transforming object

    :type: bool
    """

    def transform(
        self,
        matrix: collections.abc.Sequence[collections.abc.Sequence[float]]
        | mathutils.Matrix
        | None,
    ):
        """Transform metaball elements by a matrix

        :param matrix: Matrix
        :type matrix: collections.abc.Sequence[collections.abc.Sequence[float]] | mathutils.Matrix | None
        """
        ...

    def update_gpu_tag(self):
        """update_gpu_tag"""
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

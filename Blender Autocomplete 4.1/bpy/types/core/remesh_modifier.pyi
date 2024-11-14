import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RemeshModifier(Modifier, bpy_struct):
    """Generate a new surface with regular topology that follows the shape of the input mesh"""

    adaptivity: float
    """ Reduces the final face count by simplifying geometry where detail is not needed, generating triangles. A value greater than 0 disables Fix Poles

    :type: float
    """

    mode: str
    """ 

    :type: str
    """

    octree_depth: int
    """ Resolution of the octree; higher values give finer details

    :type: int
    """

    scale: float
    """ The ratio of the largest dimension of the model over the size of the grid

    :type: float
    """

    sharpness: float
    """ Tolerance for outliers; lower values filter noise while higher values will reproduce edges closer to the input

    :type: float
    """

    threshold: float
    """ If removing disconnected pieces, minimum size of components to preserve as a ratio of the number of polygons in the largest component

    :type: float
    """

    use_remove_disconnected: bool
    """ 

    :type: bool
    """

    use_smooth_shade: bool
    """ Output faces with smooth shading rather than flat shaded

    :type: bool
    """

    voxel_size: float
    """ Size of the voxel in object space used for volume evaluation. Lower values preserve finer details

    :type: float
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

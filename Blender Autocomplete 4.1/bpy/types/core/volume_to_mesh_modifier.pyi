import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class VolumeToMeshModifier(Modifier, bpy_struct):
    adaptivity: float
    """ Reduces the final face count by simplifying geometry where detail is not needed

    :type: float
    """

    grid_name: str
    """ Grid in the volume object that is converted to a mesh

    :type: str
    """

    object: Object
    """ Object

    :type: Object
    """

    resolution_mode: str
    """ Mode for how the desired voxel size is specified

    :type: str
    """

    threshold: float
    """ Voxels with a larger value are inside the generated mesh

    :type: float
    """

    use_smooth_shade: bool
    """ Output faces with smooth shading rather than flat shaded

    :type: bool
    """

    voxel_amount: int
    """ Approximate number of voxels along one axis

    :type: int
    """

    voxel_size: float
    """ Smaller values result in a higher resolution output

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

import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class MirrorModifier(Modifier, bpy_struct):
    """Mirroring modifier"""

    bisect_threshold: float
    """ Distance from the bisect plane within which vertices are removed

    :type: float
    """

    merge_threshold: float
    """ Distance within which mirrored vertices are merged

    :type: float
    """

    mirror_object: Object
    """ Object to use as mirror

    :type: Object
    """

    mirror_offset_u: float
    """ Amount to offset mirrored UVs flipping point from the 0.5 on the U axis

    :type: float
    """

    mirror_offset_v: float
    """ Amount to offset mirrored UVs flipping point from the 0.5 point on the V axis

    :type: float
    """

    offset_u: float
    """ Mirrored UV offset on the U axis

    :type: float
    """

    offset_v: float
    """ Mirrored UV offset on the V axis

    :type: float
    """

    use_axis: list[bool]
    """ Enable axis mirror

    :type: list[bool]
    """

    use_bisect_axis: list[bool]
    """ Cuts the mesh across the mirror plane

    :type: list[bool]
    """

    use_bisect_flip_axis: list[bool]
    """ Flips the direction of the slice

    :type: list[bool]
    """

    use_clip: bool
    """ Prevent vertices from going through the mirror during transform

    :type: bool
    """

    use_mirror_merge: bool
    """ Merge vertices within the merge threshold

    :type: bool
    """

    use_mirror_u: bool
    """ Mirror the U texture coordinate around the flip offset point

    :type: bool
    """

    use_mirror_udim: bool
    """ Mirror the texture coordinate around each tile center

    :type: bool
    """

    use_mirror_v: bool
    """ Mirror the V texture coordinate around the flip offset point

    :type: bool
    """

    use_mirror_vertex_groups: bool
    """ Mirror vertex groups (e.g. .R->.L)

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

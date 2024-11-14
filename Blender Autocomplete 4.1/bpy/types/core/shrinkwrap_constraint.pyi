import typing
import collections.abc
import mathutils
from .struct import Struct
from .constraint import Constraint
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShrinkwrapConstraint(Constraint, bpy_struct):
    """Create constraint-based shrinkwrap relationship"""

    cull_face: str
    """ Stop vertices from projecting to a face on the target when facing towards/away

    :type: str
    """

    distance: float
    """ Distance to Target

    :type: float
    """

    project_axis: str
    """ Axis constrain to

    :type: str
    """

    project_axis_space: str
    """ Space for the projection axis

    :type: str
    """

    project_limit: float
    """ Limit the distance used for projection (zero disables)

    :type: float
    """

    shrinkwrap_type: str
    """ Select type of shrinkwrap algorithm for target position

    :type: str
    """

    target: Object
    """ Target Mesh object

    :type: Object
    """

    track_axis: str
    """ Axis that is aligned to the normal

    :type: str
    """

    use_invert_cull: bool
    """ When projecting in the opposite direction invert the face cull mode

    :type: bool
    """

    use_project_opposite: bool
    """ Project in both specified and opposite directions

    :type: bool
    """

    use_track_normal: bool
    """ Align the specified axis to the surface normal

    :type: bool
    """

    wrap_mode: str
    """ Select how to constrain the object to the target surface

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

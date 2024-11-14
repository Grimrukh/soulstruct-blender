import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Constraint(bpy_struct):
    """Constraint modifying the transformation of objects and bones"""

    active: bool | None
    """ Constraint is the one being edited

    :type: bool | None
    """

    enabled: bool
    """ Use the results of this constraint

    :type: bool
    """

    error_location: float
    """ Amount of residual error in Blender space unit for constraints that work on position

    :type: float
    """

    error_rotation: float
    """ Amount of residual error in radians for constraints that work on orientation

    :type: float
    """

    influence: float
    """ Amount of influence constraint will have on the final solution

    :type: float
    """

    is_override_data: bool
    """ In a local override object, whether this constraint comes from the linked reference object, or is local to the override

    :type: bool
    """

    is_valid: bool
    """ Constraint has valid settings and can be evaluated

    :type: bool
    """

    mute: bool
    """ Enable/Disable Constraint

    :type: bool
    """

    name: str
    """ Constraint name

    :type: str
    """

    owner_space: str
    """ Space that owner is evaluated in

    :type: str
    """

    show_expanded: bool
    """ Constraint's panel is expanded in UI

    :type: bool
    """

    space_object: Object
    """ Object for Custom Space

    :type: Object
    """

    space_subtarget: str
    """ Armature bone, mesh or lattice vertex group, ...

    :type: str
    """

    target_space: str
    """ Space that target is evaluated in

    :type: str
    """

    type: str
    """ 

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

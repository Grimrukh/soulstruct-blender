import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .property import Property

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Function(bpy_struct):
    """RNA function definition"""

    description: str
    """ Description of the Function's purpose

    :type: str
    """

    identifier: str
    """ Unique name used in the code and scripting

    :type: str
    """

    is_registered: bool
    """ Function is registered as callback as part of type registration

    :type: bool
    """

    is_registered_optional: bool
    """ Function is optionally registered as callback part of type registration

    :type: bool
    """

    parameters: bpy_prop_collection[Property]
    """ Parameters for the function

    :type: bpy_prop_collection[Property]
    """

    use_self: bool
    """ Function does not pass itself as an argument (becomes a static method in Python)

    :type: bool
    """

    use_self_type: bool
    """ Function passes itself type as an argument (becomes a class method in Python if use_self is false)

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

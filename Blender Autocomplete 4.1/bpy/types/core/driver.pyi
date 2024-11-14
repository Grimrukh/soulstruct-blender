import typing
import collections.abc
import mathutils
from .struct import Struct
from .channel_driver_variables import ChannelDriverVariables
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Driver(bpy_struct):
    """Driver for the value of a setting based on an external value"""

    expression: str
    """ Expression to use for Scripted Expression

    :type: str
    """

    is_simple_expression: bool
    """ The scripted expression can be evaluated without using the full Python interpreter

    :type: bool
    """

    is_valid: bool
    """ Driver could not be evaluated in past, so should be skipped

    :type: bool
    """

    type: str
    """ Driver type

    :type: str
    """

    use_self: bool
    """ Include a 'self' variable in the name-space, so drivers can easily reference the data being modified (object, bone, etc...)

    :type: bool
    """

    variables: ChannelDriverVariables
    """ Properties acting as inputs for this driver

    :type: ChannelDriverVariables
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

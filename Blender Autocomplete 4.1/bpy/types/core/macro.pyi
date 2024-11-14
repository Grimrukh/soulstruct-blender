import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties
from .context import Context

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Macro(bpy_struct):
    """Storage of a macro operator being executed, or registered after execution"""

    bl_cursor_pending: str
    """ Cursor to use when waiting for the user to select a location to activate the operator (when bl_options has DEPENDS_ON_CURSOR set)

    :type: str
    """

    bl_description: str
    """ 

    :type: str
    """

    bl_idname: str
    """ 

    :type: str
    """

    bl_label: str
    """ 

    :type: str
    """

    bl_options: typing.Any
    """ Options for this operator type"""

    bl_translation_context: str
    """ 

    :type: str
    """

    bl_undo_group: str
    """ 

    :type: str
    """

    has_reports: bool
    """ Operator has a set of reports (warnings and errors) from last execution

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    properties: OperatorProperties
    """ 

    :type: OperatorProperties
    """

    def report(self, type, message: str | typing.Any):
        """report

        :param type: Type
        :param message: Report Message
        :type message: str | typing.Any
        """
        ...

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Test if the operator can be called or not

        :param context:
        :type context: Context
        :return:
        :rtype: bool
        """
        ...

    def draw(self, context: Context):
        """Draw function for the operator

        :param context:
        :type context: Context
        """
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

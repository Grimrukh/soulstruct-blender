import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .macro import Macro
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties
from .context import Context
from .operator_options import OperatorOptions
from .ui_layout import UILayout
from .event import Event

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Operator(bpy_struct):
    """Storage of an operator being executed, or registered after execution"""

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

    layout: UILayout
    """ 

    :type: UILayout
    """

    macros: bpy_prop_collection[Macro]
    """ 

    :type: bpy_prop_collection[Macro]
    """

    name: str
    """ 

    :type: str
    """

    options: OperatorOptions
    """ Runtime options

    :type: OperatorOptions
    """

    properties: OperatorProperties
    """ 

    :type: OperatorProperties
    """

    bl_property: typing.Any
    """ The name of a property to use as this operators primary property.
Currently this is only used to select the default property when
expanding an operator into a menu.
:type: string"""

    is_registered: bool
    """ 

    :type: bool
    """

    def report(self, type, message: str | typing.Any):
        """report

        :param type: Type
        :param message: Report Message
        :type message: str | typing.Any
        """
        ...

    def is_repeat(self) -> bool:
        """is_repeat

        :return: result
        :rtype: bool
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

    def execute(self, context: Context):
        """Execute the operator

        :param context:
        :type context: Context
        :return: result
        """
        ...

    def check(self, context: Context) -> bool:
        """Check the operator settings, return True to signal a change to redraw

        :param context:
        :type context: Context
        :return: result
        :rtype: bool
        """
        ...

    def invoke(self, context: Context, event: Event):
        """Invoke the operator

        :param context:
        :type context: Context
        :param event:
        :type event: Event
        :return: result
        """
        ...

    def modal(self, context: Context, event: Event):
        """Modal operator function

        :param context:
        :type context: Context
        :param event:
        :type event: Event
        :return: result
        """
        ...

    def draw(self, context: Context):
        """Draw function for the operator

        :param context:
        :type context: Context
        """
        ...

    def cancel(self, context: Context):
        """Called when the operator is canceled

        :param context:
        :type context: Context
        """
        ...

    @classmethod
    def description(cls, context: Context, properties: OperatorProperties) -> str:
        """Compute a description string that depends on parameters

        :param context:
        :type context: Context
        :param properties:
        :type properties: OperatorProperties
        :return: result
        :rtype: str
        """
        ...

    def as_keywords(self, *, ignore=()):
        """Return a copy of the properties as a dictionary

        :param ignore:
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

    @classmethod
    def poll_message_set(cls, message: str | None, *args):
        """Set the message to show in the tool-tip when poll fails.When message is callable, additional user defined positional arguments are passed to the message function.

        :param message: The message or a function that returns the message.
        :type message: str | None
        :param args:
        """
        ...

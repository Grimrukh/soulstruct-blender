import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .context import Context

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FileHandler(bpy_struct):
    """Extends functionality to operators that manages files, such as adding drag and drop support"""

    bl_file_extensions: str
    """ Formatted string of file extensions supported by the file handler, each extension should start with a "." and be separated by ";".
For Example: ".blend;.ble"

    :type: str
    """

    bl_idname: str
    """ If this is set, the file handler gets a custom ID, otherwise it takes the name of the class used to define the file handler (for example, if the class name is "OBJECT_FH_hello", and bl_idname is not set by the script, then bl_idname = "OBJECT_FH_hello")

    :type: str
    """

    bl_import_operator: str
    """ Operator that can handle import files with the extensions given in bl_file_extensions

    :type: str
    """

    bl_label: str
    """ The file handler label

    :type: str
    """

    @classmethod
    def poll_drop(cls, context: Context | None) -> bool:
        """If this method returns True, can be used to handle the drop of a drag-and-drop action

        :param context:
        :type context: Context | None
        :return:
        :rtype: bool
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

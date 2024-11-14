import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .keying_set import KeyingSet
from .context import Context

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyingSetInfo(bpy_struct):
    """Callback function defines for builtin Keying Sets"""

    bl_description: str
    """ A short description of the keying set

    :type: str
    """

    bl_idname: str
    """ If this is set, the Keying Set gets a custom ID, otherwise it takes the name of the class used to define the Keying Set (for example, if the class name is "BUILTIN_KSI_location", and bl_idname is not set by the script, then bl_idname = "BUILTIN_KSI_location")

    :type: str
    """

    bl_label: str
    """ 

    :type: str
    """

    bl_options: typing.Any
    """ Keying Set options to use when inserting keyframes"""

    def poll(self, context: Context | None) -> bool:
        """Test if Keying Set can be used or not

        :param context:
        :type context: Context | None
        :return:
        :rtype: bool
        """
        ...

    def iterator(self, context: Context | None, ks: KeyingSet | None):
        """Call generate() on the structs which have properties to be keyframed

        :param context:
        :type context: Context | None
        :param ks:
        :type ks: KeyingSet | None
        """
        ...

    def generate(self, context: Context | None, ks: KeyingSet | None, data: typing.Any):
        """Add Paths to the Keying Set to keyframe the properties of the given data

        :param context:
        :type context: Context | None
        :param ks:
        :type ks: KeyingSet | None
        :param data:
        :type data: typing.Any
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

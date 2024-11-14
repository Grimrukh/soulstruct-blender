import typing
import collections.abc
import mathutils
from .key_map import KeyMap
from .gizmos import Gizmos
from .struct import Struct
from .gizmo import Gizmo
from .bpy_struct import bpy_struct
from .key_config import KeyConfig
from .context import Context

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class GizmoGroup(bpy_struct):
    """Storage of an operator being executed, or registered after execution"""

    bl_idname: str
    """ 

    :type: str
    """

    bl_label: str
    """ 

    :type: str
    """

    bl_options: set[str]
    """ Options for this operator type

    :type: set[str]
    """

    bl_owner_id: str
    """ 

    :type: str
    """

    bl_region_type: str
    """ The region where the panel is going to be used in

    :type: str
    """

    bl_space_type: str
    """ The space where the panel is going to be used in

    :type: str
    """

    gizmos: Gizmos
    """ List of gizmos in the Gizmo Map

    :type: Gizmos
    """

    has_reports: bool
    """ GizmoGroup has a set of reports (warnings and errors) from last execution

    :type: bool
    """

    name: str
    """ 

    :type: str
    """

    @classmethod
    def poll(cls, context: Context) -> bool:
        """Test if the gizmo group can be called or not

        :param context:
        :type context: Context
        :return:
        :rtype: bool
        """
        ...

    @classmethod
    def setup_keymap(cls, keyconfig: KeyConfig) -> KeyMap:
        """Initialize keymaps for this gizmo group, use fallback keymap when not present

        :param keyconfig:
        :type keyconfig: KeyConfig
        :return:
        :rtype: KeyMap
        """
        ...

    def setup(self, context: Context):
        """Create gizmos function for the gizmo group

        :param context:
        :type context: Context
        """
        ...

    def refresh(self, context: Context):
        """Refresh data (called on common state changes such as selection)

        :param context:
        :type context: Context
        """
        ...

    def draw_prepare(self, context: Context):
        """Run before each redraw

        :param context:
        :type context: Context
        """
        ...

    def invoke_prepare(self, context: Context, gizmo: Gizmo):
        """Run before invoke

        :param context:
        :type context: Context
        :param gizmo:
        :type gizmo: Gizmo
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

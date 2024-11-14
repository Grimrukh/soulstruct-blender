import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .bpy_struct import bpy_struct
from .operator_properties import OperatorProperties
from .key_config import KeyConfig

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class KeyConfigurations(bpy_prop_collection[KeyConfig], bpy_struct):
    """Collection of KeyConfigs"""

    active: KeyConfig | None
    """ Active key configuration (preset)

    :type: KeyConfig | None
    """

    addon: KeyConfig
    """ Key configuration that can be extended by add-ons, and is added to the active configuration when handling events

    :type: KeyConfig
    """

    default: KeyConfig
    """ Default builtin key configuration

    :type: KeyConfig
    """

    user: KeyConfig
    """ Final key configuration that combines keymaps from the active and add-on configurations, and can be edited by the user

    :type: KeyConfig
    """

    def new(self, name: str | typing.Any) -> KeyConfig:
        """new

        :param name: Name
        :type name: str | typing.Any
        :return: Key Configuration, Added key configuration
        :rtype: KeyConfig
        """
        ...

    def remove(self, keyconfig: KeyConfig):
        """remove

        :param keyconfig: Key Configuration, Removed key configuration
        :type keyconfig: KeyConfig
        """
        ...

    def find_item_from_operator(
        self,
        idname: str | typing.Any,
        context: str | None = "INVOKE_DEFAULT",
        properties: OperatorProperties | None = None,
        include: typing.Any | None = {"ACTIONZONE", "KEYBOARD", "MOUSE", "NDOF"},
        exclude: typing.Any | None = {},
    ):
        """find_item_from_operator

                :param idname: Operator Identifier
                :type idname: str | typing.Any
                :param context: context
                :type context: str | None
                :param properties:
                :type properties: OperatorProperties | None
                :param include: Include
                :type include: typing.Any | None
                :param exclude: Exclude
                :type exclude: typing.Any | None
                :return: keymap, `KeyMap`

        item, `KeyMapItem`
        """
        ...

    def update(self, keep_properties: bool | typing.Any | None = False):
        """update

        :param keep_properties: Keep Properties, Operator properties are kept to allow the operators to be registered again in the future
        :type keep_properties: bool | typing.Any | None
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

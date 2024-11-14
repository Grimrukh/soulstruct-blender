import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Property(bpy_struct):
    """RNA property definition"""

    description: str
    """ Description of the property for tooltips

    :type: str
    """

    icon: str
    """ Icon of the item

    :type: str
    """

    identifier: str
    """ Unique name used in the code and scripting

    :type: str
    """

    is_animatable: bool
    """ Property is animatable through RNA

    :type: bool
    """

    is_argument_optional: bool
    """ True when the property is optional in a Python function implementing an RNA function

    :type: bool
    """

    is_enum_flag: bool
    """ True when multiple enums

    :type: bool
    """

    is_hidden: bool
    """ True when the property is hidden

    :type: bool
    """

    is_library_editable: bool
    """ Property is editable from linked instances (changes not saved)

    :type: bool
    """

    is_never_none: bool
    """ True when this value can't be set to None

    :type: bool
    """

    is_output: bool
    """ True when this property is an output value from an RNA function

    :type: bool
    """

    is_overridable: bool
    """ Property is overridable through RNA

    :type: bool
    """

    is_path_output: bool
    """ Property is a filename, filepath or directory output

    :type: bool
    """

    is_readonly: bool
    """ Property is editable through RNA

    :type: bool
    """

    is_registered: bool
    """ Property is registered as part of type registration

    :type: bool
    """

    is_registered_optional: bool
    """ Property is optionally registered as part of type registration

    :type: bool
    """

    is_required: bool
    """ False when this property is an optional argument in an RNA function

    :type: bool
    """

    is_runtime: bool
    """ Property has been dynamically created at runtime

    :type: bool
    """

    is_skip_preset: bool
    """ True when the property is not saved in presets

    :type: bool
    """

    is_skip_save: bool
    """ True when the property uses ghost values

    :type: bool
    """

    name: str
    """ Human readable name

    :type: str
    """

    srna: Struct
    """ Struct definition used for properties assigned to this item

    :type: Struct
    """

    subtype: str
    """ Semantic interpretation of the property

    :type: str
    """

    tags: set[str]
    """ Subset of tags (defined in parent struct) that are set for this property

    :type: set[str]
    """

    translation_context: str
    """ Translation context of the property's name

    :type: str
    """

    type: str
    """ Data type of the property

    :type: str
    """

    unit: str
    """ Type of units for this property

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

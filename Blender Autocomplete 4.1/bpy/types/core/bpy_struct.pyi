import typing
import collections.abc
import mathutils
from .f_curve import FCurve

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class bpy_struct(typing.Generic[GenericType1]):
    """built-in base class for all classes in bpy.types."""

    id_data: typing.Any
    """ The `bpy.types.ID` object this datablock is from or None, (not available for all data types)"""

    def as_pointer(self) -> int:
        """Returns the memory address which holds a pointer to Blender's internal data

        :return: int (memory address).
        :rtype: int
        """
        ...

    def driver_add(self, path: str | None, index: int | None = -1) -> FCurve:
        """Adds driver(s) to the given property

        :param path: path to the property to drive, analogous to the fcurve's data path.
        :type path: str | None
        :param index: array index of the property drive. Defaults to -1 for all indices or a single channel if the property is not an array.
        :type index: int | None
        :return: The driver(s) added.
        :rtype: FCurve
        """
        ...

    def driver_remove(self, path: str | None, index: int | None = -1) -> bool:
        """Remove driver(s) from the given property

        :param path: path to the property to drive, analogous to the fcurve's data path.
        :type path: str | None
        :param index: array index of the property drive. Defaults to -1 for all indices or a single channel if the property is not an array.
        :type index: int | None
        :return: Success of driver removal.
        :rtype: bool
        """
        ...

    def get(self, key: str | None, default=None):
        """Returns the value of the custom property assigned to key or default
        when not found (matches Python's dictionary function of the same name).

                :param key: The key associated with the custom property.
                :type key: str | None
                :param default: Optional argument for the value to return if
        key is not found.
        """
        ...

    def id_properties_clear(self):
        """

        :return: Remove the parent group for an RNA struct's custom IDProperties.
        """
        ...

    def id_properties_ensure(self):
        """

        :return: the parent group for an RNA struct's custom IDProperties.
        """
        ...

    def id_properties_ui(self, key):
        """

        :param key: String name of the property.
        :return: Return an object used to manage an IDProperty's UI data.
        """
        ...

    def is_property_hidden(self, property) -> bool:
        """Check if a property is hidden.

        :param property:
        :return: True when the property is hidden.
        :rtype: bool
        """
        ...

    def is_property_overridable_library(self, property) -> bool:
        """Check if a property is overridable.

        :param property:
        :return: True when the property is overridable.
        :rtype: bool
        """
        ...

    def is_property_readonly(self, property) -> bool:
        """Check if a property is readonly.

        :param property:
        :return: True when the property is readonly (not writable).
        :rtype: bool
        """
        ...

    def is_property_set(self, property, ghost: bool | None = True) -> bool:
        """Check if a property is set, use for testing operator properties.

                :param property:
                :param ghost: Used for operators that re-run with previous settings.
        In this case the property is not marked as set,
        yet the value from the previous execution is used.

        In rare cases you may want to set this option to false.
                :type ghost: bool | None
                :return: True when the property has been set.
                :rtype: bool
        """
        ...

    def items(self):
        """Returns the items of this objects custom properties (matches Python's
        dictionary function of the same name).

                :return: custom property key, value pairs.
        """
        ...

    def keyframe_delete(
        self,
        data_path: str | None,
        index: int | None = -1,
        frame: float | None = None,
        group: str | None = "",
    ) -> bool:
        """Remove a keyframe from this properties fcurve.

        :param data_path: path to the property to remove a key, analogous to the fcurve's data path.
        :type data_path: str | None
        :param index: array index of the property to remove a key. Defaults to -1 removing all indices or a single channel if the property is not an array.
        :type index: int | None
        :param frame: The frame on which the keyframe is deleted, defaulting to the current frame.
        :type frame: float | None
        :param group: The name of the group the F-Curve should be added to if it doesn't exist yet.
        :type group: str | None
        :return: Success of keyframe deletion.
        :rtype: bool
        """
        ...

    def keyframe_insert(
        self,
        data_path: str | None,
        index: int | None = -1,
        frame: float | None = None,
        group: str | None = "",
        options=None(),
    ) -> bool:
        """Insert a keyframe on the property given, adding fcurves and animation data when necessary.This is the most simple example of inserting a keyframe from python.Note that when keying data paths which contain nested properties this must be
        done from the `ID` subclass, in this case the `Armature` rather
        than the bone.

                :param data_path: path to the property to key, analogous to the fcurve's data path.
                :type data_path: str | None
                :param index: array index of the property to key.
        Defaults to -1 which will key all indices or a single channel if the property is not an array.
                :type index: int | None
                :param frame: The frame on which the keyframe is inserted, defaulting to the current frame.
                :type frame: float | None
                :param group: The name of the group the F-Curve should be added to if it doesn't exist yet.
                :type group: str | None
                :param options: Optional set of flags:

        INSERTKEY_NEEDED Only insert keyframes where they're needed in the relevant F-Curves.

        INSERTKEY_VISUAL Insert keyframes based on 'visual transforms'.

        INSERTKEY_XYZ_TO_RGB This flag is no longer in use, and is here so that code that uses it doesn't break. The XYZ=RGB coloring is determined by the animation preferences.

        INSERTKEY_REPLACE Only replace already existing keyframes.

        INSERTKEY_AVAILABLE Only insert into already existing F-Curves.

        INSERTKEY_CYCLE_AWARE Take cyclic extrapolation into account (Cycle-Aware Keying option).
                :return: Success of keyframe insertion.
                :rtype: bool
        """
        ...

    def keys(self):
        """Returns the keys of this objects custom properties (matches Python's
        dictionary function of the same name).

                :return: custom property keys.
        """
        ...

    def path_from_id(self, property: str | None = "") -> str:
        """Returns the data path from the ID to this object (string).

                :param property: Optional property name which can be used if the path is
        to a property of this object.
                :type property: str | None
                :return: The path from `bpy.types.bpy_struct.id_data`
        to this struct and property (when given).
                :rtype: str
        """
        ...

    def path_resolve(self, path: str | None, coerce: bool | None = True):
        """Returns the property from the path, raise an exception when not found.

                :param path: path which this property resolves.
                :type path: str | None
                :param coerce: optional argument, when True, the property will be converted
        into its Python representation.
                :type coerce: bool | None
        """
        ...

    def pop(self, key: str | None, default=None):
        """Remove and return the value of the custom property assigned to key or default
        when not found (matches Python's dictionary function of the same name).

                :param key: The key associated with the custom property.
                :type key: str | None
                :param default: Optional argument for the value to return if
        key is not found.
        """
        ...

    def property_overridable_library_set(self, property, overridable) -> bool:
        """Define a property as overridable or not (only for custom properties!).

        :param property:
        :param overridable:
        :return: True when the overridable status of the property was successfully set.
        :rtype: bool
        """
        ...

    def property_unset(self, property):
        """Unset a property, will use default value afterward.

        :param property:
        """
        ...

    def type_recast(self):
        """Return a new instance, this is needed because types
        such as textures can be changed at runtime.

                :return: a new instance of this object with the type initialized again.
        """
        ...

    def values(self):
        """Returns the values of this objects custom properties (matches Python's
        dictionary function of the same name).

                :return: custom property values.
        """
        ...

    def __getitem__(self, key: int | str) -> typing.Any:
        """

        :param key:
        :type key: int | str
        :return:
        :rtype: typing.Any
        """
        ...

    def __setitem__(self, key: int | str, value: typing.Any):
        """

        :param key:
        :type key: int | str
        :param value:
        :type value: typing.Any
        """
        ...

    def __delitem__(self, key: int | str):
        """

        :param key:
        :type key: int | str
        """
        ...

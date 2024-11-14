import typing
import collections.abc
import mathutils

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class bpy_prop_array(typing.Generic[GenericType1]):
    def __get__(self, instance, owner) -> bpy_prop_array[GenericType1]:
        """

        :param instance:
        :param owner:
        :return:
        :rtype: bpy_prop_array[GenericType1]
        """
        ...

    def __set__(self, instance, value: collections.abc.Iterable[GenericType1]):
        """

        :param instance:
        :param value:
        :type value: collections.abc.Iterable[GenericType1]
        """
        ...

    def foreach_get(self, seq: collections.abc.MutableSequence[GenericType1]):
        """

        :param seq:
        :type seq: collections.abc.MutableSequence[GenericType1]
        """
        ...

    def foreach_set(self, seq: typing.Sequence[GenericType1]):
        """

        :param seq:
        :type seq: typing.Sequence[GenericType1]
        """
        ...

    @typing.overload
    def __getitem__(self, key: int) -> GenericType1:
        """

        :param key:
        :type key: int
        :return:
        :rtype: GenericType1
        """
        ...

    @typing.overload
    def __getitem__(self, key: slice) -> tuple[GenericType1]:
        """

        :param key:
        :type key: slice
        :return:
        :rtype: tuple[GenericType1]
        """
        ...

    def __getitem__(self, key: int | slice) -> GenericType1 | tuple[GenericType1]:
        """

        :param key:
        :type key: int | slice
        :return:
        :rtype: GenericType1 | tuple[GenericType1]
        """
        ...

    @typing.overload
    def __setitem__(self, key: int, value: GenericType1):
        """

        :param key:
        :type key: int
        :param value:
        :type value: GenericType1
        """
        ...

    @typing.overload
    def __setitem__(self, key: slice, value: tuple[GenericType1]):
        """

        :param key:
        :type key: slice
        :param value:
        :type value: tuple[GenericType1]
        """
        ...

    def __setitem__(self, key: int | slice, value: GenericType1 | tuple[GenericType1]):
        """

        :param key:
        :type key: int | slice
        :param value:
        :type value: GenericType1 | tuple[GenericType1]
        """
        ...

    def __delitem__(self, key: int | slice):
        """

        :param key:
        :type key: int | slice
        """
        ...

    def __iter__(self) -> collections.abc.Iterator[GenericType1]:
        """

        :return:
        :rtype: collections.abc.Iterator[GenericType1]
        """
        ...

    def __next__(self) -> GenericType1:
        """

        :return:
        :rtype: GenericType1
        """
        ...

    def __len__(self) -> int:
        """

        :return:
        :rtype: int
        """
        ...

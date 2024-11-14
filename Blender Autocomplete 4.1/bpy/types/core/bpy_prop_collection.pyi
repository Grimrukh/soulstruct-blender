import typing
import collections.abc
import mathutils

import numpy as np

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class bpy_prop_collection(typing.Generic[GenericType1]):
    """built-in class used for all collections."""

    def find(self, key: str | None) -> int:
        """Returns the index of a key in a collection or -1 when not found
        (matches Python's string find function of the same name).

                :param key: The identifier for the collection member.
                :type key: str | None
                :return: index of the key.
                :rtype: int
        """
        ...

    def foreach_get(
        self,
        attr: str,
        seq: typing.Union[
            collections.abc.MutableSequence[bool],
            collections.abc.MutableSequence[int],
            collections.abc.MutableSequence[float],
            np.ndarray,
        ],
    ):
        """This is a function to give fast access to attributes within a collection.Only works for 'basic type' properties (bool, int and float)!
        Multi-dimensional arrays (like array of vectors) will be flattened into seq.

                :param attr:
                :type attr: str
                :param seq:
                :type seq: collections.abc.MutableSequence[bool] | collections.abc.MutableSequence[int] | collections.abc.MutableSequence[float]
        """
        ...

    def foreach_set(
        self,
        attr: str,
        seq: typing.Union[
            collections.abc.MutableSequence[bool],
            collections.abc.MutableSequence[int],
            collections.abc.MutableSequence[float],
            np.ndarray,
        ],
    ):
        """This is a function to give fast access to attributes within a collection.Only works for 'basic type' properties (bool, int and float)!
        seq must be uni-dimensional, multi-dimensional arrays (like array of vectors) will be re-created from it.

                :param attr:
                :type attr: str
                :param seq:
                :type seq: collections.abc.Sequence[bool] | collections.abc.Sequence[int] | collections.abc.Sequence[float]
        """
        ...

    def get(
        self, key: str | None, default: GenericType2 = None
    ) -> GenericType1 | GenericType2:
        """Returns the value of the item assigned to key or default when not found
        (matches Python's dictionary function of the same name).

                :param key: The identifier for the collection member.
                :type key: str | None
                :param default: Optional argument for the value to return if
        key is not found.
                :type default: GenericType2
                :return:
                :rtype: GenericType1 | GenericType2
        """
        ...

    def items(self) -> list[tuple[str, GenericType1]]:
        """Return the identifiers of collection members
        (matching Python's dict.items() functionality).

                :return:
                :rtype: list[tuple[str, GenericType1]]
        """
        ...

    def keys(self) -> list[str]:
        """Return the identifiers of collection members
        (matching Python's dict.keys() functionality).

                :return: the identifiers for each member of this collection.
                :rtype: list[str]
        """
        ...

    def values(self) -> list[GenericType1]:
        """Return the values of collection
        (matching Python's dict.values() functionality).

                :return:
                :rtype: list[GenericType1]
        """
        ...

    @typing.overload
    def __getitem__(self, key: int | str) -> GenericType1:
        """

        :param key:
        :type key: int | str
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

    def __getitem__(self, key: int | str | slice) -> GenericType1 | tuple[GenericType1]:
        """

        :param key:
        :type key: int | str | slice
        :return:
        :rtype: GenericType1 | tuple[GenericType1]
        """
        ...

    @typing.overload
    def __setitem__(self, key: int | str, value: GenericType1):
        """

        :param key:
        :type key: int | str
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

    def __setitem__(
        self, key: int | str | slice, value: GenericType1 | tuple[GenericType1]
    ):
        """

        :param key:
        :type key: int | str | slice
        :param value:
        :type value: GenericType1 | tuple[GenericType1]
        """
        ...

    def __delitem__(self, key: int | str | slice):
        """

        :param key:
        :type key: int | str | slice
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

    def __contains__(self, key: str | tuple[str, ...]) -> bool:
        """

        :param key:
        :type key: str | tuple[str, ...]
        :return:
        :rtype: bool
        """
        ...

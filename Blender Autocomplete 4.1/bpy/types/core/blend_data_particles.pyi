import typing
import collections.abc
import mathutils
from .bpy_prop_collection import bpy_prop_collection
from .struct import Struct
from .particle_settings import ParticleSettings
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendDataParticles(bpy_prop_collection[ParticleSettings], bpy_struct):
    """Collection of particle settings"""

    def new(self, name: str | typing.Any) -> ParticleSettings:
        """Add a new particle settings instance to the main database

        :param name: New name for the data-block
        :type name: str | typing.Any
        :return: New particle settings data-block
        :rtype: ParticleSettings
        """
        ...

    def remove(
        self,
        particle: ParticleSettings,
        do_unlink: bool | typing.Any | None = True,
        do_id_user: bool | typing.Any | None = True,
        do_ui_user: bool | typing.Any | None = True,
    ):
        """Remove a particle settings instance from the current blendfile

        :param particle: Particle Settings to remove
        :type particle: ParticleSettings
        :param do_unlink: Unlink all usages of those particle settings before deleting them
        :type do_unlink: bool | typing.Any | None
        :param do_id_user: Decrement user counter of all datablocks used by this particle settings
        :type do_id_user: bool | typing.Any | None
        :param do_ui_user: Make sure interface does not reference this particle settings
        :type do_ui_user: bool | typing.Any | None
        """
        ...

    def tag(self, value: bool | None):
        """tag

        :param value: Value
        :type value: bool | None
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

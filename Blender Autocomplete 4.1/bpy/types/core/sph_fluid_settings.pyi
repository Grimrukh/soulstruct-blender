import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SPHFluidSettings(bpy_struct):
    """Settings for particle fluids physics"""

    buoyancy: float
    """ Artificial buoyancy force in negative gravity direction based on pressure differences inside the fluid

    :type: float
    """

    fluid_radius: float
    """ Fluid interaction radius

    :type: float
    """

    linear_viscosity: float
    """ Linear viscosity

    :type: float
    """

    plasticity: float
    """ How much the spring rest length can change after the elastic limit is crossed

    :type: float
    """

    repulsion: float
    """ How strongly the fluid tries to keep from clustering (factor of stiffness)

    :type: float
    """

    rest_density: float
    """ Fluid rest density

    :type: float
    """

    rest_length: float
    """ Spring rest length (factor of particle radius)

    :type: float
    """

    solver: str
    """ The code used to calculate internal forces on particles

    :type: str
    """

    spring_force: float
    """ Spring force

    :type: float
    """

    spring_frames: int
    """ Create springs for this number of frames since particles birth (0 is always)

    :type: int
    """

    stiff_viscosity: float
    """ Creates viscosity for expanding fluid

    :type: float
    """

    stiffness: float
    """ How incompressible the fluid is (speed of sound)

    :type: float
    """

    use_factor_density: bool
    """ Density is calculated as a factor of default density (depends on particle size)

    :type: bool
    """

    use_factor_radius: bool
    """ Interaction radius is a factor of 4 * particle size

    :type: bool
    """

    use_factor_repulsion: bool
    """ Repulsion is a factor of stiffness

    :type: bool
    """

    use_factor_rest_length: bool
    """ Spring rest length is a factor of 2 * particle size

    :type: bool
    """

    use_factor_stiff_viscosity: bool
    """ Stiff viscosity is a factor of normal viscosity

    :type: bool
    """

    use_initial_rest_length: bool
    """ Use the initial length as spring rest length instead of 2 * particle size

    :type: bool
    """

    use_viscoelastic_springs: bool
    """ Use viscoelastic springs instead of Hooke's springs

    :type: bool
    """

    yield_ratio: float
    """ How much the spring has to be stretched/compressed in order to change its rest length

    :type: float
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

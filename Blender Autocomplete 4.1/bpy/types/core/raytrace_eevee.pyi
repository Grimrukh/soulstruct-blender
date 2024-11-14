import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RaytraceEEVEE(bpy_struct):
    denoise_bilateral: bool
    """ Blur the resolved radiance using a bilateral filter

    :type: bool
    """

    denoise_spatial: bool
    """ Reuse neighbor pixels' rays

    :type: bool
    """

    denoise_temporal: bool
    """ Accumulate samples by reprojecting last tracing results

    :type: bool
    """

    resolution_scale: str
    """ Number of rays per pixel

    :type: str
    """

    sample_clamp: float
    """ Clamp ray intensity to reduce noise (0 to disable)

    :type: float
    """

    screen_trace_max_roughness: float
    """ Maximum roughness to use the tracing pipeline for. Higher roughness surfaces will use horizon scan. A value of 1 will disable horizon scan

    :type: float
    """

    screen_trace_quality: float
    """ Precision of the screen space ray-tracing

    :type: float
    """

    screen_trace_thickness: float
    """ Surface thickness used to detect intersection when using screen-tracing

    :type: float
    """

    use_denoise: bool
    """ Enable noise reduction techniques for raytraced effects

    :type: bool
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

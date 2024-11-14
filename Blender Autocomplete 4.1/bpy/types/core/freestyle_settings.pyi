import typing
import collections.abc
import mathutils
from .struct import Struct
from .linesets import Linesets
from .bpy_struct import bpy_struct
from .freestyle_modules import FreestyleModules

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FreestyleSettings(bpy_struct):
    """Freestyle settings for a ViewLayer data-block"""

    as_render_pass: bool
    """ Renders Freestyle output to a separate pass instead of overlaying it on the Combined pass

    :type: bool
    """

    crease_angle: float
    """ Angular threshold for detecting crease edges

    :type: float
    """

    kr_derivative_epsilon: float
    """ Kr derivative epsilon for computing suggestive contours

    :type: float
    """

    linesets: Linesets
    """ 

    :type: Linesets
    """

    mode: str
    """ Select the Freestyle control mode

    :type: str
    """

    modules: FreestyleModules
    """ A list of style modules (to be applied from top to bottom)

    :type: FreestyleModules
    """

    sphere_radius: float
    """ Sphere radius for computing curvatures

    :type: float
    """

    use_culling: bool
    """ If enabled, out-of-view edges are ignored

    :type: bool
    """

    use_material_boundaries: bool
    """ Enable material boundaries

    :type: bool
    """

    use_ridges_and_valleys: bool
    """ Enable ridges and valleys

    :type: bool
    """

    use_smoothness: bool
    """ Take face smoothness into account in view map calculation

    :type: bool
    """

    use_suggestive_contours: bool
    """ Enable suggestive contours

    :type: bool
    """

    use_view_map_cache: bool
    """ Keep the computed view map and avoid recalculating it if mesh geometry is unchanged

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

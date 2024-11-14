import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class SpaceUVEditor(bpy_struct):
    """UV editor data for the image editor space"""

    custom_grid_subdivisions: bpy_prop_array[int]
    """ Number of grid units in UV space that make one UV Unit

    :type: bpy_prop_array[int]
    """

    display_stretch_type: str
    """ Type of stretch to display

    :type: str
    """

    edge_display_type: str
    """ Display style for UV edges

    :type: str
    """

    grid_shape_source: str
    """ Specify source for the grid shape

    :type: str
    """

    lock_bounds: bool
    """ Constraint to stay within the image bounds while editing

    :type: bool
    """

    pixel_round_mode: str
    """ Round UVs to pixels while editing

    :type: str
    """

    show_faces: bool
    """ Display faces over the image

    :type: bool
    """

    show_grid_over_image: bool
    """ Show the grid over the image

    :type: bool
    """

    show_metadata: bool
    """ Display metadata properties of the image

    :type: bool
    """

    show_modified_edges: bool
    """ Display edges after modifiers are applied

    :type: bool
    """

    show_pixel_coords: bool
    """ Display UV coordinates in pixels rather than from 0.0 to 1.0

    :type: bool
    """

    show_stretch: bool
    """ Display faces colored according to the difference in shape between UVs and their 3D coordinates (blue for low distortion, red for high distortion)

    :type: bool
    """

    show_texpaint: bool
    """ Display overlay of texture paint UV layer

    :type: bool
    """

    tile_grid_shape: bpy_prop_array[int]
    """ How many tiles will be shown in the background

    :type: bpy_prop_array[int]
    """

    use_live_unwrap: bool
    """ Continuously unwrap the selected UV island while transforming pinned vertices

    :type: bool
    """

    uv_opacity: float
    """ Opacity of UV overlays

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

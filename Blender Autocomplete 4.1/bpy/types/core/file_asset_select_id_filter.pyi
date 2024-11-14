import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FileAssetSelectIDFilter(bpy_struct):
    """Which asset types to show/hide, when browsing an asset library"""

    experimental_filter_armature: bool
    """ Show Armature data-blocks

    :type: bool
    """

    experimental_filter_brush: bool
    """ Show Brushes data-blocks

    :type: bool
    """

    experimental_filter_cachefile: bool
    """ Show Cache File data-blocks

    :type: bool
    """

    experimental_filter_camera: bool
    """ Show Camera data-blocks

    :type: bool
    """

    experimental_filter_curve: bool
    """ Show Curve data-blocks

    :type: bool
    """

    experimental_filter_curves: bool
    """ Show/hide Curves data-blocks

    :type: bool
    """

    experimental_filter_font: bool
    """ Show Font data-blocks

    :type: bool
    """

    experimental_filter_grease_pencil: bool
    """ Show Grease pencil data-blocks

    :type: bool
    """

    experimental_filter_image: bool
    """ Show Image data-blocks

    :type: bool
    """

    experimental_filter_lattice: bool
    """ Show Lattice data-blocks

    :type: bool
    """

    experimental_filter_light: bool
    """ Show Light data-blocks

    :type: bool
    """

    experimental_filter_light_probe: bool
    """ Show Light Probe data-blocks

    :type: bool
    """

    experimental_filter_linestyle: bool
    """ Show Freestyle's Line Style data-blocks

    :type: bool
    """

    experimental_filter_mask: bool
    """ Show Mask data-blocks

    :type: bool
    """

    experimental_filter_mesh: bool
    """ Show Mesh data-blocks

    :type: bool
    """

    experimental_filter_metaball: bool
    """ Show Metaball data-blocks

    :type: bool
    """

    experimental_filter_movie_clip: bool
    """ Show Movie Clip data-blocks

    :type: bool
    """

    experimental_filter_paint_curve: bool
    """ Show Paint Curve data-blocks

    :type: bool
    """

    experimental_filter_palette: bool
    """ Show Palette data-blocks

    :type: bool
    """

    experimental_filter_particle_settings: bool
    """ Show Particle Settings data-blocks

    :type: bool
    """

    experimental_filter_pointcloud: bool
    """ Show/hide Point Cloud data-blocks

    :type: bool
    """

    experimental_filter_scene: bool
    """ Show Scene data-blocks

    :type: bool
    """

    experimental_filter_sound: bool
    """ Show Sound data-blocks

    :type: bool
    """

    experimental_filter_speaker: bool
    """ Show Speaker data-blocks

    :type: bool
    """

    experimental_filter_text: bool
    """ Show Text data-blocks

    :type: bool
    """

    experimental_filter_texture: bool
    """ Show Texture data-blocks

    :type: bool
    """

    experimental_filter_volume: bool
    """ Show/hide Volume data-blocks

    :type: bool
    """

    experimental_filter_work_space: bool
    """ Show workspace data-blocks

    :type: bool
    """

    filter_action: bool
    """ Show Action data-blocks

    :type: bool
    """

    filter_group: bool
    """ Show Collection data-blocks

    :type: bool
    """

    filter_material: bool
    """ Show Material data-blocks

    :type: bool
    """

    filter_node_tree: bool
    """ Show Node Tree data-blocks

    :type: bool
    """

    filter_object: bool
    """ Show Object data-blocks

    :type: bool
    """

    filter_world: bool
    """ Show World data-blocks

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

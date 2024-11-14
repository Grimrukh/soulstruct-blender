import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class DopeSheet(bpy_struct):
    """Settings for filtering the channels shown in animation editors"""

    filter_collection: Collection
    """ Collection that included object should be a member of

    :type: Collection
    """

    filter_fcurve_name: str
    """ F-Curve live filtering string

    :type: str
    """

    filter_text: str
    """ Live filtering string

    :type: str
    """

    show_armatures: bool
    """ Include visualization of armature related animation data

    :type: bool
    """

    show_cache_files: bool
    """ Include visualization of cache file related animation data

    :type: bool
    """

    show_cameras: bool
    """ Include visualization of camera related animation data

    :type: bool
    """

    show_curves: bool
    """ Include visualization of curve related animation data

    :type: bool
    """

    show_datablock_filters: bool
    """ Show options for whether channels related to certain types of data are included

    :type: bool
    """

    show_driver_fallback_as_error: bool
    """ Include drivers that relied on any fallback values for their evaluation in the Only Show Errors filter, even if the driver evaluation succeeded

    :type: bool
    """

    show_expanded_summary: bool
    """ Collapse summary when shown, so all other channels get hidden (Dope Sheet editors only)

    :type: bool
    """

    show_gpencil: bool
    """ Include visualization of Grease Pencil related animation data and frames

    :type: bool
    """

    show_hair_curves: bool
    """ Include visualization of hair related animation data

    :type: bool
    """

    show_hidden: bool
    """ Include channels from objects/bone that are not visible

    :type: bool
    """

    show_lattices: bool
    """ Include visualization of lattice related animation data

    :type: bool
    """

    show_lights: bool
    """ Include visualization of light related animation data

    :type: bool
    """

    show_linestyles: bool
    """ Include visualization of Line Style related Animation data

    :type: bool
    """

    show_materials: bool
    """ Include visualization of material related animation data

    :type: bool
    """

    show_meshes: bool
    """ Include visualization of mesh related animation data

    :type: bool
    """

    show_metaballs: bool
    """ Include visualization of metaball related animation data

    :type: bool
    """

    show_missing_nla: bool
    """ Include animation data-blocks with no NLA data (NLA editor only)

    :type: bool
    """

    show_modifiers: bool
    """ Include visualization of animation data related to data-blocks linked to modifiers

    :type: bool
    """

    show_movieclips: bool
    """ Include visualization of movie clip related animation data

    :type: bool
    """

    show_nodes: bool
    """ Include visualization of node related animation data

    :type: bool
    """

    show_only_errors: bool
    """ Only include F-Curves and drivers that are disabled or have errors

    :type: bool
    """

    show_only_selected: bool
    """ Only include channels relating to selected objects and data

    :type: bool
    """

    show_particles: bool
    """ Include visualization of particle related animation data

    :type: bool
    """

    show_pointclouds: bool
    """ Include visualization of point cloud related animation data

    :type: bool
    """

    show_scenes: bool
    """ Include visualization of scene related animation data

    :type: bool
    """

    show_shapekeys: bool
    """ Include visualization of shape key related animation data

    :type: bool
    """

    show_speakers: bool
    """ Include visualization of speaker related animation data

    :type: bool
    """

    show_summary: bool
    """ Display an additional 'summary' line (Dope Sheet editors only)

    :type: bool
    """

    show_textures: bool
    """ Include visualization of texture related animation data

    :type: bool
    """

    show_transforms: bool
    """ Include visualization of object-level animation data (mostly transforms)

    :type: bool
    """

    show_volumes: bool
    """ Include visualization of volume related animation data

    :type: bool
    """

    show_worlds: bool
    """ Include visualization of world related animation data

    :type: bool
    """

    source: ID
    """ ID-Block representing source data, usually ID_SCE (i.e. Scene)

    :type: ID
    """

    use_datablock_sort: bool
    """ Alphabetically sorts data-blocks - mainly objects in the scene (disable to increase viewport speed)

    :type: bool
    """

    use_filter_invert: bool
    """ Invert filter search

    :type: bool
    """

    use_multi_word_filter: bool
    """ Perform fuzzy/multi-word matching.
Warning: May be slow

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

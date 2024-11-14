import typing
import collections.abc
import mathutils
from .blend_data_brushes import BlendDataBrushes
from .blend_data_hair_curves import BlendDataHairCurves
from .blend_data_lattices import BlendDataLattices
from .blend_data_window_managers import BlendDataWindowManagers
from .blend_data_armatures import BlendDataArmatures
from .blend_data_materials import BlendDataMaterials
from .blend_data_point_clouds import BlendDataPointClouds
from .blend_data_lights import BlendDataLights
from .blend_data_textures import BlendDataTextures
from .blend_data_cache_files import BlendDataCacheFiles
from .blend_data_images import BlendDataImages
from .struct import Struct
from .blend_data_node_trees import BlendDataNodeTrees
from .blend_data_libraries import BlendDataLibraries
from .blend_data_curves import BlendDataCurves
from .blend_data_meshes import BlendDataMeshes
from .blend_data_actions import BlendDataActions
from .blend_data_probes import BlendDataProbes
from .blend_data_paint_curves import BlendDataPaintCurves
from .blend_data_palettes import BlendDataPalettes
from .blend_data_worlds import BlendDataWorlds
from .blend_data_collections import BlendDataCollections
from .bpy_prop_collection import bpy_prop_collection
from .blend_data_work_spaces import BlendDataWorkSpaces
from .blend_data_volumes import BlendDataVolumes
from .key import Key
from .blend_data_objects import BlendDataObjects
from .blend_data_particles import BlendDataParticles
from .blend_data_meta_balls import BlendDataMetaBalls
from .blend_data_grease_pencils import BlendDataGreasePencils
from .blend_data_scenes import BlendDataScenes
from .bpy_prop_array import bpy_prop_array
from .blend_data_cameras import BlendDataCameras
from .blend_data_texts import BlendDataTexts
from .blend_data_line_styles import BlendDataLineStyles
from .blend_data_screens import BlendDataScreens
from .blend_data_speakers import BlendDataSpeakers
from .blend_data_fonts import BlendDataFonts
from .bpy_struct import bpy_struct
from .blend_data_movie_clips import BlendDataMovieClips
from .blend_data_masks import BlendDataMasks
from .blend_data_sounds import BlendDataSounds

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class BlendData(bpy_struct):
    """Main data structure representing a .blend file and all its data-blocks"""

    actions: BlendDataActions
    """ Action data-blocks

    :type: BlendDataActions
    """

    armatures: BlendDataArmatures
    """ Armature data-blocks

    :type: BlendDataArmatures
    """

    brushes: BlendDataBrushes
    """ Brush data-blocks

    :type: BlendDataBrushes
    """

    cache_files: BlendDataCacheFiles
    """ Cache Files data-blocks

    :type: BlendDataCacheFiles
    """

    cameras: BlendDataCameras
    """ Camera data-blocks

    :type: BlendDataCameras
    """

    collections: BlendDataCollections
    """ Collection data-blocks

    :type: BlendDataCollections
    """

    curves: BlendDataCurves
    """ Curve data-blocks

    :type: BlendDataCurves
    """

    filepath: str
    """ Path to the .blend file

    :type: str
    """

    fonts: BlendDataFonts
    """ Vector font data-blocks

    :type: BlendDataFonts
    """

    grease_pencils: BlendDataGreasePencils
    """ Grease Pencil data-blocks

    :type: BlendDataGreasePencils
    """

    hair_curves: BlendDataHairCurves
    """ Hair curve data-blocks

    :type: BlendDataHairCurves
    """

    images: BlendDataImages
    """ Image data-blocks

    :type: BlendDataImages
    """

    is_dirty: bool
    """ Have recent edits been saved to disk

    :type: bool
    """

    is_saved: bool
    """ Has the current session been saved to disk as a .blend file

    :type: bool
    """

    lattices: BlendDataLattices
    """ Lattice data-blocks

    :type: BlendDataLattices
    """

    libraries: BlendDataLibraries
    """ Library data-blocks

    :type: BlendDataLibraries
    """

    lightprobes: BlendDataProbes
    """ Light Probe data-blocks

    :type: BlendDataProbes
    """

    lights: BlendDataLights
    """ Light data-blocks

    :type: BlendDataLights
    """

    linestyles: BlendDataLineStyles
    """ Line Style data-blocks

    :type: BlendDataLineStyles
    """

    masks: BlendDataMasks
    """ Masks data-blocks

    :type: BlendDataMasks
    """

    materials: BlendDataMaterials
    """ Material data-blocks

    :type: BlendDataMaterials
    """

    meshes: BlendDataMeshes
    """ Mesh data-blocks

    :type: BlendDataMeshes
    """

    metaballs: BlendDataMetaBalls
    """ Metaball data-blocks

    :type: BlendDataMetaBalls
    """

    movieclips: BlendDataMovieClips
    """ Movie Clip data-blocks

    :type: BlendDataMovieClips
    """

    node_groups: BlendDataNodeTrees
    """ Node group data-blocks

    :type: BlendDataNodeTrees
    """

    objects: BlendDataObjects
    """ Object data-blocks

    :type: BlendDataObjects
    """

    paint_curves: BlendDataPaintCurves
    """ Paint Curves data-blocks

    :type: BlendDataPaintCurves
    """

    palettes: BlendDataPalettes
    """ Palette data-blocks

    :type: BlendDataPalettes
    """

    particles: BlendDataParticles
    """ Particle data-blocks

    :type: BlendDataParticles
    """

    pointclouds: BlendDataPointClouds
    """ Point cloud data-blocks

    :type: BlendDataPointClouds
    """

    scenes: BlendDataScenes
    """ Scene data-blocks

    :type: BlendDataScenes
    """

    screens: BlendDataScreens
    """ Screen data-blocks

    :type: BlendDataScreens
    """

    shape_keys: bpy_prop_collection[Key]
    """ Shape Key data-blocks

    :type: bpy_prop_collection[Key]
    """

    sounds: BlendDataSounds
    """ Sound data-blocks

    :type: BlendDataSounds
    """

    speakers: BlendDataSpeakers
    """ Speaker data-blocks

    :type: BlendDataSpeakers
    """

    texts: BlendDataTexts
    """ Text data-blocks

    :type: BlendDataTexts
    """

    textures: BlendDataTextures
    """ Texture data-blocks

    :type: BlendDataTextures
    """

    use_autopack: bool
    """ Automatically pack all external data into .blend file

    :type: bool
    """

    version: bpy_prop_array[int]
    """ File format version the .blend file was saved with

    :type: bpy_prop_array[int]
    """

    volumes: BlendDataVolumes
    """ Volume data-blocks

    :type: BlendDataVolumes
    """

    window_managers: BlendDataWindowManagers
    """ Window manager data-blocks

    :type: BlendDataWindowManagers
    """

    workspaces: BlendDataWorkSpaces
    """ Workspace data-blocks

    :type: BlendDataWorkSpaces
    """

    worlds: BlendDataWorlds
    """ World data-blocks

    :type: BlendDataWorlds
    """

    def batch_remove(self, ids):
        """Remove (delete) several IDs at once.WARNING: Considered experimental feature currently.Note that this function is quicker than individual calls to `remove()` (from `bpy.types.BlendData`
        ID collections), but less safe/versatile (it can break Blender, e.g. by removing all scenes...).

                :param ids: Iterables of IDs (types can be mixed).
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

    def orphans_purge(self):
        """Remove (delete) all IDs with no user.

        :return: The number of deleted IDs.
        """
        ...

    def temp_data(self, filepath: bytes | str | None = None) -> BlendData:
        """A context manager that temporarily creates blender file data.

        :param filepath: The file path for the newly temporary data. When None, the path of the currently open file is used.
        :type filepath: bytes | str | None
        :return: Blend file data which is freed once the context exists.
        :rtype: BlendData
        """
        ...

    def user_map(
        self,
        subset: collections.abc.Sequence | None,
        key_types: set[str] | None,
        value_types: set[str] | None,
    ) -> dict:
        """Returns a mapping of all ID data-blocks in current bpy.data to a set of all datablocks using them.For list of valid set members for key_types & value_types, see: `bpy.types.KeyingSetPath.id_type`.

        :param subset: When passed, only these data-blocks and their users will be included as keys/values in the map.
        :type subset: collections.abc.Sequence | None
        :param key_types: Filter the keys mapped by ID types.
        :type key_types: set[str] | None
        :param value_types: Filter the values in the set by ID types.
        :type value_types: set[str] | None
        :return: dictionary of `bpy.types.ID` instances, with sets of ID's as their values.
        :rtype: dict
        """
        ...

import typing
import collections.abc
import mathutils
from .color_managed_view_settings import ColorManagedViewSettings
from .anim_data import AnimData
from .rigid_body_world import RigidBodyWorld
from .scene_hydra import SceneHydra
from .keying_sets import KeyingSets
from .world import World
from .timeline_markers import TimelineMarkers
from .node_tree import NodeTree
from .unit_settings import UnitSettings
from .scene_display import SceneDisplay
from .struct import Struct
from .scene_gpencil import SceneGpencil
from .color_managed_display_settings import ColorManagedDisplaySettings
from .scene_objects import SceneObjects
from .keying_sets_all import KeyingSetsAll
from .color_managed_sequencer_colorspace_settings import ColorManagedSequencerColorspaceSettings
from .depsgraph import Depsgraph
from .bpy_prop_collection import bpy_prop_collection
from .view_layer import ViewLayer
from .object import Object
from .movie_clip import MovieClip
from .view_layers import ViewLayers
from .view3_d_cursor import View3DCursor
from .tool_settings import ToolSettings
from .collection import Collection
from .sequence_editor import SequenceEditor
from .bpy_struct import bpy_struct
from .transform_orientation_slot import TransformOrientationSlot
from .id import ID
from .scene_eevee import SceneEEVEE
from .render_settings import RenderSettings
from .display_safe_areas import DisplaySafeAreas
from .grease_pencil import GreasePencil

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")

if typing.TYPE_CHECKING:
    from io_soulstruct import *
    from experimental import *


class Scene(ID, bpy_struct):
    """Scene data-block, consisting in objects and defining time and render related settings"""

    # region Soulstruct Extensions
    soulstruct_settings: SoulstructSettings
    flver_import_settings: FLVERImportSettings
    flver_export_settings: FLVERExportSettings
    texture_export_settings: TextureExportSettings
    bake_lightmap_settings: BakeLightmapSettings
    flver_tool_settings: FLVERToolSettings
    flver_material_settings: FLVERMaterialSettings
    material_tool_settings: MaterialToolSettings
    map_collision_import_settings: MapCollisionImportSettings
    map_collision_tool_settings: MapCollisionToolSettings
    navmesh_face_settings: NavmeshFaceSettings
    nav_graph_compute_settings: NavGraphComputeSettings
    nvmhkt_import_settings: NVMHKTImportSettings
    mcg_draw_settings: MCGDrawSettings
    msb_import_settings: MSBImportSettings
    msb_export_settings: MSBExportSettings
    msb_part_creation_templates: MSBPartCreationTemplates
    find_msb_parts_pointer: MSBFindPartsPointer
    msb_tool_settings: MSBToolSettings
    region_draw_settings: RegionDrawSettings
    animation_import_settings: AnimationImportSettings
    animation_export_settings: AnimationExportSettings
    cutscene_import_settings: CutsceneImportSettings
    cutscene_export_settings: CutsceneExportSettings

    # Soulstruct Experimental Extensions
    material_debug_settings: MaterialDebugSettings
    map_progress_settings: MapProgressSettings
    # endregion

    active_clip: MovieClip | None
    """ Active Movie Clip that can be used by motion tracking constraints or as a camera's background image

    :type: MovieClip | None
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    audio_distance_model: str
    """ Distance model for distance attenuation calculation

    :type: str
    """

    audio_doppler_factor: float
    """ Pitch factor for Doppler effect calculation

    :type: float
    """

    audio_doppler_speed: float
    """ Speed of sound for Doppler effect calculation

    :type: float
    """

    audio_volume: float
    """ Audio volume

    :type: float
    """

    background_set: Scene
    """ Background set scene

    :type: Scene
    """

    camera: Object
    """ Active camera, used for rendering the scene

    :type: Object
    """

    collection: Collection
    """ Scene root collection that owns all the objects and other collections instantiated in the scene

    :type: Collection
    """

    cursor: View3DCursor
    """ 

    :type: View3DCursor
    """

    cycles: typing.Any
    """ Cycles render settings

    :type: typing.Any
    """

    cycles_curves: typing.Any
    """ Cycles curves rendering settings

    :type: typing.Any
    """

    display: SceneDisplay
    """ Scene display settings for 3D viewport

    :type: SceneDisplay
    """

    display_settings: ColorManagedDisplaySettings
    """ Settings of device saved image would be displayed on

    :type: ColorManagedDisplaySettings
    """

    eevee: SceneEEVEE
    """ EEVEE settings for the scene

    :type: SceneEEVEE
    """

    frame_current: int
    """ Current frame, to update animation data from Python frame_set() instead

    :type: int
    """

    frame_current_final: float
    """ Current frame with subframe and time remapping applied

    :type: float
    """

    frame_end: int
    """ Final frame of the playback/rendering range

    :type: int
    """

    frame_float: float
    """ 

    :type: float
    """

    frame_preview_end: int
    """ Alternative end frame for UI playback

    :type: int
    """

    frame_preview_start: int
    """ Alternative start frame for UI playback

    :type: int
    """

    frame_start: int
    """ First frame of the playback/rendering range

    :type: int
    """

    frame_step: int
    """ Number of frames to skip forward while rendering/playing back each frame

    :type: int
    """

    frame_subframe: float
    """ 

    :type: float
    """

    gravity: mathutils.Vector
    """ Constant acceleration in a given direction

    :type: mathutils.Vector
    """

    grease_pencil: GreasePencil
    """ Grease Pencil data-block used for annotations in the 3D view

    :type: GreasePencil
    """

    grease_pencil_settings: SceneGpencil
    """ Grease Pencil settings for the scene

    :type: SceneGpencil
    """

    hydra: SceneHydra
    """ Hydra settings for the scene

    :type: SceneHydra
    """

    is_nla_tweakmode: bool
    """ Whether there is any action referenced by NLA being edited (strictly read-only)

    :type: bool
    """

    keying_sets: KeyingSets
    """ Absolute Keying Sets for this Scene

    :type: KeyingSets
    """

    keying_sets_all: KeyingSetsAll
    """ All Keying Sets available for use (Builtins and Absolute Keying Sets for this Scene)

    :type: KeyingSetsAll
    """

    lock_frame_selection_to_range: bool
    """ Don't allow frame to be selected with mouse outside of frame range

    :type: bool
    """

    node_tree: NodeTree
    """ Compositing node tree

    :type: NodeTree
    """

    objects: SceneObjects
    """ 

    :type: SceneObjects
    """

    render: RenderSettings
    """ 

    :type: RenderSettings
    """

    rigidbody_world: RigidBodyWorld
    """ 

    :type: RigidBodyWorld
    """

    safe_areas: DisplaySafeAreas
    """ 

    :type: DisplaySafeAreas
    """

    sequence_editor: SequenceEditor
    """ 

    :type: SequenceEditor
    """

    sequencer_colorspace_settings: ColorManagedSequencerColorspaceSettings
    """ Settings of color space sequencer is working in

    :type: ColorManagedSequencerColorspaceSettings
    """

    show_keys_from_selected_only: bool
    """ Only include channels relating to selected objects and data

    :type: bool
    """

    show_subframe: bool
    """ Show current scene subframe and allow set it using interface tools

    :type: bool
    """

    simulation_frame_end: int
    """ Frame at which simulations end

    :type: int
    """

    simulation_frame_start: int
    """ Frame at which simulations start

    :type: int
    """

    sync_mode: str
    """ How to sync playback

    :type: str
    """

    timeline_markers: TimelineMarkers
    """ Markers used in all timelines for the current scene

    :type: TimelineMarkers
    """

    tool_settings: ToolSettings
    """ 

    :type: ToolSettings
    """

    transform_orientation_slots: bpy_prop_collection[TransformOrientationSlot]
    """ 

    :type: bpy_prop_collection[TransformOrientationSlot]
    """

    unit_settings: UnitSettings
    """ Unit editing settings

    :type: UnitSettings
    """

    use_audio: bool
    """ Play back of audio from Sequence Editor, otherwise mute audio

    :type: bool
    """

    use_audio_scrub: bool
    """ Play audio from Sequence Editor while scrubbing

    :type: bool
    """

    use_custom_simulation_range: bool
    """ Use a simulation range that is different from the scene range for simulation nodes that don't override the frame range themselves

    :type: bool
    """

    use_gravity: bool
    """ Use global gravity for all dynamics

    :type: bool
    """

    use_nodes: bool
    """ Enable the compositing node tree

    :type: bool
    """

    use_preview_range: bool
    """ Use an alternative start/end frame range for animation playback and view renders

    :type: bool
    """

    use_stamp_note: str
    """ User defined note for the render stamping

    :type: str
    """

    view_layers: ViewLayers
    """ 

    :type: ViewLayers
    """

    view_settings: ColorManagedViewSettings
    """ Color management settings applied on image before saving

    :type: ColorManagedViewSettings
    """

    world: World
    """ World used for rendering the scene

    :type: World
    """

    @classmethod
    def update_render_engine(cls):
        """Trigger a render engine update"""
        ...

    def statistics(self, view_layer: ViewLayer) -> str | typing.Any:
        """statistics

        :param view_layer: View Layer
        :type view_layer: ViewLayer
        :return: Statistics
        :rtype: str | typing.Any
        """
        ...

    def frame_set(self, frame: int | None, subframe: typing.Any | None = 0.0):
        """Set scene frame updating all objects immediately

        :param frame: Frame number to set
        :type frame: int | None
        :param subframe: Subframe time, between 0.0 and 1.0
        :type subframe: typing.Any | None
        """
        ...

    def uvedit_aspect(self, object: Object) -> mathutils.Vector:
        """Get uv aspect for current object

        :param object: Object
        :type object: Object
        :return: aspect
        :rtype: mathutils.Vector
        """
        ...

    def ray_cast(
        self,
        depsgraph: Depsgraph,
        origin: collections.abc.Sequence[float] | mathutils.Vector | None,
        direction: collections.abc.Sequence[float] | mathutils.Vector | None,
        distance: typing.Any | None = 1.70141e38,
    ):
        """Cast a ray onto in object space

                :param depsgraph: The current dependency graph
                :type depsgraph: Depsgraph
                :param origin:
                :type origin: collections.abc.Sequence[float] | mathutils.Vector | None
                :param direction:
                :type direction: collections.abc.Sequence[float] | mathutils.Vector | None
                :param distance: Maximum distance
                :type distance: typing.Any | None
                :return: result, boolean

        location, The hit location of this ray cast, `mathutils.Vector` of 3 items in [-inf, inf]

        normal, The face normal at the ray cast hit location, `mathutils.Vector` of 3 items in [-inf, inf]

        index, The face index, -1 when original data isn't available, int in [-inf, inf]

        object, Ray cast object, `Object`

        matrix, Matrix, `mathutils.Matrix` of 4 * 4 items in [-inf, inf]
        """
        ...

    def sequence_editor_create(self) -> SequenceEditor:
        """Ensure sequence editor is valid in this scene

        :return: New sequence editor data or nullptr
        :rtype: SequenceEditor
        """
        ...

    def sequence_editor_clear(self):
        """Clear sequence editor in this scene"""
        ...

    def alembic_export(
        self,
        filepath: str | typing.Any,
        frame_start: typing.Any | None = 1,
        frame_end: typing.Any | None = 1,
        xform_samples: typing.Any | None = 1,
        geom_samples: typing.Any | None = 1,
        shutter_open: typing.Any | None = 0.0,
        shutter_close: typing.Any | None = 1.0,
        selected_only: bool | typing.Any | None = False,
        uvs: bool | typing.Any | None = True,
        normals: bool | typing.Any | None = True,
        vcolors: bool | typing.Any | None = False,
        apply_subdiv: bool | typing.Any | None = True,
        flatten: bool | typing.Any | None = False,
        visible_objects_only: bool | typing.Any | None = False,
        face_sets: bool | typing.Any | None = False,
        subdiv_schema: bool | typing.Any | None = False,
        export_hair: bool | typing.Any | None = True,
        export_particles: bool | typing.Any | None = True,
        packuv: bool | typing.Any | None = False,
        scale: typing.Any | None = 1.0,
        triangulate: bool | typing.Any | None = False,
        quad_method: str | None = "BEAUTY",
        ngon_method: str | None = "BEAUTY",
    ):
        """Export to Alembic file (deprecated, use the Alembic export operator)

        :param filepath: File Path, File path to write Alembic file
        :type filepath: str | typing.Any
        :param frame_start: Start, Start Frame
        :type frame_start: typing.Any | None
        :param frame_end: End, End Frame
        :type frame_end: typing.Any | None
        :param xform_samples: Xform samples, Transform samples per frame
        :type xform_samples: typing.Any | None
        :param geom_samples: Geom samples, Geometry samples per frame
        :type geom_samples: typing.Any | None
        :param shutter_open: Shutter open
        :type shutter_open: typing.Any | None
        :param shutter_close: Shutter close
        :type shutter_close: typing.Any | None
        :param selected_only: Selected only, Export only selected objects
        :type selected_only: bool | typing.Any | None
        :param uvs: UVs, Export UVs
        :type uvs: bool | typing.Any | None
        :param normals: Normals, Export normals
        :type normals: bool | typing.Any | None
        :param vcolors: Color Attributes, Export color attributes
        :type vcolors: bool | typing.Any | None
        :param apply_subdiv: Subsurfs as meshes, Export subdivision surfaces as meshes
        :type apply_subdiv: bool | typing.Any | None
        :param flatten: Flatten hierarchy, Flatten hierarchy
        :type flatten: bool | typing.Any | None
        :param visible_objects_only: Visible layers only, Export only objects in visible layers
        :type visible_objects_only: bool | typing.Any | None
        :param face_sets: Facesets, Export face sets
        :type face_sets: bool | typing.Any | None
        :param subdiv_schema: Use Alembic subdivision Schema, Use Alembic subdivision Schema
        :type subdiv_schema: bool | typing.Any | None
        :param export_hair: Export Hair, Exports hair particle systems as animated curves
        :type export_hair: bool | typing.Any | None
        :param export_particles: Export Particles, Exports non-hair particle systems
        :type export_particles: bool | typing.Any | None
        :param packuv: Export with packed UV islands, Export with packed UV islands
        :type packuv: bool | typing.Any | None
        :param scale: Scale, Value by which to enlarge or shrink the objects with respect to the world's origin
        :type scale: typing.Any | None
        :param triangulate: Triangulate, Export polygons (quads and n-gons) as triangles
        :type triangulate: bool | typing.Any | None
        :param quad_method: Quad Method, Method for splitting the quads into triangles
        :type quad_method: str | None
        :param ngon_method: N-gon Method, Method for splitting the n-gons into triangles
        :type ngon_method: str | None
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

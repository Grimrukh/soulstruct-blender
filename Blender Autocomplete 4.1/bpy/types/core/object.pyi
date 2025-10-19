import typing
import collections.abc
import mathutils
from .object_display import ObjectDisplay
from .anim_viz import AnimViz
from .object_modifiers import ObjectModifiers
from .field_settings import FieldSettings
from .anim_data import AnimData
from .image_user import ImageUser
from .mesh import Mesh
from .material_slot import MaterialSlot
from .struct import Struct
from .vertex_groups import VertexGroups
from .object_constraints import ObjectConstraints
from .object_shader_fx import ObjectShaderFx
from .pose_bone import PoseBone
from .rigid_body_constraint import RigidBodyConstraint
from .scene import Scene
from .depsgraph import Depsgraph
from .pose import Pose
from .bpy_prop_collection import bpy_prop_collection
from .soft_body_settings import SoftBodySettings
from .shape_key import ShapeKey
from .material import Material
from .bpy_prop_array import bpy_prop_array
from .particle_systems import ParticleSystems
from .curve import Curve
from .rigid_body_object import RigidBodyObject
from .object_gpencil_modifiers import ObjectGpencilModifiers
from .motion_path import MotionPath
from .collection import Collection
from .bpy_struct import bpy_struct
from .collision_settings import CollisionSettings
from .object_line_art import ObjectLineArt
from .id import ID
from .object_light_linking import ObjectLightLinking
from .space_view3_d import SpaceView3D
from .view_layer import ViewLayer

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")

if typing.TYPE_CHECKING:
    from io_soulstruct import *
    from map_progress_manager import *


class Object(ID, bpy_struct):
    """Object data-block defining an object in a scene"""

    # region Soulstruct Extensions
    soulstruct_type: SoulstructType

    FLVER: FLVERProps
    FLVER_DUMMY: FLVERDummyProps

    NVM_EVENT_ENTITY: NVMEventEntityProps
    MCG: MCGProps
    MCG_NODE: MCGNodeProps
    MCG_EDGE: MCGEdgeProps

    MSB_PART: MSBPartProps
    MSB_MAP_PIECE: MSBMapPieceProps
    MSB_OBJECT: MSBObjectProps
    MSB_ASSET: MSBAssetProps
    MSB_CHARACTER: MSBCharacterProps
    MSB_PLAYER_START: MSBPlayerStartProps
    MSB_COLLISION: MSBCollisionProps
    MSB_NAVMESH: MSBNavmeshProps
    MSB_CONNECT_COLLISION: MSBConnectCollisionProps

    MSB_REGION: MSBRegionProps

    MSB_EVENT: MSBEventProps

    # Map Progress Manager
    map_progress: MapProgressProps
    # endregion

    active_material: Material | None
    """ Active material being displayed

    :type: Material | None
    """

    active_material_index: int | None
    """ Index of active material slot

    :type: int | None
    """

    active_shape_key: ShapeKey
    """ Current shape key

    :type: ShapeKey
    """

    active_shape_key_index: int | None
    """ Current shape key index

    :type: int | None
    """

    add_rest_position_attribute: bool
    """ Add a "rest_position" attribute that is a copy of the position attribute before shape keys and modifiers are evaluated

    :type: bool
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    animation_visualization: AnimViz
    """ Animation data for this data-block

    :type: AnimViz
    """

    bound_box: list[list[float]] | tuple[
        tuple[float, float, float, float, float, float, float, float],
        tuple[float, float, float, float, float, float, float, float],
        tuple[float, float, float, float, float, float, float, float],
    ]
    """ Object's bounding box in object-space coordinates, all values are -1.0 when not available

    :type: list[list[float]] | tuple[tuple[float, float, float, float, float, float, float, float], tuple[float, float, float, float, float, float, float, float], tuple[float, float, float, float, float, float, float, float]]
    """

    collision: CollisionSettings
    """ Settings for using the object as a collider in physics simulation

    :type: CollisionSettings
    """

    color: bpy_prop_array[float]
    """ Object color and alpha, used when the Object Color mode is enabled

    :type: bpy_prop_array[float]
    """

    constraints: ObjectConstraints
    """ Constraints affecting the transformation of the object

    :type: ObjectConstraints
    """

    cycles: typing.Any
    """ Cycles object settings

    :type: typing.Any
    """

    data: ID
    """ Object data

    :type: ID
    """

    delta_location: mathutils.Vector
    """ Extra translation added to the location of the object

    :type: mathutils.Vector
    """

    delta_rotation_euler: mathutils.Euler
    """ Extra rotation added to the rotation of the object (when using Euler rotations)

    :type: mathutils.Euler
    """

    delta_rotation_quaternion: mathutils.Quaternion
    """ Extra rotation added to the rotation of the object (when using Quaternion rotations)

    :type: mathutils.Quaternion
    """

    delta_scale: mathutils.Vector
    """ Extra scaling added to the scale of the object

    :type: mathutils.Vector
    """

    dimensions: mathutils.Vector
    """ Absolute bounding box dimensions of the object.
Warning: Assigning to it or its members multiple consecutive times will not work correctly, as this needs up-to-date evaluated data

    :type: mathutils.Vector
    """

    display: ObjectDisplay
    """ Object display settings for 3D viewport

    :type: ObjectDisplay
    """

    display_bounds_type: str
    """ Object boundary display type

    :type: str
    """

    display_type: str
    """ How to display object in viewport

    :type: str
    """

    empty_display_size: float
    """ Size of display for empties in the viewport

    :type: float
    """

    empty_display_type: str
    """ Viewport display style for empties

    :type: str
    """

    empty_image_depth: str
    """ Determine which other objects will occlude the image

    :type: str
    """

    empty_image_offset: bpy_prop_array[float]
    """ Origin offset distance

    :type: bpy_prop_array[float]
    """

    empty_image_side: str
    """ Show front/back side

    :type: str
    """

    field: FieldSettings
    """ Settings for using the object as a field in physics simulation

    :type: FieldSettings
    """

    grease_pencil_modifiers: ObjectGpencilModifiers
    """ Modifiers affecting the data of the grease pencil object

    :type: ObjectGpencilModifiers
    """

    hide_probe_plane: bool
    """ Globally disable in planar light probes

    :type: bool
    """

    hide_probe_sphere: bool
    """ Globally disable in spherical light probes

    :type: bool
    """

    hide_probe_volume: bool
    """ Globally disable in volume probes

    :type: bool
    """

    hide_render: bool
    """ Globally disable in renders

    :type: bool
    """

    hide_select: bool
    """ Disable selection in viewport

    :type: bool
    """

    hide_viewport: bool
    """ Globally disable in viewports

    :type: bool
    """

    image_user: ImageUser
    """ Parameters defining which layer, pass and frame of the image is displayed

    :type: ImageUser
    """

    instance_collection: Collection
    """ Instance an existing collection

    :type: Collection
    """

    instance_faces_scale: float
    """ Scale the face instance objects

    :type: float
    """

    instance_type: str
    """ If not None, object instancing method to use

    :type: str
    """

    is_from_instancer: bool
    """ Object comes from a instancer

    :type: bool
    """

    is_from_set: bool
    """ Object comes from a background set

    :type: bool
    """

    is_holdout: bool
    """ Render objects as a holdout or matte, creating a hole in the image with zero alpha, to fill out in compositing with real footage or another render

    :type: bool
    """

    is_instancer: bool
    """ 

    :type: bool
    """

    is_shadow_catcher: bool
    """ Only render shadows and reflections on this object, for compositing renders into real footage. Objects with this setting are considered to already exist in the footage, objects without it are synthetic objects being composited into it

    :type: bool
    """

    light_linking: ObjectLightLinking
    """ Light linking settings

    :type: ObjectLightLinking
    """

    lightgroup: str
    """ Lightgroup that the object belongs to

    :type: str
    """

    lineart: ObjectLineArt
    """ Line art settings for the object

    :type: ObjectLineArt
    """

    location: mathutils.Vector
    """ Location of the object

    :type: mathutils.Vector
    """

    lock_location: list[bool]
    """ Lock editing of location when transforming

    :type: list[bool]
    """

    lock_rotation: list[bool]
    """ Lock editing of rotation when transforming

    :type: list[bool]
    """

    lock_rotation_w: bool
    """ Lock editing of 'angle' component of four-component rotations when transforming

    :type: bool
    """

    lock_rotations_4d: bool
    """ Lock editing of four component rotations by components (instead of as Eulers)

    :type: bool
    """

    lock_scale: list[bool]
    """ Lock editing of scale when transforming

    :type: list[bool]
    """

    material_slots: bpy_prop_collection[MaterialSlot]
    """ Material slots in the object

    :type: bpy_prop_collection[MaterialSlot]
    """

    matrix_basis: mathutils.Matrix
    """ Matrix access to location, rotation and scale (including deltas), before constraints and parenting are applied

    :type: mathutils.Matrix
    """

    matrix_local: mathutils.Matrix
    """ Parent relative transformation matrix.
Warning: Only takes into account object parenting, so e.g. in case of bone parenting you get a matrix relative to the Armature object, not to the actual parent bone

    :type: mathutils.Matrix
    """

    matrix_parent_inverse: mathutils.Matrix
    """ Inverse of object's parent matrix at time of parenting

    :type: mathutils.Matrix
    """

    matrix_world: mathutils.Matrix
    """ Worldspace transformation matrix

    :type: mathutils.Matrix
    """

    mode: str
    """ Object interaction mode

    :type: str
    """

    modifiers: ObjectModifiers
    """ Modifiers affecting the geometric data of the object

    :type: ObjectModifiers
    """

    motion_path: MotionPath
    """ Motion Path for this element

    :type: MotionPath
    """

    parent: Object
    """ Parent object

    :type: Object
    """

    parent_bone: str
    """ Name of parent bone in case of a bone parenting relation

    :type: str
    """

    parent_type: str
    """ Type of parent relation

    :type: str
    """

    parent_vertices: bpy_prop_array[int]
    """ Indices of vertices in case of a vertex parenting relation

    :type: bpy_prop_array[int]
    """

    particle_systems: ParticleSystems
    """ Particle systems emitted from the object

    :type: ParticleSystems
    """

    pass_index: int
    """ Index number for the "Object Index" render pass

    :type: int
    """

    pose: Pose
    """ Current pose for armatures

    :type: Pose
    """

    rigid_body: RigidBodyObject
    """ Settings for rigid body simulation

    :type: RigidBodyObject
    """

    rigid_body_constraint: RigidBodyConstraint
    """ Constraint constraining rigid bodies

    :type: RigidBodyConstraint
    """

    rotation_axis_angle: bpy_prop_array[float]
    """ Angle of Rotation for Axis-Angle rotation representation

    :type: bpy_prop_array[float]
    """

    rotation_euler: mathutils.Euler
    """ Rotation in Eulers

    :type: mathutils.Euler
    """

    rotation_mode: str
    """ 

    :type: str
    """

    rotation_quaternion: mathutils.Quaternion
    """ Rotation in Quaternions

    :type: mathutils.Quaternion
    """

    scale: mathutils.Vector
    """ Scaling of the object

    :type: mathutils.Vector
    """

    shader_effects: ObjectShaderFx
    """ Effects affecting display of object

    :type: ObjectShaderFx
    """

    show_all_edges: bool
    """ Display all edges for mesh objects

    :type: bool
    """

    show_axis: bool
    """ Display the object's origin and axes

    :type: bool
    """

    show_bounds: bool
    """ Display the object's bounds

    :type: bool
    """

    show_empty_image_only_axis_aligned: bool
    """ Only display the image when it is aligned with the view axis

    :type: bool
    """

    show_empty_image_orthographic: bool
    """ Display image in orthographic mode

    :type: bool
    """

    show_empty_image_perspective: bool
    """ Display image in perspective mode

    :type: bool
    """

    show_in_front: bool
    """ Make the object display in front of others

    :type: bool
    """

    show_instancer_for_render: bool
    """ Make instancer visible when rendering

    :type: bool
    """

    show_instancer_for_viewport: bool
    """ Make instancer visible in the viewport

    :type: bool
    """

    show_name: bool
    """ Display the object's name

    :type: bool
    """

    show_only_shape_key: bool
    """ Only show the active shape key at full value

    :type: bool
    """

    show_texture_space: bool
    """ Display the object's texture space

    :type: bool
    """

    show_transparent: bool
    """ Display material transparency in the object

    :type: bool
    """

    show_wire: bool
    """ Display the object's wireframe over solid shading

    :type: bool
    """

    soft_body: SoftBodySettings
    """ Settings for soft body simulation

    :type: SoftBodySettings
    """

    track_axis: str
    """ Axis that points in the 'forward' direction (applies to Instance Vertices when Align to Vertex Normal is enabled)

    :type: str
    """

    type: str
    """ Type of object

    :type: str
    """

    up_axis: str
    """ Axis that points in the upward direction (applies to Instance Vertices when Align to Vertex Normal is enabled)

    :type: str
    """

    use_camera_lock_parent: bool
    """ View Lock 3D viewport camera transformation affects the object's parent instead

    :type: bool
    """

    use_dynamic_topology_sculpting: bool
    """ 

    :type: bool
    """

    use_empty_image_alpha: bool
    """ Use alpha blending instead of alpha test (can produce sorting artifacts)

    :type: bool
    """

    use_grease_pencil_lights: bool
    """ Lights affect grease pencil object

    :type: bool
    """

    use_instance_faces_scale: bool
    """ Scale instance based on face size

    :type: bool
    """

    use_instance_vertices_rotation: bool
    """ Rotate instance according to vertex normal

    :type: bool
    """

    use_mesh_mirror_x: bool
    """ Enable mesh symmetry in the X axis

    :type: bool
    """

    use_mesh_mirror_y: bool
    """ Enable mesh symmetry in the Y axis

    :type: bool
    """

    use_mesh_mirror_z: bool
    """ Enable mesh symmetry in the Z axis

    :type: bool
    """

    use_shape_key_edit_mode: bool
    """ Display shape keys in edit mode (for meshes only)

    :type: bool
    """

    use_simulation_cache: bool
    """ Cache frames during simulation nodes playback

    :type: bool
    """

    vertex_groups: VertexGroups
    """ Vertex groups of the object

    :type: VertexGroups
    """

    visible_camera: bool
    """ Object visibility to camera rays

    :type: bool
    """

    visible_diffuse: bool
    """ Object visibility to diffuse rays

    :type: bool
    """

    visible_glossy: bool
    """ Object visibility to glossy rays

    :type: bool
    """

    visible_shadow: bool
    """ Object visibility to shadow rays

    :type: bool
    """

    visible_transmission: bool
    """ Object visibility to transmission rays

    :type: bool
    """

    visible_volume_scatter: bool
    """ Object visibility to volume scattering rays

    :type: bool
    """

    children: tuple[Object, ...]
    """ All the children of this object.(readonly)

    :type: tuple[Object, ...]
    """

    children_recursive: tuple[Object, ...]
    """ A list of all children from this object.(readonly)

    :type: tuple[Object, ...]
    """

    users_collection: tuple[Collection, ...]
    """ The collections this object is in.(readonly)

    :type: tuple[Collection, ...]
    """

    users_scene: tuple[Scene, ...]
    """ The scenes this object is in.(readonly)

    :type: tuple[Scene, ...]
    """

    def select_get(self, view_layer: ViewLayer | None = None) -> bool:
        """Test if the object is selected. The selection state is per view layer

        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        :return: Object selected
        :rtype: bool
        """
        ...

    def select_set(self, state: bool | None, view_layer: ViewLayer | None = None):
        """Select or deselect the object. The selection state is per view layer

        :param state: Selection state to define
        :type state: bool | None
        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        """
        ...

    def hide_get(self, view_layer: ViewLayer | None = None) -> bool:
        """Test if the object is hidden for viewport editing. This hiding state is per view layer

        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        :return: Object hidden
        :rtype: bool
        """
        ...

    def hide_set(self, state: bool | None, view_layer: ViewLayer | None = None):
        """Hide the object for viewport editing. This hiding state is per view layer

        :param state: Hide state to define
        :type state: bool | None
        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        """
        ...

    def visible_get(
        self, view_layer: ViewLayer | None = None, viewport: SpaceView3D | None = None
    ) -> bool:
        """Test if the object is visible in the 3D viewport, taking into account all visibility settings

        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        :param viewport: Use this instead of the active 3D viewport
        :type viewport: SpaceView3D | None
        :return: Object visible
        :rtype: bool
        """
        ...

    def holdout_get(self, view_layer: ViewLayer | None = None) -> bool:
        """Test if object is masked in the view layer

        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        :return: Object holdout
        :rtype: bool
        """
        ...

    def indirect_only_get(self, view_layer: ViewLayer | None = None) -> bool:
        """Test if object is set to contribute only indirectly (through shadows and reflections) in the view layer

        :param view_layer: Use this instead of the active view layer
        :type view_layer: ViewLayer | None
        :return: Object indirect only
        :rtype: bool
        """
        ...

    def local_view_get(self, viewport: SpaceView3D | None) -> bool:
        """Get the local view state for this object

        :param viewport: Viewport in local view
        :type viewport: SpaceView3D | None
        :return: Object local view state
        :rtype: bool
        """
        ...

    def local_view_set(self, viewport: SpaceView3D | None, state: bool | None):
        """Set the local view state for this object

        :param viewport: Viewport in local view
        :type viewport: SpaceView3D | None
        :param state: Local view state to define
        :type state: bool | None
        """
        ...

    def visible_in_viewport_get(self, viewport: SpaceView3D | None) -> bool:
        """Check for local view and local collections for this viewport and object

        :param viewport: Viewport in local collections
        :type viewport: SpaceView3D | None
        :return: Object viewport visibility
        :rtype: bool
        """
        ...

    def convert_space(
        self,
        pose_bone: PoseBone | None = None,
        matrix: typing.Any | None = (
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
        ),
        from_space: str | None = "WORLD",
        to_space: str | None = "WORLD",
    ) -> mathutils.Matrix:
        """Convert (transform) the given matrix from one space to another

                :param pose_bone: Bone to use to define spaces (may be None, in which case only the two 'WORLD' and 'LOCAL' spaces are usable)
                :type pose_bone: PoseBone | None
                :param matrix: The matrix to transform
                :type matrix: typing.Any | None
                :param from_space: The space in which 'matrix' is currently

        WORLD
        World Space -- The most global space in Blender.

        POSE
        Pose Space -- The pose space of a bone (its armature's object space).

        LOCAL_WITH_PARENT
        Local With Parent -- The rest pose local space of a bone (this matrix includes parent transforms).

        LOCAL
        Local Space -- The local space of an object/bone.
                :type from_space: str | None
                :param to_space: The space to which you want to transform 'matrix'

        WORLD
        World Space -- The most global space in Blender.

        POSE
        Pose Space -- The pose space of a bone (its armature's object space).

        LOCAL_WITH_PARENT
        Local With Parent -- The rest pose local space of a bone (this matrix includes parent transforms).

        LOCAL
        Local Space -- The local space of an object/bone.
                :type to_space: str | None
                :return: The transformed matrix
                :rtype: mathutils.Matrix
        """
        ...

    def calc_matrix_camera(
        self,
        depsgraph: Depsgraph | None,
        x: typing.Any | None = 1,
        y: typing.Any | None = 1,
        scale_x: typing.Any | None = 1.0,
        scale_y: typing.Any | None = 1.0,
    ) -> mathutils.Matrix:
        """Generate the camera projection matrix of this object (mostly useful for Camera and Light types)

        :param depsgraph: Depsgraph to get evaluated data from
        :type depsgraph: Depsgraph | None
        :param x: Width of the render area
        :type x: typing.Any | None
        :param y: Height of the render area
        :type y: typing.Any | None
        :param scale_x: Width scaling factor
        :type scale_x: typing.Any | None
        :param scale_y: Height scaling factor
        :type scale_y: typing.Any | None
        :return: The camera projection matrix
        :rtype: mathutils.Matrix
        """
        ...

    def camera_fit_coords(self, depsgraph: Depsgraph | None, coordinates: typing.Any):
        """Compute the coordinate (and scale for ortho cameras) given object should be to 'see' all given coordinates

                :param depsgraph: Depsgraph to get evaluated data from
                :type depsgraph: Depsgraph | None
                :param coordinates: Coordinates to fit in
                :type coordinates: typing.Any
                :return: co_return, The location to aim to be able to see all given points, `mathutils.Vector` of 3 items in [-inf, inf]

        scale_return, The ortho scale to aim to be able to see all given points (if relevant), float in [-inf, inf]
        """
        ...

    def crazyspace_eval(self, depsgraph: Depsgraph | None, scene: Scene | None):
        """Compute orientation mapping between vertices of an original object and object with shape keys and deforming modifiers applied.The evaluation is to be freed with the crazyspace_eval_free function

        :param depsgraph: Dependency Graph, Evaluated dependency graph
        :type depsgraph: Depsgraph | None
        :param scene: Scene, Scene of the object
        :type scene: Scene | None
        """
        ...

    def crazyspace_displacement_to_deformed(
        self,
        vertex_index: typing.Any | None = 0,
        displacement: typing.Any | None = (0.0, 0.0, 0.0),
    ) -> mathutils.Vector:
        """Convert displacement vector from non-deformed object space to deformed object space

        :param vertex_index: vertex_index
        :type vertex_index: typing.Any | None
        :param displacement: displacement
        :type displacement: typing.Any | None
        :return: displacement_deformed
        :rtype: mathutils.Vector
        """
        ...

    def crazyspace_displacement_to_original(
        self,
        vertex_index: typing.Any | None = 0,
        displacement: typing.Any | None = (0.0, 0.0, 0.0),
    ) -> mathutils.Vector:
        """Free evaluated state of crazyspace

        :param vertex_index: vertex_index
        :type vertex_index: typing.Any | None
        :param displacement: displacement
        :type displacement: typing.Any | None
        :return: displacement_original
        :rtype: mathutils.Vector
        """
        ...

    def crazyspace_eval_clear(self):
        """crazyspace_eval_clear"""
        ...

    def to_mesh(
        self,
        preserve_all_data_layers: bool | typing.Any | None = False,
        depsgraph: Depsgraph | None = None,
    ) -> Mesh:
        """Create a Mesh data-block from the current state of the object. The object owns the data-block. To force free it use to_mesh_clear(). The result is temporary and cannot be used by objects from the main database

        :param preserve_all_data_layers: Preserve all data layers in the mesh, like UV maps and vertex groups. By default Blender only computes the subset of data layers needed for viewport display and rendering, for better performance
        :type preserve_all_data_layers: bool | typing.Any | None
        :param depsgraph: Dependency Graph, Evaluated dependency graph which is required when preserve_all_data_layers is true
        :type depsgraph: Depsgraph | None
        :return: Mesh created from object
        :rtype: Mesh
        """
        ...

    def to_mesh_clear(self):
        """Clears mesh data-block created by to_mesh()"""
        ...

    def to_curve(
        self,
        depsgraph: Depsgraph | None,
        apply_modifiers: bool | typing.Any | None = False,
    ) -> Curve:
        """Create a Curve data-block from the current state of the object. This only works for curve and text objects. The object owns the data-block. To force free it, use to_curve_clear(). The result is temporary and cannot be used by objects from the main database

        :param depsgraph: Dependency Graph, Evaluated dependency graph
        :type depsgraph: Depsgraph | None
        :param apply_modifiers: Apply the deform modifiers on the control points of the curve. This is only supported for curve objects
        :type apply_modifiers: bool | typing.Any | None
        :return: Curve created from object
        :rtype: Curve
        """
        ...

    def to_curve_clear(self):
        """Clears curve data-block created by to_curve()"""
        ...

    def find_armature(self) -> Object:
        """Find armature influencing this object as a parent or via a modifier

        :return: Armature object influencing this object or nullptr
        :rtype: Object
        """
        ...

    def shape_key_add(
        self, name: str | typing.Any = "Key", from_mix: bool | typing.Any | None = True
    ) -> ShapeKey:
        """Add shape key to this object

        :param name: Unique name for the new keyblock
        :type name: str | typing.Any
        :param from_mix: Create new shape from existing mix of shapes
        :type from_mix: bool | typing.Any | None
        :return: New shape keyblock
        :rtype: ShapeKey
        """
        ...

    def shape_key_remove(self, key: ShapeKey):
        """Remove a Shape Key from this object

        :param key: Keyblock to be removed
        :type key: ShapeKey
        """
        ...

    def shape_key_clear(self):
        """Remove all Shape Keys from this object"""
        ...

    def ray_cast(
        self,
        origin: collections.abc.Sequence[float] | mathutils.Vector | None,
        direction: collections.abc.Sequence[float] | mathutils.Vector | None,
        distance: typing.Any | None = 1.70141e38,
        depsgraph: Depsgraph | None = None,
    ):
        """Cast a ray onto evaluated geometry, in object space (using context's or provided depsgraph to get evaluated mesh if needed)

                :param origin: Origin of the ray, in object space
                :type origin: collections.abc.Sequence[float] | mathutils.Vector | None
                :param direction: Direction of the ray, in object space
                :type direction: collections.abc.Sequence[float] | mathutils.Vector | None
                :param distance: Maximum distance
                :type distance: typing.Any | None
                :param depsgraph: Depsgraph to use to get evaluated data, when called from original object (only needed if current Context's depsgraph is not suitable)
                :type depsgraph: Depsgraph | None
                :return: result, Whether the ray successfully hit the geometry, boolean

        location, The hit location of this ray cast, `mathutils.Vector` of 3 items in [-inf, inf]

        normal, The face normal at the ray cast hit location, `mathutils.Vector` of 3 items in [-inf, inf]

        index, The face index, -1 when original data isn't available, int in [-inf, inf]
        """
        ...

    def closest_point_on_mesh(
        self,
        origin: collections.abc.Sequence[float] | mathutils.Vector | None,
        distance: typing.Any | None = 1.84467e19,
        depsgraph: Depsgraph | None = None,
    ):
        """Find the nearest point on evaluated geometry, in object space (using context's or provided depsgraph to get evaluated mesh if needed)

                :param origin: Point to find closest geometry from (in object space)
                :type origin: collections.abc.Sequence[float] | mathutils.Vector | None
                :param distance: Maximum distance
                :type distance: typing.Any | None
                :param depsgraph: Depsgraph to use to get evaluated data, when called from original object (only needed if current Context's depsgraph is not suitable)
                :type depsgraph: Depsgraph | None
                :return: result, Whether closest point on geometry was found, boolean

        location, The location on the object closest to the point, `mathutils.Vector` of 3 items in [-inf, inf]

        normal, The face normal at the closest point, `mathutils.Vector` of 3 items in [-inf, inf]

        index, The face index, -1 when original data isn't available, int in [-inf, inf]
        """
        ...

    def is_modified(self, scene: Scene, settings: str | None) -> bool:
        """Determine if this object is modified from the base mesh data

                :param scene: Scene in which to check the object
                :type scene: Scene
                :param settings: Modifier settings to apply

        PREVIEW
        Preview -- Apply modifier preview settings.

        RENDER
        Render -- Apply modifier render settings.
                :type settings: str | None
                :return: Whether the object is modified
                :rtype: bool
        """
        ...

    def is_deform_modified(self, scene: Scene, settings: str | None) -> bool:
        """Determine if this object is modified by a deformation from the base mesh data

                :param scene: Scene in which to check the object
                :type scene: Scene
                :param settings: Modifier settings to apply

        PREVIEW
        Preview -- Apply modifier preview settings.

        RENDER
        Render -- Apply modifier render settings.
                :type settings: str | None
                :return: Whether the object is deform-modified
                :rtype: bool
        """
        ...

    def update_from_editmode(self) -> bool:
        """Load the objects edit-mode data into the object data

        :return: Success
        :rtype: bool
        """
        ...

    def cache_release(self):
        """Release memory used by caches associated with this object. Intended to be used by render engines only"""
        ...

    def generate_gpencil_strokes(
        self,
        grease_pencil_object: Object,
        use_collections: bool | typing.Any | None = True,
        scale_thickness: typing.Any | None = 1.0,
        sample: typing.Any | None = 0.0,
    ) -> bool:
        """Convert a curve object to grease pencil strokes.

        :param grease_pencil_object: Grease Pencil object used to create new strokes
        :type grease_pencil_object: Object
        :param use_collections: Use Collections
        :type use_collections: bool | typing.Any | None
        :param scale_thickness: Thickness scaling factor
        :type scale_thickness: typing.Any | None
        :param sample: Sample distance, zero to disable
        :type sample: typing.Any | None
        :return: Result
        :rtype: bool
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

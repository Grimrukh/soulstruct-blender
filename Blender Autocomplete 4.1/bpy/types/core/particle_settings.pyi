import typing
import collections.abc
import mathutils
from .field_settings import FieldSettings
from .anim_data import AnimData
from .curve_mapping import CurveMapping
from .struct import Struct
from .texture import Texture
from .boid_settings import BoidSettings
from .bpy_prop_collection import bpy_prop_collection
from .sph_fluid_settings import SPHFluidSettings
from .effector_weights import EffectorWeights
from .particle_dupli_weight import ParticleDupliWeight
from .object import Object
from .particle_settings_texture_slots import ParticleSettingsTextureSlots
from .collection import Collection
from .bpy_struct import bpy_struct
from .id import ID

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ParticleSettings(ID, bpy_struct):
    """Particle settings, reusable by multiple particle systems"""

    active_instanceweight: ParticleDupliWeight
    """ 

    :type: ParticleDupliWeight
    """

    active_instanceweight_index: int | None
    """ 

    :type: int | None
    """

    active_texture: Texture | None
    """ Active texture slot being displayed

    :type: Texture | None
    """

    active_texture_index: int | None
    """ Index of active texture slot

    :type: int | None
    """

    adaptive_angle: int
    """ How many degrees path has to curve to make another render segment

    :type: int
    """

    adaptive_pixel: int
    """ How many pixels path has to cover to make another render segment

    :type: int
    """

    angular_velocity_factor: float
    """ Angular velocity amount (in radians per second)

    :type: float
    """

    angular_velocity_mode: str
    """ What axis is used to change particle rotation with time

    :type: str
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    apply_effector_to_children: bool
    """ Apply effectors to children

    :type: bool
    """

    apply_guide_to_children: bool
    """ 

    :type: bool
    """

    bending_random: float
    """ Random stiffness of hairs

    :type: float
    """

    boids: BoidSettings
    """ 

    :type: BoidSettings
    """

    branch_threshold: float
    """ Threshold of branching

    :type: float
    """

    brownian_factor: float
    """ Amount of random, erratic particle movement

    :type: float
    """

    child_length: float
    """ Length of child paths

    :type: float
    """

    child_length_threshold: float
    """ Amount of particles left untouched by child path length

    :type: float
    """

    child_parting_factor: float
    """ Create parting in the children based on parent strands

    :type: float
    """

    child_parting_max: float
    """ Maximum root to tip angle (tip distance/root distance for long hair)

    :type: float
    """

    child_parting_min: float
    """ Minimum root to tip angle (tip distance/root distance for long hair)

    :type: float
    """

    child_percent: int
    """ Number of children per parent

    :type: int
    """

    child_radius: float
    """ Radius of children around parent

    :type: float
    """

    child_roundness: float
    """ Roundness of children around parent

    :type: float
    """

    child_size: float
    """ A multiplier for the child particle size

    :type: float
    """

    child_size_random: float
    """ Random variation to the size of the child particles

    :type: float
    """

    child_type: str
    """ Create child particles

    :type: str
    """

    clump_curve: CurveMapping
    """ Curve defining clump tapering

    :type: CurveMapping
    """

    clump_factor: float
    """ Amount of clumping

    :type: float
    """

    clump_noise_size: float
    """ Size of clump noise

    :type: float
    """

    clump_shape: float
    """ Shape of clumping

    :type: float
    """

    collision_collection: Collection
    """ Limit colliders to this collection

    :type: Collection
    """

    color_maximum: float
    """ Maximum length of the particle color vector

    :type: float
    """

    count: int
    """ Total number of particles

    :type: int
    """

    courant_target: float
    """ The relative distance a particle can move before requiring more subframes (target Courant number); 0.01 to 0.3 is the recommended range

    :type: float
    """

    create_long_hair_children: bool
    """ Calculate children that suit long hair well

    :type: bool
    """

    damping: float
    """ Amount of damping

    :type: float
    """

    display_color: str
    """ Display additional particle data as a color

    :type: str
    """

    display_method: str
    """ How particles are displayed in viewport

    :type: str
    """

    display_percentage: int
    """ Percentage of particles to display in 3D view

    :type: int
    """

    display_size: float
    """ Size of particles on viewport

    :type: float
    """

    display_step: int
    """ How many steps paths are displayed with (power of 2)

    :type: int
    """

    distribution: str
    """ How to distribute particles on selected element

    :type: str
    """

    drag_factor: float
    """ Amount of air drag

    :type: float
    """

    effect_hair: float
    """ Hair stiffness for effectors

    :type: float
    """

    effector_amount: int
    """ How many particles are effectors (0 is all particles)

    :type: int
    """

    effector_weights: EffectorWeights
    """ 

    :type: EffectorWeights
    """

    emit_from: str
    """ Where to emit particles from

    :type: str
    """

    factor_random: float
    """ Give the starting velocity a random variation

    :type: float
    """

    fluid: SPHFluidSettings
    """ 

    :type: SPHFluidSettings
    """

    force_field_1: FieldSettings
    """ 

    :type: FieldSettings
    """

    force_field_2: FieldSettings
    """ 

    :type: FieldSettings
    """

    frame_end: float
    """ Frame number to stop emitting particles

    :type: float
    """

    frame_start: float
    """ Frame number to start emitting particles

    :type: float
    """

    grid_random: float
    """ Add random offset to the grid locations

    :type: float
    """

    grid_resolution: int
    """ The resolution of the particle grid

    :type: int
    """

    hair_length: float
    """ Length of the hair

    :type: float
    """

    hair_step: int
    """ Number of hair segments

    :type: int
    """

    hexagonal_grid: bool
    """ Create the grid in a hexagonal pattern

    :type: bool
    """

    instance_collection: Collection
    """ Show objects in this collection in place of particles

    :type: Collection
    """

    instance_object: Object
    """ Show this object in place of particles

    :type: Object
    """

    instance_weights: bpy_prop_collection[ParticleDupliWeight]
    """ Weights for all of the objects in the instance collection

    :type: bpy_prop_collection[ParticleDupliWeight]
    """

    integrator: str
    """ Algorithm used to calculate physics, from the fastest to the most stable and accurate: Midpoint, Euler, Verlet, RK4

    :type: str
    """

    invert_grid: bool
    """ Invert what is considered object and what is not

    :type: bool
    """

    is_fluid: bool
    """ Particles were created by a fluid simulation

    :type: bool
    """

    jitter_factor: float
    """ Amount of jitter applied to the sampling

    :type: float
    """

    keyed_loops: int
    """ Number of times the keys are looped

    :type: int
    """

    keys_step: int
    """ 

    :type: int
    """

    kink: str
    """ Type of periodic offset on the path

    :type: str
    """

    kink_amplitude: float
    """ The amplitude of the offset

    :type: float
    """

    kink_amplitude_clump: float
    """ How much clump affects kink amplitude

    :type: float
    """

    kink_amplitude_random: float
    """ Random variation of the amplitude

    :type: float
    """

    kink_axis: str
    """ Which axis to use for offset

    :type: str
    """

    kink_axis_random: float
    """ Random variation of the orientation

    :type: float
    """

    kink_extra_steps: int
    """ Extra steps for resolution of special kink features

    :type: int
    """

    kink_flat: float
    """ How flat the hairs are

    :type: float
    """

    kink_frequency: float
    """ The frequency of the offset (1/total length)

    :type: float
    """

    kink_shape: float
    """ Adjust the offset to the beginning/end

    :type: float
    """

    length_random: float
    """ Give path length a random variation

    :type: float
    """

    lifetime: float
    """ Life span of the particles

    :type: float
    """

    lifetime_random: float
    """ Give the particle life a random variation

    :type: float
    """

    line_length_head: float
    """ Length of the line's head

    :type: float
    """

    line_length_tail: float
    """ Length of the line's tail

    :type: float
    """

    lock_boids_to_surface: bool
    """ Constrain boids to a surface

    :type: bool
    """

    mass: float
    """ Mass of the particles

    :type: float
    """

    material: int
    """ Index of material slot used for rendering particles

    :type: int
    """

    material_slot: str
    """ Material slot used for rendering particles

    :type: str
    """

    normal_factor: float
    """ Let the surface normal give the particle a starting velocity

    :type: float
    """

    object_align_factor: mathutils.Vector
    """ Let the emitter object orientation give the particle a starting velocity

    :type: mathutils.Vector
    """

    object_factor: float
    """ Let the object give the particle a starting velocity

    :type: float
    """

    particle_factor: float
    """ Let the target particle give the particle a starting velocity

    :type: float
    """

    particle_size: float
    """ The size of the particles

    :type: float
    """

    path_end: float
    """ End time of path

    :type: float
    """

    path_start: float
    """ Starting time of path

    :type: float
    """

    phase_factor: float
    """ Rotation around the chosen orientation axis

    :type: float
    """

    phase_factor_random: float
    """ Randomize rotation around the chosen orientation axis

    :type: float
    """

    physics_type: str
    """ Particle physics type

    :type: str
    """

    radius_scale: float
    """ Multiplier of diameter properties

    :type: float
    """

    react_event: str
    """ The event of target particles to react on

    :type: str
    """

    reactor_factor: float
    """ Let the vector away from the target particle's location give the particle a starting velocity

    :type: float
    """

    render_step: int
    """ How many steps paths are rendered with (power of 2)

    :type: int
    """

    render_type: str
    """ How particles are rendered

    :type: str
    """

    rendered_child_count: int
    """ Number of children per parent for rendering

    :type: int
    """

    root_radius: float
    """ Strand diameter width at the root

    :type: float
    """

    rotation_factor_random: float
    """ Randomize particle orientation

    :type: float
    """

    rotation_mode: str
    """ Particle orientation axis (does not affect Explode modifier's results)

    :type: str
    """

    roughness_1: float
    """ Amount of location dependent roughness

    :type: float
    """

    roughness_1_size: float
    """ Size of location dependent roughness

    :type: float
    """

    roughness_2: float
    """ Amount of random roughness

    :type: float
    """

    roughness_2_size: float
    """ Size of random roughness

    :type: float
    """

    roughness_2_threshold: float
    """ Amount of particles left untouched by random roughness

    :type: float
    """

    roughness_curve: CurveMapping
    """ Curve defining roughness

    :type: CurveMapping
    """

    roughness_end_shape: float
    """ Shape of endpoint roughness

    :type: float
    """

    roughness_endpoint: float
    """ Amount of endpoint roughness

    :type: float
    """

    shape: float
    """ Strand shape parameter

    :type: float
    """

    show_guide_hairs: bool
    """ Show guide hairs

    :type: bool
    """

    show_hair_grid: bool
    """ Show hair simulation grid

    :type: bool
    """

    show_health: bool
    """ Display boid health

    :type: bool
    """

    show_number: bool
    """ Show particle number

    :type: bool
    """

    show_size: bool
    """ Show particle size

    :type: bool
    """

    show_unborn: bool
    """ Show particles before they are emitted

    :type: bool
    """

    show_velocity: bool
    """ Show particle velocity

    :type: bool
    """

    size_random: float
    """ Give the particle size a random variation

    :type: float
    """

    subframes: int
    """ Subframes to simulate for improved stability and finer granularity simulations (dt = timestep / (subframes + 1))

    :type: int
    """

    tangent_factor: float
    """ Let the surface tangent give the particle a starting velocity

    :type: float
    """

    tangent_phase: float
    """ Rotate the surface tangent

    :type: float
    """

    texture_slots: ParticleSettingsTextureSlots
    """ Texture slots defining the mapping and influence of textures

    :type: ParticleSettingsTextureSlots
    """

    time_tweak: float
    """ A multiplier for physics timestep (1.0 means one frame = 1/25 seconds)

    :type: float
    """

    timestep: float
    """ The simulation timestep per frame (seconds per frame)

    :type: float
    """

    tip_radius: float
    """ Strand diameter width at the tip

    :type: float
    """

    trail_count: int
    """ Number of trail particles

    :type: int
    """

    twist: float
    """ Number of turns around parent along the strand

    :type: float
    """

    twist_curve: CurveMapping
    """ Curve defining twist

    :type: CurveMapping
    """

    type: str
    """ Particle type

    :type: str
    """

    use_absolute_path_time: bool
    """ Path timing is in absolute frames

    :type: bool
    """

    use_adaptive_subframes: bool
    """ Automatically set the number of subframes

    :type: bool
    """

    use_advanced_hair: bool
    """ Use full physics calculations for growing hair

    :type: bool
    """

    use_close_tip: bool
    """ Set tip radius to zero

    :type: bool
    """

    use_clump_curve: bool
    """ Use a curve to define clump tapering

    :type: bool
    """

    use_clump_noise: bool
    """ Create random clumps around the parent

    :type: bool
    """

    use_collection_count: bool
    """ Use object multiple times in the same collection

    :type: bool
    """

    use_collection_pick_random: bool
    """ Pick objects from collection randomly

    :type: bool
    """

    use_dead: bool
    """ Show particles after they have died

    :type: bool
    """

    use_die_on_collision: bool
    """ Particles die when they collide with a deflector object

    :type: bool
    """

    use_dynamic_rotation: bool
    """ Particle rotations are affected by collisions and effectors

    :type: bool
    """

    use_emit_random: bool
    """ Emit in random order of elements

    :type: bool
    """

    use_even_distribution: bool
    """ Use even distribution from faces based on face areas or edge lengths

    :type: bool
    """

    use_global_instance: bool
    """ Use object's global coordinates for duplication

    :type: bool
    """

    use_hair_bspline: bool
    """ Interpolate hair using B-Splines

    :type: bool
    """

    use_modifier_stack: bool
    """ Emit particles from mesh with modifiers applied (must use same subdivision surface level for viewport and render for correct results)

    :type: bool
    """

    use_multiply_size_mass: bool
    """ Multiply mass by particle size

    :type: bool
    """

    use_parent_particles: bool
    """ Render parent particles

    :type: bool
    """

    use_react_multiple: bool
    """ React multiple times

    :type: bool
    """

    use_react_start_end: bool
    """ Give birth to unreacted particles eventually

    :type: bool
    """

    use_regrow_hair: bool
    """ Regrow hair for each frame

    :type: bool
    """

    use_render_adaptive: bool
    """ Display steps of the particle path

    :type: bool
    """

    use_rotation_instance: bool
    """ Use object's rotation for duplication (global x-axis is aligned particle rotation axis)

    :type: bool
    """

    use_rotations: bool
    """ Calculate particle rotations

    :type: bool
    """

    use_roughness_curve: bool
    """ Use a curve to define roughness

    :type: bool
    """

    use_scale_instance: bool
    """ Use object's scale for duplication

    :type: bool
    """

    use_self_effect: bool
    """ Particle effectors affect themselves

    :type: bool
    """

    use_size_deflect: bool
    """ Use particle's size in deflection

    :type: bool
    """

    use_strand_primitive: bool
    """ Use the strand primitive for rendering

    :type: bool
    """

    use_twist_curve: bool
    """ Use a curve to define twist

    :type: bool
    """

    use_velocity_length: bool
    """ Multiply line length by particle speed

    :type: bool
    """

    use_whole_collection: bool
    """ Use whole collection at once

    :type: bool
    """

    userjit: int
    """ Emission locations per face (0 = automatic)

    :type: int
    """

    virtual_parents: float
    """ Relative amount of virtual parents

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

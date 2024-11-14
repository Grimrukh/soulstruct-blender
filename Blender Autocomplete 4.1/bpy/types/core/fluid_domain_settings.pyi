import typing
import collections.abc
import mathutils
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct
from .bpy_prop_array import bpy_prop_array
from .effector_weights import EffectorWeights
from .object import Object
from .color_ramp import ColorRamp

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FluidDomainSettings(bpy_struct):
    """Fluid domain settings"""

    adapt_margin: int
    """ Margin added around fluid to minimize boundary interference

    :type: int
    """

    adapt_threshold: float
    """ Minimum amount of fluid a cell can contain before it is considered empty

    :type: float
    """

    additional_res: int
    """ Maximum number of additional cells

    :type: int
    """

    alpha: float
    """ Buoyant force based on smoke density (higher value results in faster rising smoke)

    :type: float
    """

    beta: float
    """ Buoyant force based on smoke heat (higher value results in faster rising smoke)

    :type: float
    """

    burning_rate: float
    """ Speed of the burning reaction (higher value results in smaller flames)

    :type: float
    """

    cache_data_format: str
    """ Select the file format to be used for caching volumetric data

    :type: str
    """

    cache_directory: str
    """ Directory that contains fluid cache files

    :type: str
    """

    cache_frame_end: int
    """ Frame on which the simulation stops. This is the last frame that will be baked

    :type: int
    """

    cache_frame_offset: int
    """ Frame offset that is used when loading the simulation from the cache. It is not considered when baking the simulation, only when loading it

    :type: int
    """

    cache_frame_pause_data: int
    """ 

    :type: int
    """

    cache_frame_pause_guide: int
    """ 

    :type: int
    """

    cache_frame_pause_mesh: int
    """ 

    :type: int
    """

    cache_frame_pause_noise: int
    """ 

    :type: int
    """

    cache_frame_pause_particles: int
    """ 

    :type: int
    """

    cache_frame_start: int
    """ Frame on which the simulation starts. This is the first frame that will be baked

    :type: int
    """

    cache_mesh_format: str
    """ Select the file format to be used for caching surface data

    :type: str
    """

    cache_noise_format: str
    """ Select the file format to be used for caching noise data

    :type: str
    """

    cache_particle_format: str
    """ Select the file format to be used for caching particle data

    :type: str
    """

    cache_resumable: bool
    """ Additional data will be saved so that the bake jobs can be resumed after pausing. Because more data will be written to disk it is recommended to avoid enabling this option when baking at high resolutions

    :type: bool
    """

    cache_type: str
    """ Change the cache type of the simulation

    :type: str
    """

    cell_size: mathutils.Vector
    """ Cell Size

    :type: mathutils.Vector
    """

    cfl_condition: float
    """ Maximal velocity per cell (greater CFL numbers will minimize the number of simulation steps and the computation time.)

    :type: float
    """

    clipping: float
    """ Value under which voxels are considered empty space to optimize rendering

    :type: float
    """

    color_grid: bpy_prop_array[float]
    """ Smoke color grid

    :type: bpy_prop_array[float]
    """

    color_ramp: ColorRamp
    """ 

    :type: ColorRamp
    """

    color_ramp_field: str
    """ Simulation field to color map

    :type: str
    """

    color_ramp_field_scale: float
    """ Multiplier for scaling the selected field to color map

    :type: float
    """

    delete_in_obstacle: bool
    """ Delete fluid inside obstacles

    :type: bool
    """

    density_grid: bpy_prop_array[float]
    """ Smoke density grid

    :type: bpy_prop_array[float]
    """

    display_interpolation: str
    """ Interpolation method to use for smoke/fire volumes in solid mode

    :type: str
    """

    display_thickness: float
    """ Thickness of smoke display in the viewport

    :type: float
    """

    dissolve_speed: int
    """ Determine how quickly the smoke dissolves (lower value makes smoke disappear faster)

    :type: int
    """

    domain_resolution: bpy_prop_array[int]
    """ Smoke Grid Resolution

    :type: bpy_prop_array[int]
    """

    domain_type: str
    """ Change domain type of the simulation

    :type: str
    """

    effector_group: Collection
    """ Limit effectors to this collection

    :type: Collection
    """

    effector_weights: EffectorWeights
    """ 

    :type: EffectorWeights
    """

    export_manta_script: bool
    """ Generate and export Mantaflow script from current domain settings during bake. This is only needed if you plan to analyze the cache (e.g. view grids, velocity vectors, particles) in Mantaflow directly (outside of Blender) after baking the simulation

    :type: bool
    """

    flame_grid: bpy_prop_array[float]
    """ Smoke flame grid

    :type: bpy_prop_array[float]
    """

    flame_ignition: float
    """ Minimum temperature of the flames (higher value results in faster rising flames)

    :type: float
    """

    flame_max_temp: float
    """ Maximum temperature of the flames (higher value results in faster rising flames)

    :type: float
    """

    flame_smoke: float
    """ Amount of smoke created by burning fuel

    :type: float
    """

    flame_smoke_color: mathutils.Color
    """ Color of smoke emitted from burning fuel

    :type: mathutils.Color
    """

    flame_vorticity: float
    """ Additional vorticity for the flames

    :type: float
    """

    flip_ratio: float
    """ PIC/FLIP Ratio. A value of 1.0 will result in a completely FLIP based simulation. Use a lower value for simulations which should produce smaller splashes

    :type: float
    """

    fluid_group: Collection
    """ Limit fluid objects to this collection

    :type: Collection
    """

    force_collection: Collection
    """ Limit forces to this collection

    :type: Collection
    """

    fractions_distance: float
    """ Determines how far apart fluid and obstacle are (higher values will result in fluid being further away from obstacles, smaller values will let fluid move towards the inside of obstacles)

    :type: float
    """

    fractions_threshold: float
    """ Determines how much fluid is allowed in an obstacle cell (higher values will tag a boundary cell as an obstacle easier and reduce the boundary smoothening effect)

    :type: float
    """

    gravity: mathutils.Vector
    """ Gravity in X, Y and Z direction

    :type: mathutils.Vector
    """

    gridlines_cell_filter: str
    """ Cell type to be highlighted

    :type: str
    """

    gridlines_color_field: str
    """ Simulation field to color map onto gridlines

    :type: str
    """

    gridlines_lower_bound: float
    """ Lower bound of the highlighting range

    :type: float
    """

    gridlines_range_color: bpy_prop_array[float]
    """ Color used to highlight the range

    :type: bpy_prop_array[float]
    """

    gridlines_upper_bound: float
    """ Upper bound of the highlighting range

    :type: float
    """

    guide_alpha: float
    """ Guiding weight (higher value results in greater lag)

    :type: float
    """

    guide_beta: int
    """ Guiding size (higher value results in larger vortices)

    :type: int
    """

    guide_parent: Object
    """ Use velocities from this object for the guiding effect (object needs to have fluid modifier and be of type domain))

    :type: Object
    """

    guide_source: str
    """ Choose where to get guiding velocities from

    :type: str
    """

    guide_vel_factor: float
    """ Guiding velocity factor (higher value results in greater guiding velocities)

    :type: float
    """

    has_cache_baked_any: bool
    """ 

    :type: bool
    """

    has_cache_baked_data: bool
    """ 

    :type: bool
    """

    has_cache_baked_guide: bool
    """ 

    :type: bool
    """

    has_cache_baked_mesh: bool
    """ 

    :type: bool
    """

    has_cache_baked_noise: bool
    """ 

    :type: bool
    """

    has_cache_baked_particles: bool
    """ 

    :type: bool
    """

    heat_grid: bpy_prop_array[float]
    """ Smoke heat grid

    :type: bpy_prop_array[float]
    """

    highres_sampling: str
    """ Method for sampling the high resolution flow

    :type: str
    """

    is_cache_baking_any: bool
    """ 

    :type: bool
    """

    is_cache_baking_data: bool
    """ 

    :type: bool
    """

    is_cache_baking_guide: bool
    """ 

    :type: bool
    """

    is_cache_baking_mesh: bool
    """ 

    :type: bool
    """

    is_cache_baking_noise: bool
    """ 

    :type: bool
    """

    is_cache_baking_particles: bool
    """ 

    :type: bool
    """

    mesh_concave_lower: float
    """ Lower mesh concavity bound (high values tend to smoothen and fill out concave regions)

    :type: float
    """

    mesh_concave_upper: float
    """ Upper mesh concavity bound (high values tend to smoothen and fill out concave regions)

    :type: float
    """

    mesh_generator: str
    """ Which particle level set generator to use

    :type: str
    """

    mesh_particle_radius: float
    """ Particle radius factor (higher value results in larger (meshed) particles). Needs to be adjusted after changing the mesh scale

    :type: float
    """

    mesh_scale: int
    """ The mesh simulation is scaled up by this factor (compared to the base resolution of the domain). For best meshing, it is recommended to adjust the mesh particle radius alongside this value

    :type: int
    """

    mesh_smoothen_neg: int
    """ Negative mesh smoothening

    :type: int
    """

    mesh_smoothen_pos: int
    """ Positive mesh smoothening

    :type: int
    """

    noise_pos_scale: float
    """ Scale of noise (higher value results in larger vortices)

    :type: float
    """

    noise_scale: int
    """ The noise simulation is scaled up by this factor (compared to the base resolution of the domain)

    :type: int
    """

    noise_strength: float
    """ Strength of noise

    :type: float
    """

    noise_time_anim: float
    """ Animation time of noise

    :type: float
    """

    openvdb_cache_compress_type: str
    """ Compression method to be used

    :type: str
    """

    openvdb_data_depth: str
    """ Bit depth for fluid particles and grids (lower bit values reduce file size)

    :type: str
    """

    particle_band_width: float
    """ Particle (narrow) band width (higher value results in thicker band and more particles)

    :type: float
    """

    particle_max: int
    """ Maximum number of particles per cell (ensures that each cell has at most this amount of particles)

    :type: int
    """

    particle_min: int
    """ Minimum number of particles per cell (ensures that each cell has at least this amount of particles)

    :type: int
    """

    particle_number: int
    """ Particle number factor (higher value results in more particles)

    :type: int
    """

    particle_radius: float
    """ Particle radius factor. Increase this value if the simulation appears to leak volume, decrease it if the simulation seems to gain volume

    :type: float
    """

    particle_randomness: float
    """ Randomness factor for particle sampling

    :type: float
    """

    particle_scale: int
    """ The particle simulation is scaled up by this factor (compared to the base resolution of the domain)

    :type: int
    """

    resolution_max: int
    """ Resolution used for the fluid domain. Value corresponds to the longest domain side (resolution for other domain sides is calculated automatically)

    :type: int
    """

    show_gridlines: bool
    """ Show gridlines

    :type: bool
    """

    show_velocity: bool
    """ Visualize vector fields

    :type: bool
    """

    simulation_method: str
    """ Change the underlying simulation method

    :type: str
    """

    slice_axis: str
    """ 

    :type: str
    """

    slice_depth: float
    """ Position of the slice

    :type: float
    """

    slice_per_voxel: float
    """ How many slices per voxel should be generated

    :type: float
    """

    sndparticle_boundary: str
    """ How particles that left the domain are treated

    :type: str
    """

    sndparticle_bubble_buoyancy: float
    """ Amount of buoyancy force that rises bubbles (high value results in bubble movement mainly upwards)

    :type: float
    """

    sndparticle_bubble_drag: float
    """ Amount of drag force that moves bubbles along with the fluid (high value results in bubble movement mainly along with the fluid)

    :type: float
    """

    sndparticle_combined_export: str
    """ Determines which particle systems are created from secondary particles

    :type: str
    """

    sndparticle_life_max: float
    """ Highest possible particle lifetime

    :type: float
    """

    sndparticle_life_min: float
    """ Lowest possible particle lifetime

    :type: float
    """

    sndparticle_potential_max_energy: float
    """ Upper clamping threshold that indicates the fluid speed where cells no longer emit more particles (higher value results in generally less particles)

    :type: float
    """

    sndparticle_potential_max_trappedair: float
    """ Upper clamping threshold for marking fluid cells where air is trapped (higher value results in less marked cells)

    :type: float
    """

    sndparticle_potential_max_wavecrest: float
    """ Upper clamping threshold for marking fluid cells as wave crests (higher value results in less marked cells)

    :type: float
    """

    sndparticle_potential_min_energy: float
    """ Lower clamping threshold that indicates the fluid speed where cells start to emit particles (lower values result in generally more particles)

    :type: float
    """

    sndparticle_potential_min_trappedair: float
    """ Lower clamping threshold for marking fluid cells where air is trapped (lower value results in more marked cells)

    :type: float
    """

    sndparticle_potential_min_wavecrest: float
    """ Lower clamping threshold for marking fluid cells as wave crests (lower value results in more marked cells)

    :type: float
    """

    sndparticle_potential_radius: int
    """ Radius to compute potential for each cell (higher values are slower but create smoother potential grids)

    :type: int
    """

    sndparticle_sampling_trappedair: int
    """ Maximum number of particles generated per trapped air cell per frame

    :type: int
    """

    sndparticle_sampling_wavecrest: int
    """ Maximum number of particles generated per wave crest cell per frame

    :type: int
    """

    sndparticle_update_radius: int
    """ Radius to compute position update for each particle (higher values are slower but particles move less chaotic)

    :type: int
    """

    start_point: mathutils.Vector
    """ Start point

    :type: mathutils.Vector
    """

    surface_tension: float
    """ Surface tension of liquid (higher value results in greater hydrophobic behavior)

    :type: float
    """

    sys_particle_maximum: int
    """ Maximum number of fluid particles that are allowed in this simulation

    :type: int
    """

    temperature_grid: bpy_prop_array[float]
    """ Smoke temperature grid, range 0 to 1 represents 0 to 1000K

    :type: bpy_prop_array[float]
    """

    time_scale: float
    """ Adjust simulation speed

    :type: float
    """

    timesteps_max: int
    """ Maximum number of simulation steps to perform for one frame

    :type: int
    """

    timesteps_min: int
    """ Minimum number of simulation steps to perform for one frame

    :type: int
    """

    use_adaptive_domain: bool
    """ Adapt simulation resolution and size to fluid

    :type: bool
    """

    use_adaptive_timesteps: bool
    """ 

    :type: bool
    """

    use_bubble_particles: bool
    """ Create bubble particle system

    :type: bool
    """

    use_collision_border_back: bool
    """ Enable collisions with back domain border

    :type: bool
    """

    use_collision_border_bottom: bool
    """ Enable collisions with bottom domain border

    :type: bool
    """

    use_collision_border_front: bool
    """ Enable collisions with front domain border

    :type: bool
    """

    use_collision_border_left: bool
    """ Enable collisions with left domain border

    :type: bool
    """

    use_collision_border_right: bool
    """ Enable collisions with right domain border

    :type: bool
    """

    use_collision_border_top: bool
    """ Enable collisions with top domain border

    :type: bool
    """

    use_color_ramp: bool
    """ Render a simulation field while mapping its voxels values to the colors of a ramp or using a predefined color code

    :type: bool
    """

    use_diffusion: bool
    """ Enable fluid diffusion settings (e.g. viscosity, surface tension)

    :type: bool
    """

    use_dissolve_smoke: bool
    """ Let smoke disappear over time

    :type: bool
    """

    use_dissolve_smoke_log: bool
    """ Dissolve smoke in a logarithmic fashion. Dissolves quickly at first, but lingers longer

    :type: bool
    """

    use_flip_particles: bool
    """ Create liquid particle system

    :type: bool
    """

    use_foam_particles: bool
    """ Create foam particle system

    :type: bool
    """

    use_fractions: bool
    """ Fractional obstacles improve and smoothen the fluid-obstacle boundary

    :type: bool
    """

    use_guide: bool
    """ Enable fluid guiding

    :type: bool
    """

    use_mesh: bool
    """ Enable fluid mesh (using amplification)

    :type: bool
    """

    use_noise: bool
    """ Enable fluid noise (using amplification)

    :type: bool
    """

    use_slice: bool
    """ Perform a single slice of the domain object

    :type: bool
    """

    use_speed_vectors: bool
    """ Caches velocities of mesh vertices. These will be used (automatically) when rendering with motion blur enabled

    :type: bool
    """

    use_spray_particles: bool
    """ Create spray particle system

    :type: bool
    """

    use_tracer_particles: bool
    """ Create tracer particle system

    :type: bool
    """

    use_viscosity: bool
    """ Simulate fluids with high viscosity using a special solver

    :type: bool
    """

    vector_display_type: str
    """ 

    :type: str
    """

    vector_field: str
    """ Vector field to be represented by the display vectors

    :type: str
    """

    vector_scale: float
    """ Multiplier for scaling the vectors

    :type: float
    """

    vector_scale_with_magnitude: bool
    """ Scale vectors with their magnitudes

    :type: bool
    """

    vector_show_mac_x: bool
    """ Show X-component of MAC Grid

    :type: bool
    """

    vector_show_mac_y: bool
    """ Show Y-component of MAC Grid

    :type: bool
    """

    vector_show_mac_z: bool
    """ Show Z-component of MAC Grid

    :type: bool
    """

    velocity_grid: bpy_prop_array[float]
    """ Smoke velocity grid

    :type: bpy_prop_array[float]
    """

    velocity_scale: float
    """ Factor to control the amount of motion blur

    :type: float
    """

    viscosity_base: float
    """ Viscosity setting: value that is multiplied by 10 to the power of (exponent*-1)

    :type: float
    """

    viscosity_exponent: int
    """ Negative exponent for the viscosity value (to simplify entering small values e.g. 5*10^-6)

    :type: int
    """

    viscosity_value: float
    """ Viscosity of liquid (higher values result in more viscous fluids, a value of 0 will still apply some viscosity)

    :type: float
    """

    vorticity: float
    """ Amount of turbulence and rotation in smoke

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

import typing
import collections.abc
import mathutils
from .aov import AOV
from .struct import Struct
from .lightgroup import Lightgroup
from .bpy_struct import bpy_struct
from .freestyle_settings import FreestyleSettings
from .view_layer_eevee import ViewLayerEEVEE
from .material import Material
from .layer_objects import LayerObjects
from .lightgroups import Lightgroups
from .ao_vs import AOVs
from .layer_collection import LayerCollection
from .depsgraph import Depsgraph

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ViewLayer(bpy_struct):
    """View layer"""

    active_aov: AOV
    """ Active AOV

    :type: AOV
    """

    active_aov_index: int | None
    """ Index of active AOV

    :type: int | None
    """

    active_layer_collection: LayerCollection
    """ Active layer collection in this view layer's hierarchy

    :type: LayerCollection
    """

    active_lightgroup: Lightgroup
    """ Active Lightgroup

    :type: Lightgroup
    """

    active_lightgroup_index: int | None
    """ Index of active lightgroup

    :type: int | None
    """

    aovs: AOVs
    """ 

    :type: AOVs
    """

    cycles: typing.Any
    """ Cycles ViewLayer Settings

    :type: typing.Any
    """

    depsgraph: Depsgraph
    """ Dependencies in the scene data

    :type: Depsgraph
    """

    eevee: ViewLayerEEVEE
    """ View layer settings for EEVEE

    :type: ViewLayerEEVEE
    """

    freestyle_settings: FreestyleSettings
    """ 

    :type: FreestyleSettings
    """

    layer_collection: LayerCollection
    """ Root of collections hierarchy of this view layer, its 'collection' pointer property is the same as the scene's master collection

    :type: LayerCollection
    """

    lightgroups: Lightgroups
    """ 

    :type: Lightgroups
    """

    material_override: Material
    """ Material to override all other materials in this view layer

    :type: Material
    """

    name: str
    """ View layer name

    :type: str
    """

    objects: LayerObjects
    """ All the objects in this layer

    :type: LayerObjects
    """

    pass_alpha_threshold: float
    """ Z, Index, normal, UV and vector passes are only affected by surfaces with alpha transparency equal to or higher than this threshold

    :type: float
    """

    pass_cryptomatte_depth: int
    """ Sets how many unique objects can be distinguished per pixel

    :type: int
    """

    samples: int
    """ Override number of render samples for this view layer, 0 will use the scene setting

    :type: int
    """

    use: bool
    """ Enable or disable rendering of this View Layer

    :type: bool
    """

    use_ao: bool
    """ Render Ambient Occlusion in this Layer

    :type: bool
    """

    use_freestyle: bool
    """ Render stylized strokes in this Layer

    :type: bool
    """

    use_motion_blur: bool
    """ Render motion blur in this Layer, if enabled in the scene

    :type: bool
    """

    use_pass_ambient_occlusion: bool
    """ Deliver Ambient Occlusion pass

    :type: bool
    """

    use_pass_combined: bool
    """ Deliver full combined RGBA buffer

    :type: bool
    """

    use_pass_cryptomatte_accurate: bool
    """ Generate a more accurate cryptomatte pass

    :type: bool
    """

    use_pass_cryptomatte_asset: bool
    """ Render cryptomatte asset pass, for isolating groups of objects with the same parent

    :type: bool
    """

    use_pass_cryptomatte_material: bool
    """ Render cryptomatte material pass, for isolating materials in compositing

    :type: bool
    """

    use_pass_cryptomatte_object: bool
    """ Render cryptomatte object pass, for isolating objects in compositing

    :type: bool
    """

    use_pass_diffuse_color: bool
    """ Deliver diffuse color pass

    :type: bool
    """

    use_pass_diffuse_direct: bool
    """ Deliver diffuse direct pass

    :type: bool
    """

    use_pass_diffuse_indirect: bool
    """ Deliver diffuse indirect pass

    :type: bool
    """

    use_pass_emit: bool
    """ Deliver emission pass

    :type: bool
    """

    use_pass_environment: bool
    """ Deliver environment lighting pass

    :type: bool
    """

    use_pass_glossy_color: bool
    """ Deliver glossy color pass

    :type: bool
    """

    use_pass_glossy_direct: bool
    """ Deliver glossy direct pass

    :type: bool
    """

    use_pass_glossy_indirect: bool
    """ Deliver glossy indirect pass

    :type: bool
    """

    use_pass_material_index: bool
    """ Deliver material index pass

    :type: bool
    """

    use_pass_mist: bool
    """ Deliver mist factor pass (0.0 to 1.0)

    :type: bool
    """

    use_pass_normal: bool
    """ Deliver normal pass

    :type: bool
    """

    use_pass_object_index: bool
    """ Deliver object index pass

    :type: bool
    """

    use_pass_position: bool
    """ Deliver position pass

    :type: bool
    """

    use_pass_shadow: bool
    """ Deliver shadow pass

    :type: bool
    """

    use_pass_subsurface_color: bool
    """ Deliver subsurface color pass

    :type: bool
    """

    use_pass_subsurface_direct: bool
    """ Deliver subsurface direct pass

    :type: bool
    """

    use_pass_subsurface_indirect: bool
    """ Deliver subsurface indirect pass

    :type: bool
    """

    use_pass_transmission_color: bool
    """ Deliver transmission color pass

    :type: bool
    """

    use_pass_transmission_direct: bool
    """ Deliver transmission direct pass

    :type: bool
    """

    use_pass_transmission_indirect: bool
    """ Deliver transmission indirect pass

    :type: bool
    """

    use_pass_uv: bool
    """ Deliver texture UV pass

    :type: bool
    """

    use_pass_vector: bool
    """ Deliver speed vector pass

    :type: bool
    """

    use_pass_z: bool
    """ Deliver Z values pass

    :type: bool
    """

    use_sky: bool
    """ Render Sky in this Layer

    :type: bool
    """

    use_solid: bool
    """ Render Solid faces in this Layer

    :type: bool
    """

    use_strand: bool
    """ Render Strands in this Layer

    :type: bool
    """

    use_volumes: bool
    """ Render volumes in this Layer

    :type: bool
    """

    @classmethod
    def update_render_passes(cls):
        """Requery the enabled render passes from the render engine"""
        ...

    def update(self):
        """Update data tagged to be updated from previous access to data or operators"""
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

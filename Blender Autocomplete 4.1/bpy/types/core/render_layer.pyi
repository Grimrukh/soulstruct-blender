import typing
import collections.abc
import mathutils
from .render_passes import RenderPasses
from .struct import Struct
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class RenderLayer(bpy_struct):
    name: str
    """ View layer name

    :type: str
    """

    passes: RenderPasses
    """ 

    :type: RenderPasses
    """

    use_ao: bool
    """ Render Ambient Occlusion in this Layer

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

    def load_from_file(
        self,
        filepath: str | typing.Any,
        x: typing.Any | None = 0,
        y: typing.Any | None = 0,
    ):
        """Copies the pixels of this renderlayer from an image file

        :param filepath: File Path, File path to load into this render tile, must be no smaller than the renderlayer
        :type filepath: str | typing.Any
        :param x: Offset X, Offset the position to copy from if the image is larger than the render layer
        :type x: typing.Any | None
        :param y: Offset Y, Offset the position to copy from if the image is larger than the render layer
        :type y: typing.Any | None
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

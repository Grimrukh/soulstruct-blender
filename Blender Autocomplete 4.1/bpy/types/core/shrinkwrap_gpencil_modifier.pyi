import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .material import Material
from .object import Object
from .gpencil_modifier import GpencilModifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShrinkwrapGpencilModifier(GpencilModifier, bpy_struct):
    """Shrink wrapping modifier to shrink wrap and object to a target"""

    auxiliary_target: Object
    """ Additional mesh target to shrink to

    :type: Object
    """

    cull_face: str
    """ Stop vertices from projecting to a face on the target when facing towards/away

    :type: str
    """

    invert_layer_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_layers: bool
    """ Inverse filter

    :type: bool
    """

    invert_material_pass: bool
    """ Inverse filter

    :type: bool
    """

    invert_materials: bool
    """ Inverse filter

    :type: bool
    """

    invert_vertex: bool
    """ Inverse filter

    :type: bool
    """

    layer: str
    """ Layer name

    :type: str
    """

    layer_pass: int
    """ Layer pass index

    :type: int
    """

    material: Material
    """ Material used for filtering effect

    :type: Material
    """

    offset: float
    """ Distance to keep from the target

    :type: float
    """

    pass_index: int
    """ Pass index

    :type: int
    """

    project_limit: float
    """ Limit the distance used for projection (zero disables)

    :type: float
    """

    smooth_factor: float
    """ Amount of smoothing to apply

    :type: float
    """

    smooth_step: int
    """ Number of times to apply smooth (high numbers can reduce FPS)

    :type: int
    """

    subsurf_levels: int
    """ Number of subdivisions that must be performed before extracting vertices' positions and normals

    :type: int
    """

    target: Object
    """ Mesh target to shrink to

    :type: Object
    """

    use_invert_cull: bool
    """ When projecting in the negative direction invert the face cull mode

    :type: bool
    """

    use_negative_direction: bool
    """ Allow vertices to move in the negative direction of axis

    :type: bool
    """

    use_positive_direction: bool
    """ Allow vertices to move in the positive direction of axis

    :type: bool
    """

    use_project_x: bool
    """ 

    :type: bool
    """

    use_project_y: bool
    """ 

    :type: bool
    """

    use_project_z: bool
    """ 

    :type: bool
    """

    vertex_group: str
    """ Vertex group name for modulating the deform

    :type: str
    """

    wrap_method: str
    """ 

    :type: str
    """

    wrap_mode: str
    """ Select how vertices are constrained to the target surface

    :type: str
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

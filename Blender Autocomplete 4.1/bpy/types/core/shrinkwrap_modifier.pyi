import typing
import collections.abc
import mathutils
from .struct import Struct
from .bpy_struct import bpy_struct
from .object import Object
from .modifier import Modifier

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class ShrinkwrapModifier(Modifier, bpy_struct):
    """Shrink wrapping modifier to shrink wrap and object to a target"""

    auxiliary_target: Object
    """ Additional mesh target to shrink to

    :type: Object
    """

    cull_face: str
    """ Stop vertices from projecting to a face on the target when facing towards/away

    :type: str
    """

    invert_vertex_group: bool
    """ Invert vertex group influence

    :type: bool
    """

    offset: float
    """ Distance to keep from the target

    :type: float
    """

    project_limit: float
    """ Limit the distance used for projection (zero disables)

    :type: float
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
    """ Vertex group name

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

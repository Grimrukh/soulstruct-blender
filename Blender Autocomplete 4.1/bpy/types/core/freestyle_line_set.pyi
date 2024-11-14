import typing
import collections.abc
import mathutils
from .freestyle_line_style import FreestyleLineStyle
from .struct import Struct
from .collection import Collection
from .bpy_struct import bpy_struct

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class FreestyleLineSet(bpy_struct):
    """Line set for associating lines and style parameters"""

    collection: Collection
    """ A collection of objects based on which feature edges are selected

    :type: Collection
    """

    collection_negation: str
    """ Specify either inclusion or exclusion of feature edges belonging to a collection of objects

    :type: str
    """

    edge_type_combination: str
    """ Specify a logical combination of selection conditions on feature edge types

    :type: str
    """

    edge_type_negation: str
    """ Specify either inclusion or exclusion of feature edges selected by edge types

    :type: str
    """

    exclude_border: bool
    """ Exclude border edges

    :type: bool
    """

    exclude_contour: bool
    """ Exclude contours

    :type: bool
    """

    exclude_crease: bool
    """ Exclude crease edges

    :type: bool
    """

    exclude_edge_mark: bool
    """ Exclude edge marks

    :type: bool
    """

    exclude_external_contour: bool
    """ Exclude external contours

    :type: bool
    """

    exclude_material_boundary: bool
    """ Exclude edges at material boundaries

    :type: bool
    """

    exclude_ridge_valley: bool
    """ Exclude ridges and valleys

    :type: bool
    """

    exclude_silhouette: bool
    """ Exclude silhouette edges

    :type: bool
    """

    exclude_suggestive_contour: bool
    """ Exclude suggestive contours

    :type: bool
    """

    face_mark_condition: str
    """ Specify a feature edge selection condition based on face marks

    :type: str
    """

    face_mark_negation: str
    """ Specify either inclusion or exclusion of feature edges selected by face marks

    :type: str
    """

    linestyle: FreestyleLineStyle
    """ Line style settings

    :type: FreestyleLineStyle
    """

    name: str
    """ Line set name

    :type: str
    """

    qi_end: int
    """ Last QI value of the QI range

    :type: int
    """

    qi_start: int
    """ First QI value of the QI range

    :type: int
    """

    select_border: bool
    """ Select border edges (open mesh edges)

    :type: bool
    """

    select_by_collection: bool
    """ Select feature edges based on a collection of objects

    :type: bool
    """

    select_by_edge_types: bool
    """ Select feature edges based on edge types

    :type: bool
    """

    select_by_face_marks: bool
    """ Select feature edges by face marks

    :type: bool
    """

    select_by_image_border: bool
    """ Select feature edges by image border (less memory consumption)

    :type: bool
    """

    select_by_visibility: bool
    """ Select feature edges based on visibility

    :type: bool
    """

    select_contour: bool
    """ Select contours (outer silhouettes of each object)

    :type: bool
    """

    select_crease: bool
    """ Select crease edges (those between two faces making an angle smaller than the Crease Angle)

    :type: bool
    """

    select_edge_mark: bool
    """ Select edge marks (edges annotated by Freestyle edge marks)

    :type: bool
    """

    select_external_contour: bool
    """ Select external contours (outer silhouettes of occluding and occluded objects)

    :type: bool
    """

    select_material_boundary: bool
    """ Select edges at material boundaries

    :type: bool
    """

    select_ridge_valley: bool
    """ Select ridges and valleys (boundary lines between convex and concave areas of surface)

    :type: bool
    """

    select_silhouette: bool
    """ Select silhouettes (edges at the boundary of visible and hidden faces)

    :type: bool
    """

    select_suggestive_contour: bool
    """ Select suggestive contours (almost silhouette/contour edges)

    :type: bool
    """

    show_render: bool
    """ Enable or disable this line set during stroke rendering

    :type: bool
    """

    visibility: str
    """ Determine how to use visibility for feature edge selection

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

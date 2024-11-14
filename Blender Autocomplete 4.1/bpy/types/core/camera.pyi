import typing
import collections.abc
import mathutils
from .camera_dof_settings import CameraDOFSettings
from .struct import Struct
from .bpy_struct import bpy_struct
from .anim_data import AnimData
from .camera_background_images import CameraBackgroundImages
from .id import ID
from .camera_stereo_data import CameraStereoData
from .scene import Scene

GenericType1 = typing.TypeVar("GenericType1")
GenericType2 = typing.TypeVar("GenericType2")


class Camera(ID, bpy_struct):
    """Camera data-block for storing camera settings"""

    angle: float
    """ Camera lens field of view

    :type: float
    """

    angle_x: float
    """ Camera lens horizontal field of view

    :type: float
    """

    angle_y: float
    """ Camera lens vertical field of view

    :type: float
    """

    animation_data: AnimData
    """ Animation data for this data-block

    :type: AnimData
    """

    background_images: CameraBackgroundImages
    """ List of background images

    :type: CameraBackgroundImages
    """

    clip_end: float
    """ Camera far clipping distance

    :type: float
    """

    clip_start: float
    """ Camera near clipping distance

    :type: float
    """

    display_size: float
    """ Apparent size of the Camera object in the 3D View

    :type: float
    """

    dof: CameraDOFSettings
    """ 

    :type: CameraDOFSettings
    """

    fisheye_fov: float
    """ Field of view for the fisheye lens

    :type: float
    """

    fisheye_lens: float
    """ Lens focal length (mm)

    :type: float
    """

    fisheye_polynomial_k0: float
    """ Coefficient K0 of the lens polynomial

    :type: float
    """

    fisheye_polynomial_k1: float
    """ Coefficient K1 of the lens polynomial

    :type: float
    """

    fisheye_polynomial_k2: float
    """ Coefficient K2 of the lens polynomial

    :type: float
    """

    fisheye_polynomial_k3: float
    """ Coefficient K3 of the lens polynomial

    :type: float
    """

    fisheye_polynomial_k4: float
    """ Coefficient K4 of the lens polynomial

    :type: float
    """

    latitude_max: float
    """ Maximum latitude (vertical angle) for the equirectangular lens

    :type: float
    """

    latitude_min: float
    """ Minimum latitude (vertical angle) for the equirectangular lens

    :type: float
    """

    lens: float
    """ Perspective Camera focal length value in millimeters

    :type: float
    """

    lens_unit: str
    """ Unit to edit lens in for the user interface

    :type: str
    """

    longitude_max: float
    """ Maximum longitude (horizontal angle) for the equirectangular lens

    :type: float
    """

    longitude_min: float
    """ Minimum longitude (horizontal angle) for the equirectangular lens

    :type: float
    """

    ortho_scale: float
    """ Orthographic Camera scale (similar to zoom)

    :type: float
    """

    panorama_type: str
    """ Distortion to use for the calculation

    :type: str
    """

    passepartout_alpha: float
    """ Opacity (alpha) of the darkened overlay in Camera view

    :type: float
    """

    sensor_fit: str
    """ Method to fit image and field of view angle inside the sensor

    :type: str
    """

    sensor_height: float
    """ Vertical size of the image sensor area in millimeters

    :type: float
    """

    sensor_width: float
    """ Horizontal size of the image sensor area in millimeters

    :type: float
    """

    shift_x: float
    """ Camera horizontal shift

    :type: float
    """

    shift_y: float
    """ Camera vertical shift

    :type: float
    """

    show_background_images: bool
    """ Display reference images behind objects in the 3D View

    :type: bool
    """

    show_composition_center: bool
    """ Display center composition guide inside the camera view

    :type: bool
    """

    show_composition_center_diagonal: bool
    """ Display diagonal center composition guide inside the camera view

    :type: bool
    """

    show_composition_golden: bool
    """ Display golden ratio composition guide inside the camera view

    :type: bool
    """

    show_composition_golden_tria_a: bool
    """ Display golden triangle A composition guide inside the camera view

    :type: bool
    """

    show_composition_golden_tria_b: bool
    """ Display golden triangle B composition guide inside the camera view

    :type: bool
    """

    show_composition_harmony_tri_a: bool
    """ Display harmony A composition guide inside the camera view

    :type: bool
    """

    show_composition_harmony_tri_b: bool
    """ Display harmony B composition guide inside the camera view

    :type: bool
    """

    show_composition_thirds: bool
    """ Display rule of thirds composition guide inside the camera view

    :type: bool
    """

    show_limits: bool
    """ Display the clipping range and focus point on the camera

    :type: bool
    """

    show_mist: bool
    """ Display a line from the Camera to indicate the mist area

    :type: bool
    """

    show_name: bool
    """ Show the active Camera's name in Camera view

    :type: bool
    """

    show_passepartout: bool
    """ Show a darkened overlay outside the image area in Camera view

    :type: bool
    """

    show_safe_areas: bool
    """ Show TV title safe and action safe areas in Camera view

    :type: bool
    """

    show_safe_center: bool
    """ Show safe areas to fit content in a different aspect ratio

    :type: bool
    """

    show_sensor: bool
    """ Show sensor size (film gate) in Camera view

    :type: bool
    """

    stereo: CameraStereoData
    """ 

    :type: CameraStereoData
    """

    type: str
    """ Camera types

    :type: str
    """

    def view_frame(self, scene: Scene | None = None):
        """Return 4 points for the cameras frame (before object transformation)

                :param scene: Scene to use for aspect calculation, when omitted 1:1 aspect is used
                :type scene: Scene | None
                :return: result_1, Result, `mathutils.Vector` of 3 items in [-inf, inf]

        result_2, Result, `mathutils.Vector` of 3 items in [-inf, inf]

        result_3, Result, `mathutils.Vector` of 3 items in [-inf, inf]

        result_4, Result, `mathutils.Vector` of 3 items in [-inf, inf]
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

from __future__ import annotations

__all__ = ["ExportHKXCutscene"]

import traceback
import typing as tp
from multiprocessing import Pool, Queue
from pathlib import Path

import bmesh
import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from mathutils import Euler, Matrix, Vector
from bpy_extras.io_utils import ExportHelper
from soulstruct.containers.dcx import DCXType

from soulstruct.containers import Binder, BinderEntry
from soulstruct.base.models.flver import FLVER, Version
from soulstruct.base.models.flver.vertex import VertexBuffer, BufferLayout, LayoutMember, MemberType, MemberFormat
from soulstruct.utilities.maths import Vector3

from io_soulstruct.utilities import *
from .utilities import HKXCutsceneExportError


class ExportHKXCutscene(LoggingOperator, ExportHelper):
    """Export RemoBND cutscene animation from Actions attached to all selected FLVER armatures."""
    bl_idname = "export_scene.hkx_cutscene"
    bl_label = "Export HKX Cutscene"
    bl_description = "Export all selected armatures' Blender actions to a RemoBND cutscene file"

    # ExportHelper mixin class uses this
    filename_ext = ".remobnd"

    filter_glob: StringProperty(
        default="*.remobnd;*.remobnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    dcx_type: get_dcx_enum_property(DCXType.DS1_DS2)  # DS1 RemoBND default

    @classmethod
    def poll(cls, context):
        # TODO: All selected objects must be armatures.
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        # TODO
        print("Executing HKX cutscene export...")
        return {"FINISHED"}

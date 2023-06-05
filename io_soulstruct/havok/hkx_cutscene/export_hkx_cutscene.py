from __future__ import annotations

__all__ = ["ExportHKXCutscene"]

import traceback
import typing as tp
from multiprocessing import Pool, Queue
from pathlib import Path

import bmesh
import bpy
import bpy_types
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty
from mathutils import Euler, Matrix, Vector
from bpy_extras.io_utils import ExportHelper
from soulstruct.containers.dcx import DCXType

from soulstruct.containers import Binder, BinderEntry
from soulstruct.base.models.flver import FLVER, Version
from soulstruct.base.models.flver.vertex import VertexBuffer, BufferLayout, LayoutMember, MemberType, MemberFormat
from soulstruct.base.models.flver.material import MTDInfo
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

    dcx_type: EnumProperty(
        name="Compression",
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        description="Type of DCX compression to apply to exported file",
        default="DCX_DFLT_10000_24_9",  # DS1 default
    )

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
        return {'FINISHED'}

from __future__ import annotations

__all__ = [
    "FLVERImportError",
    "FLVERExportError",
    "PrintGameTransform",
    "parse_dummy_name",
    "HideAllDummiesOperator",
    "ShowAllDummiesOperator",
    "get_flver_from_binder",
    "get_map_piece_msb_transforms",
    "game_forward_up_vectors_to_bl_euler",
    "bl_euler_to_game_forward_up_vectors",
    "bl_rotmat_to_game_forward_up_vectors",
    "BufferLayoutFactory",
    "MTDInfo",
]

import re
import typing as tp
from dataclasses import dataclass, field
from pathlib import Path

from mathutils import Euler, Matrix

from soulstruct import Binder, FLVER
from soulstruct.utilities.maths import Vector3, Matrix3
from soulstruct.darksouls1r.maps import MSB, get_map
from soulstruct.base.models.flver.vertex import MemberType, MemberFormat, LayoutMember, BufferLayout
from soulstruct.base.models.mtd import MTD

from io_soulstruct.utilities import (
    Transform, BlenderTransform, GAME_TO_BL_EULER, BL_TO_GAME_EULER, BL_TO_GAME_MAT3, LoggingOperator
)


DUMMY_NAME_RE = re.compile(  # accepts and ignore Blender '.001' suffix, etc.
    r"^(?P<other_model>\[\w+])? *Dummy<(?P<index>\d+)> *(?P<reference_id>\[\d+]) *(\.\d+)?$"
)


class FLVERImportError(Exception):
    """Exception raised during FLVER import."""
    pass


class FLVERExportError(Exception):
    """Exception raised during FLVER export."""
    pass


class HideAllDummiesOperator(LoggingOperator):
    """Simple operator to hide all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.hide_all_dummies"
    bl_label = "Hide All Dummies"
    bl_description = "Hide all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        """At least one Blender Mesh selected."""
        return len(context.selected_objects) > 0 and all(obj.type == "MESH" for obj in context.selected_objects)

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        armature = context.selected_objects[0]
        for child in armature.children:
            if child.type == "EMPTY" and "dummy" in child.name.lower():
                child.hide_viewport = True
        return {"FINISHED"}


class ShowAllDummiesOperator(LoggingOperator):
    """Simple operator to show all dummy children of a selected FLVER armature."""
    bl_idname = "io_scene_soulstruct.show_all_dummies"
    bl_label = "Show All Dummies"
    bl_description = "Show all dummy point children in the selected armature (Empties with 'Dummy' in name)"

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        armature = context.selected_objects[0]
        for child in armature.children:
            if child.type == "EMPTY" and "dummy" in child.name.lower():
                child.hide_viewport = False
        return {"FINISHED"}


class PrintGameTransform(LoggingOperator):
    """Simple operator that prints the Blender transform of a selected object to console in game coordinates."""
    bl_idname = "io_scene_soulstruct.print_game_transform"
    bl_label = "Print Game Transform"
    bl_description = "Print the selected object's transform in game coordinates to console."

    @classmethod
    def poll(cls, context):
        return context.object is not None

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        obj = context.object
        if obj:
            bl_transform = BlenderTransform(obj.location, obj.rotation_euler, obj.scale)
            print(
                f"FromSoftware game transform of object '{obj.name}':\n"
                f"    translate = {repr(bl_transform.game_translate)}\n"
                f"    rotate = {repr(bl_transform.game_rotate_rad)}\n"
                f"    scale = {repr(bl_transform.game_scale)}"
            )
        return {"FINISHED"}


def parse_dummy_name(dummy_name: str) -> dict[str, str | int]:
    """Parse a FLVER dummy name into its component parts: `other_model`, `index`, and `reference_id`.

    Returns a dictionary with keys `other_model` (str, optional), `index` (int), and `reference_id` (int).

    If the dummy name is invalid, an empty dictionary is returned.
    """
    match = DUMMY_NAME_RE.match(dummy_name)
    if match is None:
        return {}  # invalid name
    other_model = match.group("other_model")
    return {
        "other_model": other_model[1:-1] if other_model else "",  # exclude brackets
        "index": int(match.group("index")),
        "reference_id": int(match.group("reference_id")[1:-1]),  # exclude brackets
    }


def get_flver_from_binder(binder: Binder, file_path: Path) -> FLVER:
    flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
    if not flver_entries:
        raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
    elif len(flver_entries) > 1:
        raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}.")
    return flver_entries[0].to_binary_file(FLVER)


def get_map_piece_msb_transforms(flver_path: Path, msb_path: Path = None) -> list[tuple[str, Transform]]:
    """Search MSB at `msb_path` (autodetected from `flver_path.parent` by default) and return
    `(map_piece_name, Transform)` pairs for all Map Piece entries using the `flver_path` model."""
    if msb_path is None:
        flver_parent_dir = flver_path.parent
        flver_map = get_map(flver_parent_dir.name)
        msb_path = flver_parent_dir.parent / f"MapStudio/{flver_map.msb_file_stem}.msb"
    if not msb_path.is_file():
        raise FileNotFoundError(f"Cannot find MSB file '{msb_path}'.")
    try:
        msb = MSB.from_path(msb_path)
    except Exception as ex:
        raise RuntimeError(
            f"Cannot open MSB: {ex}.\n"
            f"\nCurrently, only Dark Souls 1 (either version) MSBs are supported."
        )
    matches = []
    for map_piece in msb.map_pieces:
        if flver_path.name.startswith(map_piece.model.name):
            matches.append(map_piece)
    if not matches:
        raise ValueError(f"Cannot find any MSB Map Piece entries using model '{flver_path.name}'.")
    transforms = [(m.name, Transform.from_msb_part(m)) for m in matches]
    return transforms


def game_forward_up_vectors_to_bl_euler(forward: Vector3, up: Vector3) -> Euler:
    """Convert `forward` and `up` vectors to Euler angles `(x, y, z)` (in Blender coordinates).

    Mainly used for representing FLVER dummies in Blender.
    """
    right = up.cross(forward)
    rotation_matrix = Matrix3([
        [right.x, up.x, forward.x],
        [right.y, up.y, forward.y],
        [right.z, up.z, forward.z],
    ])
    game_euler = rotation_matrix.to_euler_angles(radians=True)
    return GAME_TO_BL_EULER(game_euler)


def bl_euler_to_game_forward_up_vectors(bl_euler: Euler) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Euler` to its forward-axis and up-axis vectors in game space (for `FLVER.Dummy`)."""
    game_euler = BL_TO_GAME_EULER(bl_euler)
    game_mat = Matrix3.from_euler_angles(game_euler)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


def bl_rotmat_to_game_forward_up_vectors(bl_rotmat: Matrix) -> tuple[Vector3, Vector3]:
    """Convert a Blender `Matrix` to its game equivalent's forward-axis and up-axis vectors (for `FLVER.Dummy`)."""
    game_mat = BL_TO_GAME_MAT3(bl_rotmat)
    forward = Vector3((game_mat[0][2], game_mat[1][2], game_mat[2][2]))  # third column (Z)
    up = Vector3((game_mat[0][1], game_mat[1][1], game_mat[2][1]))  # second column (Y)
    return forward, up


class BufferLayoutFactory:

    member_unkx_00: int

    def __init__(self, unkx_00: int):
        self.member_unkx_00 = unkx_00

    def member(self, member_type: MemberType, member_format: MemberFormat, index=0):
        return LayoutMember(
            member_type=member_type,
            member_format=member_format,
            index=index,
            unk_x00=self.member_unkx_00,
        )

    def get_ds1_map_buffer_layout(
        self, is_multiple=False, is_lightmap=False, extra_uv_maps: tuple[int, int] = None, no_tangents=False
    ) -> BufferLayout:
        members = [  # always present
            self.member(MemberType.Position, MemberFormat.Float3),
            self.member(MemberType.BoneIndices, MemberFormat.Byte4B),
            self.member(MemberType.Normal, MemberFormat.Byte4C),
            # Tangent/Bitangent will be inserted here if needed.
            self.member(MemberType.VertexColor, MemberFormat.Byte4C),
            # UV/UVPair will be appended here if needed.
        ]

        if not no_tangents:
            members.insert(3, self.member(MemberType.Tangent, MemberFormat.Byte4C))
            if is_multiple:  # has Bitangent
                members.insert(4, self.member(MemberType.Bitangent, MemberFormat.Byte4C))
        elif is_multiple:  # has Bitangent but not Tangent (probably never happens)
            members.insert(3, self.member(MemberType.Bitangent, MemberFormat.Byte4C))

        # Calculate total UV map count and use a combination of UVPair and UV format members below.
        if is_multiple and is_lightmap:  # three UVs
            uv_count = 3
        elif is_multiple or is_lightmap:  # two UVs
            uv_count = 2
        else:  # one UV
            uv_count = 1

        if extra_uv_maps:
            extra_count, first_index = extra_uv_maps
            if first_index > uv_count:
                raise ValueError(
                    f"Material already has {uv_count} UV maps, but extra UV maps start at index {first_index}."
                )
            uv_count = first_index + extra_count  # will add 'dummy' UVs for some shaders (e.g. 'M_3Ivy[DSB].mtd')

        if uv_count > 4:
            raise ValueError(f"Cannot have more than 4 UV maps in a vertex buffer (got {uv_count}).")

        uv_member_index = 0
        while uv_count > 0:  # extra UVs
            # For odd counts, single UV member is added first.
            if uv_count % 2:
                members.append(self.member(MemberType.UV, MemberFormat.UV, index=uv_member_index))
                uv_count -= 1
                uv_member_index += 1
            else:  # must be a non-zero even number remaining
                # Use a UVPair member.
                members.append(self.member(MemberType.UV, MemberFormat.UVPair, index=uv_member_index))
                uv_count -= 2
                uv_member_index += 1

        return BufferLayout(members)

    def get_ds1_chr_buffer_layout(self, is_multiple=False) -> BufferLayout:
        """Default buffer layout for character (and probably object) materials in DS1R."""
        members = [
            self.member(MemberType.Position, MemberFormat.Float3),
            self.member(MemberType.BoneIndices, MemberFormat.Byte4B),
            self.member(MemberType.BoneWeights, MemberFormat.Short4ToFloat4A),
            self.member(MemberType.Normal, MemberFormat.Byte4C),
            self.member(MemberType.Tangent, MemberFormat.Byte4C),
            self.member(MemberType.VertexColor, MemberFormat.Byte4C),
        ]
        if is_multiple:  # has Bitangent and UVPair
            members.insert(5, self.member(MemberType.Bitangent, MemberFormat.Byte4C))
            members.append(self.member(MemberType.UV, MemberFormat.UVPair))
        else:  # one UV
            members.append(self.member(MemberType.UV, MemberFormat.UV))

        return BufferLayout(members)


@dataclass(slots=True)
class MTDInfo:
    """Various booleans that indicate required textures for a specific MTD shader."""

    MTD_DSBH_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(D)?(S)?(B)?(H)?\].*")  # TODO: support 'T" (translucency)
    MTD_M_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(M|ML|LM)\].*")
    MTD_L_RE: tp.ClassVar[re.Pattern] = re.compile(r".*\[(L|ML|LM)\].*")
    # Checked separately: [Dn] (g_Diffuse only), [We] (g_Bumpmap only)

    # MTD name prefixes that indicate two extra UV slots, and the required index of their first UV data.
    # TODO: Why are these different, when both can use M and/or L?
    MTD_FOLIAGE_PREFIXES: tp.ClassVar[str, int] = {
        "M_2Foliage": 1,
        "M_3Ivy": 2,
    }

    # TODO: Hardcoding a set of 'water' shader names I've encountered in DSR.
    WATER_NAMES: tp.ClassVar[set[str]] = {
        "A14_numa.mtd",  # Blighttown swamp
        "A12_DarkRiver.mtd",
        "A12_DarkWater.mtd",
    }

    # Ordered dict mapping texture type names like 'g_Diffuse' to their FLVER vertex UV index/Blender layer (1-indexed).
    texture_types: dict[str, int] = field(default_factory=list)
    # TODO: Some shaders simply don't use the always-empty 'g_DetailBumpmap', but I can find no reliable way to detect
    #  this from their MTD names alone. I may have to guess that they do unless the MTD file is provided.

    alpha: bool = False
    edge: bool = False
    spec: bool = False
    detb: bool = False  # I don't think these shaders are used in DS1. Also `g_EnvSpcSlotNo = 2`...
    is_water: bool = False
    no_tangents: bool = False  # True for unshaded (flag) FLVERs like skybox textures
    extra_uv_maps: None | tuple[int, int] = None  # extra UV slots and first index of them

    @classmethod
    def from_mtd_file(cls, mtd: MTD):
        mtd_info = cls()

        # MTD UV indices are consistent in the sense that lightmap index is always 3, whereas it could actually be
        # FLVER vertex index 2 if only one texture slot is present. So we remove 'UV index gaps' from this.
        remapped_uv_values = {}
        for texture in mtd.textures:
            uv_index = remapped_uv_values.setdefault(texture.uv_index, len(remapped_uv_values) + 1)
            mtd_info.texture_types[texture.texture_type] = uv_index

        blend_mode = mtd.get_param("g_BlendMode", default=0)
        if blend_mode == 1:
            mtd_info.edge = True
        elif blend_mode == 2:
            mtd_info.alpha = True

        env_spc_slot_no = mtd.get_param("g_EnvSpcSlotNo", default=0)
        if env_spc_slot_no == 1:
            mtd_info.spec = True

        detail_bump_power = mtd.get_param("g_DetailBump_BumpPower", default=0.0)
        if detail_bump_power > 0.0:
            mtd_info.detb = True

        lighting_type = mtd.get_param("g_LightingType", default=1)
        if lighting_type == 0:
            mtd_info.no_tangents = True  # e.g. skybox

        return mtd_info

    @classmethod
    def from_mtd_name(cls, mtd_name):
        mtd_info = cls()

        if dsbh_match := cls.MTD_DSBH_RE.match(mtd_name):
            if dsbh_match.group(1):
                mtd_info.texture_types["g_Diffuse"] = 1
            if dsbh_match.group(2):
                mtd_info.texture_types["g_Specular"] = 1
            if dsbh_match.group(3):
                mtd_info.texture_types["g_Bumpmap"] = 1
            if dsbh_match.group(4):
                mtd_info.texture_types["g_Height"] = 1
        elif "[Dn]" in mtd_name:
            mtd_info.texture_types["g_Diffuse"] = 1
            mtd_info.no_tangents = True  # TODO: A few [D] shaders also don't use tangents...
        elif "[We]" in mtd_name or mtd_name in cls.WATER_NAMES:
            mtd_info.texture_types["g_Bumpmap"] = 1
            mtd_info.is_water = True
        else:
            print(f"# ERROR: Shader name '{mtd_name}' could not be parsed for its textures.")

        if cls.MTD_M_RE.match(mtd_name):
            for texture_type, _ in mtd_info.texture_types:
                mtd_info.texture_types[texture_type + "_2"] = 2
            lightmap_uv_index = 3
        else:
            lightmap_uv_index = 2

        if cls.MTD_L_RE.match(mtd_name):
            mtd_info.texture_types["g_Lightmap"] = lightmap_uv_index

        for prefix, first_uv_index in cls.MTD_FOLIAGE_PREFIXES.items():
            if mtd_name.startswith(prefix):
                mtd_info.extra_uv_maps = (2, first_uv_index)
                break  # can't match more than one

        mtd_info.alpha = "_Alp" in mtd_name
        mtd_info.edge = "_Edge" in mtd_name
        mtd_info.spec = "_Spec" in mtd_name
        mtd_info.detb = "_DetB" in mtd_name

        if "g_Bumpmap" in mtd_info.texture_types:
            # Add useless 'g_DetailBumpmap' for completion. TODO: Some shaders, even with 'g_Bumpmap', do not have this.
            mtd_info.texture_types["g_DetailBumpmap"] = 1  # always

        return mtd_info

    @property
    def has_two_slots(self):
        return any(texture_type.endswith("_2") for texture_type, _ in self.texture_types)

    @property
    def has_lightmap(self):
        return any(texture_type == "g_Lightmap" for texture_type, _ in self.texture_types)

    @property
    def has_detail_bumpmap(self):
        return "g_DetailBumpmap" in self.texture_types

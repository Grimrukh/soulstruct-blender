from __future__ import annotations

__all__ = ["SoulstructCutsceneAnimation"]

import math
import typing as tp

import bpy
import numpy as np

from soulstruct.base.animations.sibcam import CameraFrameTransform
from soulstruct.havok.fromsoft.darksouls1r.remobnd import RemoPartAnimationFrame

from ..animation.types import SoulstructAnimation
from ..animation.utilities import *
from ..exceptions import SoulstructTypeError
from ..types import ArmatureObject, CameraObject, EmptyObject
from ..utilities import to_blender


class SoulstructCutsceneAnimation:
	"""Wrapper around a single shared cutscene Action with per-ID slots/channelbags.

	Blender 5.1 no longer exposes a flat `Action.fcurves` API for layered Actions. Instead, every animated ID
	(Object, Camera data, etc.) gets its own `ActionSlot`, whose animation data lives in a `channelbag` on the
	Action's keyframe strip.
	"""

	FAST = {"FAST"}

	action: bpy.types.Action

	def __init__(self, action: bpy.types.Action):
		if not isinstance(action, bpy.types.Action):
			raise SoulstructTypeError(
				f"Cutscene animation must be initialized with a Blender Action, not {type(action)}."
			)
		self.action = action

	@classmethod
	def new(cls, action_name: str) -> SoulstructCutsceneAnimation:
		action = bpy.data.actions.new(name=action_name)
		action.use_fake_user = True
		get_or_create_action_strip(action)
		return cls(action)

	@property
	def name(self) -> str:
		return self.action.name

	@name.setter
	def name(self, value: str):
		self.action.name = value

	@property
	def strip(self) -> bpy.types.ActionKeyframeStrip:
		return get_or_create_action_strip(self.action)

	@staticmethod
	def _get_slot_id_type(animated_id: bpy.types.ID) -> str:
		"""Only Objects (including Armatures) and Cameras can be animated by cutscenes."""
		if isinstance(animated_id, bpy.types.Object):
			return "OBJECT"
		if isinstance(animated_id, bpy.types.Camera):
			return "CAMERA"
		raise TypeError(f"Unsupported cutscene Action slot ID type: {type(animated_id)}")

	def bind(
		self,
		animated_id: bpy.types.ID,
		slot_name: str = "",
	) -> tuple[bpy.types.ActionSlot, bpy.types.ActionChannelbag]:
		"""Bind our `Action` to `animated_id` and find/create the appropriate slot."""
		anim_data = animated_id.animation_data_create()
		anim_data.action = self.action
		# After assigning the Action, we can find the same-named slot.
		for slot in anim_data.action_suitable_slots:
			if slot.name_display == animated_id.name:
				anim_data.action_slot = slot
				break
		else:
			# Create action slot.
			anim_data.action_slot = self.action.slots.new(
				id_type=self._get_slot_id_type(animated_id),
				name=animated_id.name,
			)

		channelbag = self.strip.channelbag(anim_data.action_slot, ensure=True)
		return anim_data.action_slot, channelbag

	@staticmethod
	def _normalize_keyframe_t(keyframe_t: float) -> float:
		return round(float(keyframe_t), 6)

	@classmethod
	def _set_keyframe_interpolation(
		cls,
		channelbag: bpy.types.ActionChannelbag,
		constant_keyframe_t: tp.Iterable[float] = (),
	):
		constant_keyframe_t = {cls._normalize_keyframe_t(t) for t in constant_keyframe_t}
		for fcurve in channelbag.fcurves:
			for keyframe in fcurve.keyframe_points:
				if cls._normalize_keyframe_t(keyframe.co.x) in constant_keyframe_t:
					keyframe.interpolation = "CONSTANT"
				else:
					keyframe.interpolation = "LINEAR"
			fcurve.update()

	@staticmethod
	def _add_samples(
		channelbag: bpy.types.ActionChannelbag,
		data_path: str,
		samples: np.ndarray,
	):
		"""Add `t,value...` samples to a channelbag path using batched `foreach_set()` writes."""
		if samples.ndim != 2 or samples.shape[1] < 2:
			raise ValueError(
				f"Cutscene sample array must be 2D with at least 2 columns (`keyframe_t` plus values), not: "
				f"{samples.shape}"
			)
		if samples.shape[0] == 0:
			return

		for array_index in range(samples.shape[1] - 1):
			fcurve = channelbag.fcurves.new(data_path=data_path, index=array_index)
			data = samples[:, [0, array_index + 1]]
			fcurve.keyframe_points.add(count=data.shape[0])
			fcurve.keyframe_points.foreach_set("co", data.ravel().tolist())

	def add_camera_cuts(
		self,
		camera: CameraObject,
		camera_transforms: list[list[CameraFrameTransform]],
		camera_fov_keyframes: list[list[tuple[float, float]]],
		to_60_fps: bool,
	):
		camera.rotation_mode = "XYZ"
		camera_data = camera.data

		_, object_channelbag = self.bind(camera)  # OBJECT
		_, data_channelbag = self.bind(camera_data)  # CAMERA

		bl_frames_per_game_frame = 2.0 if to_60_fps else 1.0

		location_rows = []
		rotation_rows = []
		final_frame_t = []

		cutscene_frame_index = 0
		for cut_camera_transforms in camera_transforms:
			for cut_frame_index, camera_transform in enumerate(cut_camera_transforms):
				bl_frame_index = cutscene_frame_index * bl_frames_per_game_frame
				bl_translate = to_blender(camera_transform.position)
				bl_euler = to_blender(camera_transform.rotation)
				location_rows.append([bl_frame_index, bl_translate.x, bl_translate.y, bl_translate.z])
				rotation_rows.append([bl_frame_index, bl_euler.x, bl_euler.y, bl_euler.z])
				if cut_frame_index == len(cut_camera_transforms) - 1:
					final_frame_t.append(bl_frame_index)
				cutscene_frame_index += 1

		location_samples = np.array(location_rows, dtype=np.float64) if location_rows else np.empty((0, 4))
		rotation_samples = np.array(rotation_rows, dtype=np.float64) if rotation_rows else np.empty((0, 4))
		self._add_samples(object_channelbag, "location", location_samples)
		self._add_samples(object_channelbag, "rotation_euler", rotation_samples)
		self._set_keyframe_interpolation(object_channelbag, final_frame_t)

		sensor_width = camera_data.sensor_width
		cut_fov_t_offset = 0
		lens_rows = []
		lens_final_t = []
		for cut_fov_keyframes, cut_camera_transforms in zip(camera_fov_keyframes, camera_transforms, strict=True):
			last_bl_t = None
			for t, fov in cut_fov_keyframes:
				lens = sensor_width / (2 * math.tan(fov / 2.0))
				bl_t = (cut_fov_t_offset + t) * bl_frames_per_game_frame
				lens_rows.append([bl_t, lens])
				last_bl_t = bl_t
			if last_bl_t is not None:
				lens_final_t.append(last_bl_t)
			cut_fov_t_offset += len(cut_camera_transforms)

		lens_samples = np.array(lens_rows, dtype=np.float64) if lens_rows else np.empty((0, 2))
		self._add_samples(data_channelbag, "lens", lens_samples)
		self._set_keyframe_interpolation(data_channelbag, lens_final_t)

	def add_cutscene_cuts(
		self,
		context: bpy.types.Context,
		armature_or_dummy: EmptyObject | ArmatureObject,
		arma_cuts: list[list[RemoPartAnimationFrame] | int],
		is_root_motion_only=False,
	):
		"""Bind cutscene animation data for one Armature or Dummy into this shared Action."""
		armature_or_dummy.rotation_mode = "XYZ"
		_, channelbag = self.bind(armature_or_dummy)

		to_60_fps = context.scene.cutscene_import_settings.to_60_fps
		bl_frames_per_game_frame = 2.0 if to_60_fps else 1.0

		cut_end_keyframe_t = []
		frame_count = 0
		for arma_frames in arma_cuts:
			frame_count += arma_frames if isinstance(arma_frames, int) else len(arma_frames)
			if frame_count > 0:
				cut_end_keyframe_t.append(bl_frames_per_game_frame * (frame_count - 1))

		if not is_root_motion_only:
			if armature_or_dummy.type != "ARMATURE":
				raise ValueError(
					"Cutscene animation can only be applied to an Empty (Dummy) with `is_root_motion_only=True`."
				)
			armature_or_dummy: ArmatureObject
			arma_local_inv_matrices = SoulstructAnimation.get_armature_local_inv_matrices(armature_or_dummy)
		else:
			arma_local_inv_matrices = {}

		bone_basis_sample_arrays = {}  # type: dict[str, list[np.ndarray]]
		root_motion_rows = []  # type: list[list[float]]

		global_keyframe_t = 0.0
		for arma_cut_frames in arma_cuts:
			if isinstance(arma_cut_frames, int):
				global_keyframe_t += arma_cut_frames * bl_frames_per_game_frame
				continue

			bone_arma_frames = [frame.bone_transforms for frame in arma_cut_frames]
			if not is_root_motion_only and any(bone_arma_frames):
				cut_bone_basis_samples = SoulstructAnimation.get_bone_basis_samples(
					armature_or_dummy,
					bone_arma_frames,
					arma_local_inv_matrices,
					bl_frames_per_game_frame,
				)
				for bone_name, basis_samples in cut_bone_basis_samples.items():
					basis_samples[:, 0] += global_keyframe_t
					bone_basis_sample_arrays.setdefault(bone_name, []).append(basis_samples)

			for frame in arma_cut_frames:
				rm_translate = to_blender(frame.root_motion.translation)
				rm_rotate_z = -frame.root_motion.rotation.to_euler_angles_rad(order="xzy").y
				root_motion_rows.append([global_keyframe_t, rm_translate.x, rm_translate.y, rm_translate.z, rm_rotate_z])
				global_keyframe_t += bl_frames_per_game_frame

		bone_basis_samples = (
			{
				bone_name: np.concatenate(basis_sample_arrays)
				for bone_name, basis_sample_arrays in bone_basis_sample_arrays.items()
			}
			if bone_basis_sample_arrays else {}
		)

		root_motion = np.array(root_motion_rows, dtype=np.float64) if root_motion_rows else np.empty((0, 5))

		if not bone_basis_samples and root_motion.shape[0] == 0:
			return

		SoulstructAnimation._add_keyframes_batch(
			channelbag,
			bone_basis_samples,
			root_motion=root_motion,
			root_motion_bone_name="",
		)
		self._set_keyframe_interpolation(channelbag, cut_end_keyframe_t)

	def set_scene_frame_range(self, context: bpy.types.Context, reset_current_frame=True):
		"""Set Blender scene frame range to match this cutscene Action."""
		context.scene.frame_start = int(self.action.frame_range[0])
		context.scene.frame_end = int(self.action.frame_range[1])
		if reset_current_frame:
			context.scene.frame_set(context.scene.frame_start)

from __future__ import annotations

import time
import traceback
import typing as tp

import numpy as np

import bpy
from mathutils import Matrix, Quaternion as BlenderQuaternion

from soulstruct.dcx import DCXType
from soulstruct.games import *
from soulstruct_havok.fromsoft.base import BaseSkeletonHKX, BaseAnimationHKX
from soulstruct_havok.fromsoft.darksouls1r.remobnd import *
from soulstruct_havok.fromsoft.demonssouls import AnimationHKX as DES_AnimationHKX, SkeletonHKX as DES_SkeletonHKX
from soulstruct_havok.utilities.maths import TRSTransform

from io_soulstruct.exceptions import *
from io_soulstruct.utilities import *
from .utilities import *


class GameAnimationInfo(tp.NamedTuple):
    # TODO: Probably want an `ANIBND` class in Soulstruct that is simpler (or extended by) the Soulstruct Havok one.
    relative_binder_path: str  # with `model_name` format argument
    stem_template: str
    hkx_entry_path: str  # with `model_name` and `animation_stem` format arguments
    dcx_type: DCXType


class SoulstructAnimation:

    GAME_ANIMATION_INFO_CHR = {
        DEMONS_SOULS: GameAnimationInfo(
            relative_binder_path="chr/{model_name}/{model_name}.anibnd",  # additional nested folder
            stem_template="##_####",
            hkx_entry_path="N:\\DemonsSoul\\data\\Model\\chr\\{model_name}\\hkx\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        DARK_SOULS_PTDE: GameAnimationInfo(
            relative_binder_path="chr/{model_name}.anibnd",
            stem_template="##_####",
            hkx_entry_path="N:\\FRPG\\data\\Model\\chr\\{model_name}\\hkxwin32\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        DARK_SOULS_DSR: GameAnimationInfo(
            relative_binder_path="chr/{model_name}.anibnd",
            stem_template="##_####",
            hkx_entry_path="N:\\FRPG\\data\\Model\\chr\\{model_name}\\hkxx64\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        BLOODBORNE: GameAnimationInfo(
            relative_binder_path="chr/{model_name}.anibnd",
            stem_template="###_######",
            hkx_entry_path="N:\\SPRJ\\data\\INTERROOT_ps4\\chr\\{model_name}\\hkx\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        ELDEN_RING: GameAnimationInfo(
            relative_binder_path="chr/{model_name}.anibnd",
            stem_template="###_######",
            hkx_entry_path=(  # note new variable `div_id` for DivXX ANIBNDs, which should end in '_' if non-empty
                "N:\\GR\\data\\INTERROOT_win64\\chr\\{model_name}\\hkx_{div_id}compendium\\{animation_stem}.hkx"
            ),
            dcx_type=DCXType.Null,
        )
    }

    GAME_ANIMATION_INFO_OBJ = {
        DEMONS_SOULS: GameAnimationInfo(
            relative_binder_path="obj/{model_name}.objbnd",  # no additional nested folder, unlike `chr`
            stem_template="##_####",
            hkx_entry_path="N:\\DemonsSoul\\data\\Model\\obj\\{model_name}\\hkx\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        DARK_SOULS_PTDE: GameAnimationInfo(
            relative_binder_path="obj/{model_name}.objbnd",
            stem_template="##_####",
            hkx_entry_path="N:\\FRPG\\data\\Model\\obj\\{model_name}\\hkxwin32\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        DARK_SOULS_DSR: GameAnimationInfo(
            relative_binder_path="obj/{model_name}.objbnd",
            stem_template="##_####",
            hkx_entry_path="N:\\FRPG\\data\\Model\\obj\\{model_name}\\hkxx64\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        BLOODBORNE: GameAnimationInfo(
            relative_binder_path="obj/{model_name}.objbnd",
            stem_template="###_######",
            hkx_entry_path="N:\\SPRJ\\data\\INTERROOT_ps4\\obj\\{model_name}\\hkx\\{animation_stem}.hkx",
            dcx_type=DCXType.Null,
        ),
        # TODO: Could just put Elden Ring Asset config here.
    }

    FAST = {"FAST"}

    action: bpy.types.Action

    def __init__(self, action: bpy.types.Action):
        if not isinstance(action, bpy.types.Action):
            raise SoulstructTypeError(f"Animation must be initialized with a Blender Action, not {type(action)}.")
        self.action = action

    @property
    def name(self):
        return self.action.name

    @name.setter
    def name(self, value: str):
        self.action.name = value

    @property
    def game_name(self) -> str:
        """We remove dupe suffix, then take name before any pipe, space, or period."""
        name = remove_dupe_suffix(self.action.name)
        for char in "| .":
            name = name.split(char)[0]
        return name.strip()

    @property
    def model_stem(self):
        """Try to extract the model stem from the action name.

        Action name should be in the format `{model_name}}|{anim_name}` and may have a Blender dupe suffix. If there is
        no pipe in the name, we return an empty string.

        Example:
            'c1234|a00_0000.001' -> 'c1234'
        """
        if "|" not in self.action.name:
            return ""
        return self.action.name.split("|")[0]

    @property
    def animation_stem(self):
        """Try to extract the animation stem from the action name.

        Action name should be in the format `{model_name}}|{anim_name}` and may have a Blender dupe suffix. If there is
        no pipe in the name, we return the whole thing.

        Example:
            'c1234|a00_0000.001' -> 'a00_0000'
        """
        if "|" not in self.action.name:
            return self.action.name
        return self.action.name.split("|")[-1].split(".")[0]

    @property
    def animation_id(self) -> int:
        """Try to parse animation stem as an ID.

        Example:
            'c1234|a12_0500.001' -> 120500
        """
        try:
            return int(self.animation_stem.removeprefix("a"))
        except ValueError:
            raise ValueError(f"Could not parse animation ID from Action name '{self.name}'.")

    @classmethod
    def from_armature_animation_data(cls, armature: bpy.types.ArmatureObject) -> SoulstructAnimation:
        """Load from current animation data of given `armature`."""
        if not armature.animation_data:
            raise ValueError(f"Armature '{armature.name}' has no animation data.")
        if not armature.animation_data.action:
            raise ValueError(f"Armature '{armature.name}' has no animation data Action.")
        return cls(armature.animation_data.action)

    # region Import

    @classmethod
    def new_from_hkx_animation(
        cls,
        operator: LoggingOperator,
        context: Context,
        animation_hkx: ANIMATION_TYPING,
        skeleton_hkx: SKELETON_TYPING,
        name: str,
        armature_obj: bpy.types.ArmatureObject,
        model_name: str,
        root_motion_bone_name="",
    ) -> SoulstructAnimation:
        """Create a new wrapped Blender Action from the given HKX animation data.

        If `root_motion_bone_name` is given, the HKX animation's root motion will be applied to that bone instead of the
        object's location and Z-axis rotation. This allows MSB Parts to be animated 'in place', with root motion being
        previewed by the root motion bone instead of the object itself. (Note that Cutscene animations do NOT use this,
        as their root
        """
        operator.info(f"Importing HKX animation to Armature '{armature_obj.name}': '{name}'")

        # We cannot rely on track annotations for bone names in all games (e.g. Demon's Souls, Elden Ring).
        # In Elden Ring, some HKX skeletons also animate 'Twist' bones that are not actually present in the FLVER. We
        # handle and warn about this cases, rather than throwing.
        hk_bone_names = [b.name for b in skeleton_hkx.skeleton.bones]
        track_bone_indices = animation_hkx.animation_container.hkx_binding.transformTrackToBoneIndices
        track_bone_names = [hk_bone_names[i] for i in track_bone_indices]
        bl_bone_names = [b.name for b in armature_obj.data.bones]

        if not animation_hkx.animation_container.is_interleaved:
            p = time.perf_counter()
            interleaved_animation_hkx = animation_hkx.to_interleaved_hkx()
            operator.debug(f"Converted animation to interleaved in {time.perf_counter() - p:.3f} s.")
        else:
            # Already interleaved (fine for import).
            interleaved_animation_hkx = animation_hkx
            operator.debug(f"Imported animation was already interleaved (uncompressed).")

        p = time.perf_counter()
        arma_frames = get_armature_frames(interleaved_animation_hkx, skeleton_hkx)
        root_motion = get_root_motion(interleaved_animation_hkx)
        operator.debug(f"Constructed armature animation frames in {time.perf_counter() - p:.3f} s.")

        # Note that it's common for the HKX animation to not animate all bones in the FLVER, but we do warn if there
        # are any bones in the HKX animation that are not in the FLVER.
        for bone_name in track_bone_names:
            if bone_name not in bl_bone_names:
                operator.warning(
                    f"Animated bone name '{bone_name}' is missing from FLVER Armature. Animation data for this absent "
                    f"bone will be discarded."
                )
                # Remove bone name from every Armature frame.
                for frame in arma_frames:
                    frame.pop(bone_name)

        # Import single animation HKX.
        p = time.perf_counter()
        try:
            bl_animation = cls.new_from_transform_frames(
                context,
                action_name=f"{model_name}|{name}",
                armature_obj=armature_obj,
                arma_frames=arma_frames,
                root_motion=root_motion,
            )
        except Exception as ex:
            traceback.print_exc()
            raise AnimationImportError(f"Cannot import HKX animation: {name}. Error: {ex}")
        operator.debug(f"Created animation Blender action in {time.perf_counter() - p:.3f} s.")

        return bl_animation

    @classmethod
    def new_from_transform_frames(
        cls,
        context: Context,
        action_name: str,
        armature_obj: bpy.types.ArmatureObject,
        arma_frames: list[dict[str, TRSTransform]] | None,
        root_motion: np.ndarray | None = None,  # shape (n_frames, 4) or None
        root_motion_bone_name="",
    ) -> SoulstructAnimation:
        """Import single animation HKX.

        `arma_frames` is a list of dictionaries mapping bone names to `TRSTransform` objects that represent transforms
        in armature space. It is necessary to use the computed armature space transforms, rather than the raw local
        HKX frame transforms given in the parent bone's space, because the FLVER skeleton that we are animating here
        may NOT have the same hierarchy as the HKX skeleton used by the animation.

        Once we have converted the 'HKX local' bone transforms to 'armature space' transforms (passed in here), we then
        convert those to 'FLVER local' 'bone basis' transforms, i.e. the `pose_bone.matrix_basis` property of PoseBones.
        This is the same transform actually shown in the PoseBone Properties GUI (rather than the `matrix` property,
        which is the final transform of the bone in armature space, but is 'output only' and cannot be animated/driven).

        CALCULATING THE BASIS MATRIX:

            The `matrix_basis` is aptly named because it is the rightmost matrix in the Matrix multiplication sequence
            that determines its final armature-space `matrix`:

                pose_bone.matrix =
                    parent_pose_bone.matrix
                    @ parent_bone.matrix_local.inverted()  # EditBones data
                    @ bone.matrix_local  # EditBones data
                    @ pose_bone.matrix_basis

            This final `pose_bone.matrix`, of course, is then left-multiplied by `armature_object.matrix_world` to get
            the final bone position in world space (though in practice, the bones are used to deform the local mesh,
            which is then transformed from object to world space).

            The two matrices in the middle, `parent_bone.matrix_local.inverted()` and `bone.matrix_local`, are
            the least intuitive to understand here, but it's actually straightforward when we remember that these
            `Bone.matrix_local` matrices are actually *already in armature space*, which is slightly non-obvious from
            the name. That means that the matrix product `parent_bone.matrix_local.inverted() @ bone.matrix_local` is
            just a way of getting the 'rest pose' of `bone` in its parent space (originally set using transient
            `EditBone` instances), which is the correct matrix to use for left-multipling the `matrix_basis` to get the
            parent-relative pose matrix, which we then left-multiply by the parent's similarly-computed pose matrix to
            get the armature-space pose matrix (forward kinematics).
        """

        # TODO: Assumes source is 30 FPS, which is probably always true with FromSoft?
        to_60_fps = context.scene.animation_import_settings.to_60_fps
        bl_frames_per_game_frame = 2.0 if to_60_fps else 1.0

        if root_motion is not None:
            if root_motion.ndim != 2:
                raise ValueError(f"Root motion array must have 2 dimensions, not {root_motion.ndim}.")
            if root_motion.shape[1] != 4:
                raise ValueError(f"Root motion array must have 4 columns (x, y, z, r), not {root_motion.shape[1]}.")

            # Attach `keyframe_t` frame time column to start, scaled appropriately.
            keyframe_t_column = np.arange(root_motion.shape[0], dtype=np.float32) * bl_frames_per_game_frame
            if root_motion.shape[0] == 0:
                # Empty array.  Weird, but we'll leave default scaling and put any single root motion keyframe at 0.
                pass
            elif arma_frames and len(root_motion) != len(arma_frames):
                # Root motion is at a lesser (or possibly greater?) sample rate than bone animation. For example, if
                # only two root motion samples are given, they will be scaled to match the first and last frame of
                # `arma_frames`. This scaling stacks with the intrinsic `bone_frame_scaling` (e.g. 2 for 60 FPS).
                keyframe_t_column *= len(arma_frames) / (root_motion.shape[0] - 1)
            root_motion = np.hstack([keyframe_t_column[:, None], root_motion])

        action = None  # type: bpy.types.Action | None
        original_location = armature_obj.location.copy()  # TODO: not necessary with batch method?
        try:
            armature_obj.animation_data_create()
            armature_obj.animation_data.action = action = bpy.data.actions.new(name=action_name)

            if arma_frames:
                bone_basis_samples = cls.get_bone_basis_samples(
                    armature_obj,
                    arma_frames,
                    cls.get_armature_local_inv_matrices(armature_obj),
                    bl_frames_per_game_frame,
                )
            else:
                bone_basis_samples = {}

            cls._add_keyframes_batch(
                action,
                bone_basis_samples,
                root_motion,
                root_motion_bone_name,
            )

        except Exception:
            if action:
                bpy.data.actions.remove(action)
            armature_obj.location = original_location  # reset location (i.e. erase last root motion)
            raise

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # Update all F-curves and make them cycle.
        for fcurve in action.fcurves:
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()
        # Update Blender timeline start/stop times.
        context.scene.frame_start = int(action.frame_range[0])
        context.scene.frame_end = int(action.frame_range[1])
        context.scene.frame_set(context.scene.frame_start)

        return cls(action)

    @classmethod
    def new_from_cutscene_cuts(
        cls,
        context: Context,
        action_name: str,
        armature_or_dummy: bpy.types.EmptyObject | bpy.types.ArmatureObject,
        arma_cuts: list[list[RemoPartAnimationFrame] | int],
        is_root_motion_only=False,
    ) -> SoulstructAnimation:
        """Create a Blender Action that combines all the given cuts in `all_cut_arma_frames`, read from RemoBND."""
        to_60_fps = context.scene.cutscene_import_settings.to_60_fps
        bl_frames_per_game_frame = 2.0 if to_60_fps else 1.0

        action = None  # type: bpy.types.Action | None
        original_location = armature_or_dummy.location.copy()  # TODO: not necessary with batch method?

        # Record indices of last frame in each cut to set CONSTANT interpolation afterward.
        # Note that these are keyframe `co.x` values, not just indices (but compared as integers).
        cut_end_keyframe_x = []  # type: list[float]
        frame_count = 0
        for arma_frames in arma_cuts:
            if isinstance(arma_frames, int):
                frame_count += arma_frames
            else:
                frame_count += len(arma_frames)
            cut_end_keyframe_x.append(int(bl_frames_per_game_frame * (frame_count - 1)))

        try:
            armature_or_dummy.animation_data_create()
            armature_or_dummy.animation_data.action = action = bpy.data.actions.new(name=action_name)
            if not is_root_motion_only:
                if armature_or_dummy.type != "ARMATURE":
                    raise ValueError(
                        "Cutscene animation can only be applied to an Empty (Dummy) with `is_root_motion_only=True`."
                    )
                armature_or_dummy: bpy.types.ArmatureObject
                arma_local_inv_matrices = cls.get_armature_local_inv_matrices(armature_or_dummy)  # used by every frame
            else:
                arma_local_inv_matrices = {}  # unused

            # We concatenate all bone basis samples for each cut. Only actual animated bones appear in it.
            # The cut sub-arrays that appear in here
            bone_basis_sample_arrays = {}  # type: dict[str, list[np.ndarray]]
            root_motion_rows = []  # type: list[list[float]]

            global_keyframe_t = 0.0
            for arma_cut_frames in arma_cuts:
                if isinstance(arma_cut_frames, int):
                    # Skip this many (game) frames. (Last cut will still put CONSTANT interpolation at the end.)
                    global_keyframe_t += arma_cut_frames * bl_frames_per_game_frame
                    continue

                bone_arma_frames = [frame.bone_transforms for frame in arma_cut_frames]
                # Get bone basis samples if ANY frame has bone animation data.
                if not is_root_motion_only and any(bone_arma_frames):
                    cut_bone_basis_samples = cls.get_bone_basis_samples(
                        armature_or_dummy,
                        [frame.bone_transforms for frame in arma_cut_frames],
                        arma_local_inv_matrices,
                        bl_frames_per_game_frame,
                    )
                    for bone_name, basis_samples in cut_bone_basis_samples.items():
                        # Add global keyframe time to first column.
                        basis_samples[:, 0] += global_keyframe_t
                        if bone_name not in bone_basis_sample_arrays:
                            bone_basis_sample_arrays[bone_name] = []
                        bone_basis_sample_arrays[bone_name].append(basis_samples)

                # Root motion. Note that root motion is ALWAYS present in cutscene animations, even if all identity.
                # We increment `global_keyframe_t` within here.
                for frame in arma_cut_frames:
                    # TODO: Theoretically, cutscene root motion supports full rotation. Just doing Z (-Y) for now.
                    rm_translate = GAME_TO_BL_VECTOR(frame.root_motion.translation)
                    rm_rotate_z = -frame.root_motion.rotation.to_euler_angles(radians=True, order="xzy").y
                    root_motion_rows.append(
                        [global_keyframe_t, rm_translate.x, rm_translate.y, rm_translate.z, rm_rotate_z]
                    )
                    global_keyframe_t += bl_frames_per_game_frame

            if bone_basis_sample_arrays:
                bone_basis_samples = {
                    bone_name: np.concatenate(basis_sample_arrays)
                    for bone_name, basis_sample_arrays in bone_basis_sample_arrays.items()
                }
            else:
                bone_basis_samples = {}

            root_motion = np.array(root_motion_rows)

            cls._add_keyframes_batch(
                action,
                bone_basis_samples,
                root_motion=root_motion,
                root_motion_bone_name="",  # root motion drives Armature transform directly
            )
        except Exception:
            if action:
                bpy.data.actions.remove(action)
            armature_or_dummy.location = original_location  # reset location (i.e. erase last root motion)
            raise

        # Set constant interpolation at the ends of cuts.
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                if int(keyframe.co.x) in cut_end_keyframe_x:
                    keyframe.interpolation = "CONSTANT"

        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # No CYCLES modifier.
        # Update Blender timeline start/stop times.
        # TODO: Don't bother doing this here. The caller should set the range to the maximal cutscene range after.
        context.scene.frame_start = int(action.frame_range[0])
        context.scene.frame_end = int(action.frame_range[1])
        context.scene.frame_set(context.scene.frame_start)

        return cls(action)

    @staticmethod
    def get_armature_local_inv_matrices(armature: bpy.types.ArmatureObject) -> dict[str, Matrix]:
        """Return a dictionary mapping Blender bone names to their inverted `matrix_local` transforms."""
        return {
            bone.name: bone.matrix_local.inverted()
            for bone in armature.data.bones
        }

    @staticmethod
    def get_bone_basis_samples(
        armature: bpy.types.ArmatureObject,
        arma_frames: list[dict[str, TRSTransform]],
        arma_local_inv_matrices: dict[str, Matrix],
        bl_frames_per_game_frame: float,
    ) -> dict[str, np.ndarray]:
        """Convert a list of Armature-space frames, where each frame is a `dict[bone_name: str, TRSTransform]`, to an
        an outer dictionary that maps bone names to an array of 11 bone basis-space keyframe values:
            t, location XYZ, rotation quaternion WXYZ, scale XYZ
        """

        # Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        last_frame_rotations = {}  # type: dict[str, BlenderQuaternion]
        frame_count = len(arma_frames)

        bone_basis_samples = {
            bone_name: np.empty((frame_count, 11))
            for bone_name in arma_frames[0].keys()
        }  # type: dict[str, np.ndarray]

        keyframe_t = 0.0
        for frame_i, frame in enumerate(arma_frames):
            # `frame_i` is used to index array rows (created above).

            # Get Blender armature space 4x4 transform `Matrix` for each bone.
            bl_arma_matrices = {
                bone_name: GAME_TRS_TO_BL_MATRIX(transform) for bone_name, transform in frame.items()
            }
            cached_arma_inv_matrices = {}  # cached for frame as needed

            for bone_name, bl_arma_matrix in bl_arma_matrices.items():
                basis_samples = bone_basis_samples[bone_name]

                bl_edit_bone = armature.data.bones[bone_name]

                if (
                    bl_edit_bone.parent is not None
                    and bl_edit_bone.parent.name not in cached_arma_inv_matrices
                ):
                    # Cache parent's inverted armature matrix (may be needed by other sibling bones this frame).
                    # Note that as FLVER and HKX skeleton hierarchies may be different, the FLVER (Blender Armature)
                    # parent bone may not even be animated, in which case we just use an identity matrix.
                    parent_name = bl_edit_bone.parent.name
                    if parent_name in bl_arma_matrices:
                        cached_arma_inv_matrices[parent_name] = bl_arma_matrices[parent_name].inverted()
                    else:
                        cached_arma_inv_matrices[parent_name] = Matrix.Identity(4)

                bl_basis_matrix = get_basis_matrix(
                    armature,
                    bone_name,
                    bl_arma_matrix,
                    cached_arma_inv_matrices,
                    arma_local_inv_matrices,
                )

                t, r, s = bl_basis_matrix.decompose()

                if bone_name in last_frame_rotations:
                    if last_frame_rotations[bone_name].dot(r) < 0.0:
                        r.negate()  # negate quaternion to avoid discontinuity (reverse direction of rotation)

                basis_samples[frame_i] = [keyframe_t, *t, *r, *s]
                last_frame_rotations[bone_name] = r

            keyframe_t += bl_frames_per_game_frame

        return bone_basis_samples

    @staticmethod
    def _add_keyframes_batch(
        action: bpy.types.Action,
        bone_basis_samples: dict[str, np.ndarray],
        root_motion: np.ndarray | None,
        root_motion_bone_name: str = "",
    ):
        """Faster method of adding all bone and (optional) root keyframe data.

        Constructs `FCurves` with known length and uses `foreach_set` to batch-set all the `.co` attributes of the
        curve keyframe points at once.

        `bone_basis_samples` should map bone names to a `frame_count x 11` array of data, where the 11 columns are:
            keyframe_t, location XYZ, quaternion WXYZ, scale XYZ
        Here, the `t` column should already be scaled as desired for the frame rate conversion, e.g. (0, 2, 4, ...)
        when converting 30 to 60 FPS.

        If `root_motion_bone_name` is given (non-empty), root motion will be applied to the bone with that name.
        Otherwise it will be applied directly to the object's local transform (location and Z-axis rotation).
        """

        # Initialize FCurves for root motion and bones.
        if root_motion is not None:
            if root_motion.ndim != 2 or root_motion.shape[1] != 5:
                raise ValueError(
                    f"If given, root motion array must be 2D with 5 columns (`keyframe_t, x, y, z, rz`) not: "
                    f"{root_motion.shape}"
                )
            if root_motion_bone_name:
                # We animate the given bone name with root motion instead of the Armature transform.
                data_path = f"pose.bones[\"{root_motion_bone_name}\"]"
                root_fcurves = [action.fcurves.new(data_path=f"{data_path}.location", index=i) for i in range(3)]
                root_fcurves.append(action.fcurves.new(data_path=f"{data_path}.rotation_euler", index=2))  # Z
            else:
                root_fcurves = [action.fcurves.new(data_path="location", index=i) for i in range(3)]
                root_fcurves.append(action.fcurves.new(data_path="rotation_euler", index=2))  # Z
        else:
            root_fcurves = []

        # If `bone_basis_samples` is empty, no bone FCurves will be created here.
        bone_fcurves = {}
        for bone_name in bone_basis_samples.keys():
            bone_fcurves[bone_name] = []  # ten FCurves per bone
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].location", index=i)
                for i in range(3)
            ]
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].rotation_quaternion", index=i)
                for i in range(4)
            ]
            bone_fcurves[bone_name] += [
                action.fcurves.new(data_path=f"pose.bones[\"{bone_name}\"].scale", index=i)
                for i in range(3)
            ]

        # Build lists of FCurve keyframe points by initializing their size and using `foreach_set`.
        # Each keyframe point has a `.co` attribute to which we set `(t, value)` (per dimension).
        # `foreach_set` requires that we flatten the list of tuples to be assigned, a la:
        #    `[keyframe_t_0, value_0, keyframe_t_1, value_1, ...]`
        # which we do with array column indexing and `ravel()`.
        if root_fcurves:
            # NOTE: There may be less root motion samples than bone animation samples. We spread the root motion samples
            # out to match the interval covered by the bone animation frames (done by caller).
            for fcurve_i, root_fcurve in enumerate(root_fcurves):  # x, y, z, -rz (from game ry)
                data = root_motion[:, [0, fcurve_i + 1]]  # get `keyframe_t` column plus indexed dim of root motion
                root_fcurve.keyframe_points.add(count=data.shape[0])  # row count
                root_fcurve.keyframe_points.foreach_set("co", data.ravel().tolist())
                for kp in root_fcurve.keyframe_points:
                    kp.interpolation = "LINEAR"

        for bone_name, bone_transform_fcurves in bone_fcurves.items():
            basis_samples = bone_basis_samples[bone_name]
            for fcurve_i, bone_fcurve in enumerate(bone_transform_fcurves):
                bone_fcurve.keyframe_points.add(count=basis_samples.shape[0])  # row count
                data = basis_samples[:, [0, fcurve_i + 1]]  # get `keyframe_t` column plus indexed dim of bone motion
                bone_fcurve.keyframe_points.foreach_set("co", data.ravel().tolist())
                for kp in bone_fcurve.keyframe_points:
                    kp.interpolation = "LINEAR"

    # endregion
    
    # region Export

    def to_interleaved_animation_hkx(
        self,
        operator: LoggingOperator,
        context: Context,
        armature: bpy.types.ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[BaseAnimationHKX],
    ) -> ANIMATION_TYPING | BaseAnimationHKX:
        """Animation data is easier to export from Blender than import, as we can just read the bone transforms on each
        frame in Armature space directly (rather than needing to compute each basis Matrix when importing).

        We still need this action to determine the name and start/end times for the animation.

        The `skeleton_hkx` Havok type version is used to determine the returned `AnimationHKX` Havok type version.
        """
        if animation_hkx_class.get_version_string().startswith("Havok_"):
            raise NotImplementedError("Cannot export Demon's Souls animations.")

        export_settings = context.scene.animation_export_settings

        # TODO: Technically, animation export only needs a start/end frame range, since it samples location/bone pose
        #  on every single frame anyway and does NOT need to actually use the action FCurves!

        # Determine the frame range.
        # TODO: Export bool option to just read from current scene values, rather than checking action.
        if export_settings.selected_frames_only:
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
        else:
            start_frame = int(min(fcurve.range()[0] for fcurve in self.action.fcurves))
            end_frame = int(max(fcurve.range()[1] for fcurve in self.action.fcurves))

        # All frame interleaved transforms, in armature space.
        root_motion_samples = []  # type: list[tuple[float, float, float, float]]
        armature_space_frames = []  # type: list[list[TRSTransform]]

        has_root_motion = False

        # Animation track order will match Blender bone order (which should come from FLVER).
        track_bone_mapping = list(range(len(skeleton_hkx.skeleton.bones)))

        # Store last bone TRS for rotation negation.
        last_bone_trs = {bone.name: TRSTransform.identity() for bone in skeleton_hkx.skeleton.bones}

        # Slight efficiency boost.
        bl_bones_by_name = {
            bone.name: bone for bone in armature.pose.bones
        }

        # Evaluate all curves at every frame, inclusive of `end_frame`.
        for i, frame in enumerate(range(start_frame, end_frame + 1)):

            if export_settings.from_60_fps and i % 2 == 1:
                # Skip every second frame to convert 60 FPS to 30 FPS (frame 0 should generally be keyframed).
                continue

            bpy.context.scene.frame_set(frame)
            armature_space_frame = []  # type: list[TRSTransform]

            # We collect root motion vectors, as we're not sure if any root motion exists yet.
            loc = armature.location
            rot = armature.rotation_euler
            root_motion_sample = (loc[0], loc[1], loc[2], rot[2])  # XYZ and Z rotation (soon to be game Y)
            root_motion_samples.append(root_motion_sample)
            if not has_root_motion:
                if len(root_motion_samples) >= 2 and root_motion_samples[-1] != root_motion_samples[-2]:
                    # Some actual root motion has appeared.
                    has_root_motion = True

            for bone in skeleton_hkx.skeleton.bones:
                try:
                    bl_bone = bl_bones_by_name[bone.name]
                except KeyError:
                    # Ignore bone missing from FLVER Armature.
                    if i == 0:
                        # Only emit warning on first frame.
                        operator.warning(
                            f"Bone '{bone.name}' in HKX skeleton not found in Blender armature. Identity animation "
                            f"data will exported for this HKX bone for all frames."
                        )
                    # raise AnimationExportError(f"Bone '{bone.name}' in HKX skeleton not found in Blender armature.")
                    armature_space_transform = TRSTransform.identity()
                else:
                    armature_space_transform = BL_MATRIX_TO_GAME_TRS(bl_bone.matrix)
                    if i > 0:
                        # Negate rotation quaternion if dot with last rotation is negative (first frame ignored).
                        dot = np.dot(armature_space_transform.rotation.data, last_bone_trs[bone.name].rotation.data)
                        if dot < 0:
                            armature_space_transform.rotation = -armature_space_transform.rotation

                last_bone_trs[bone.name] = armature_space_transform
                armature_space_frame.append(armature_space_transform)

            armature_space_frames.append(armature_space_frame)

        if has_root_motion:
            root_motion = np.array(root_motion_samples, dtype=np.float32)
            # Swap translate Y/Z and negate rotation Z (now Y).
            root_motion = np.c_[root_motion[:, 0], root_motion[:, 2], root_motion[:, 1], -root_motion[:, 3]]
        else:
            root_motion = None

        return animation_hkx_class.from_minimal_data_interleaved(
            frame_transforms=armature_space_frames,
            track_names=[bone.name for bone in skeleton_hkx.skeleton.bones],
            transform_track_bone_indices=track_bone_mapping,
            root_motion_array=root_motion,
            original_skeleton_name=skeleton_hkx.skeleton.skeleton.name,
            frame_rate=30.0,
            skeleton_for_armature_to_local=skeleton_hkx,
        )

    def to_wavelet_animation(
        self,
        operator: LoggingOperator,
        context: Context,
        armature: bpy.types.ArmatureObject,
        skeleton_hkx: DES_SkeletonHKX,
        animation_hkx_class: type[DES_AnimationHKX],
    ) -> DES_AnimationHKX:
        """Convert to wavelet-compressed."""
        interleaved_animation = self.to_interleaved_animation_hkx(
            operator, context, armature, skeleton_hkx, animation_hkx_class
        )
        return interleaved_animation.to_wavelet_hkx()

    def to_spline_animation(
        self,
        operator: LoggingOperator,
        context: Context,
        armature: bpy.types.ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[BaseAnimationHKX],
    ) -> ANIMATION_TYPING:
        interleaved_animation = self.to_interleaved_animation_hkx(
            operator, context, armature, skeleton_hkx, animation_hkx_class
        )
        return interleaved_animation.to_spline_hkx()

    def to_game_compressed_animation(
        self,
        operator: LoggingOperator,
        context: Context,
        game: Game,
        armature: bpy.types.ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[BaseAnimationHKX],
        force_interleaved=False,
    ) -> ANIMATION_TYPING:
        """Detect appropriate wavelet or spline compression based on game."""

        if force_interleaved:
            animation_hkx = self.to_interleaved_animation_hkx(
                operator, context, armature, skeleton_hkx, animation_hkx_class
            )
        elif game is DEMONS_SOULS:
            assert isinstance(skeleton_hkx, DES_SkeletonHKX)
            assert issubclass(animation_hkx_class, DES_AnimationHKX)
            animation_hkx = self.to_wavelet_animation(operator, context, armature, skeleton_hkx, animation_hkx_class)
        else:
            # All other games use spline compression.
            animation_hkx = self.to_spline_animation(operator, context, armature, skeleton_hkx, animation_hkx_class)

        if game is DEMONS_SOULS:
            # Demon's Souls HKX files must be big-endian.
            animation_hkx.is_big_endian = True

        return animation_hkx

    # endregion

    # region Utilities

    def set_scene_frame_range(self, context: bpy.types.Context, reset_current_frame=True):
        """Set Blender scene frame range to match this animation, and set start frame as current."""
        context.scene.frame_start = int(self.action.frame_range[0])
        context.scene.frame_end = int(self.action.frame_range[1])
        if reset_current_frame:
            context.scene.frame_set(context.scene.frame_start)

    # endregion

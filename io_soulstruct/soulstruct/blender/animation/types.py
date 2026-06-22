from __future__ import annotations

import time
import traceback
import typing as tp

import numpy as np

import bpy
from mathutils import Matrix, Quaternion as BLQuaternion

from soulstruct.dcx import DCXType
from soulstruct.games import *
from soulstruct.havok.fromsoft.base import BaseSkeletonHKX, BaseAnimationHKX
from soulstruct.havok.fromsoft.demonssouls import AnimationHKX as DES_AnimationHKX, SkeletonHKX as DES_SkeletonHKX
from soulstruct.havok.utilities.maths import TRSTransform

from ..base.operators import *
from ..flver.utilities import game_bone_transform_to_bl_bone_matrix, BONE_CoB_4x4
from ..flver.models.types import BlenderFLVER, FLVERBoneDataType
from ..exceptions import *
from ..types import *
from ..utilities import *
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

    @property
    def action_slot(self) -> bpy.types.ActionSlot:
        """Return first action slot."""
        return self.action.slots[0]

    @property
    def channelbag(self) -> bpy.types.ActionChannelbag:
        """Return channelbag of first layer, strip, and action slot."""
        strip = self.action.layers[0].strips[0]
        return strip.channelbag(self.action.slots[0], ensure=True)

    @classmethod
    def from_armature_animation_data(cls, armature: ArmatureObject) -> SoulstructAnimation:
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
        animation_hkx: BaseAnimationHKX,
        skeleton_hkx: BaseSkeletonHKX,
        name: str,
        armature_obj: ArmatureObject,
        model_name: str,
        bone_data_type: FLVERBoneDataType = FLVERBoneDataType.OMITTED,
    ) -> SoulstructAnimation:
        """Create a new wrapped Blender Action from the given HKX animation data."""
        operator.info(f"Importing HKX animation to Armature '{armature_obj.name}': '{name}'")

        # We cannot rely on track annotations for bone names in all games (e.g. Demon's Souls, Elden Ring).
        # In Elden Ring, some HKX skeletons also animate 'Twist' bones that are not actually present in the FLVER. We
        # handle and warn about these cases, rather than throwing.
        hk_bone_names = [b.name for b in skeleton_hkx.skeleton.bones]
        track_bone_indices = animation_hkx.animation_container.get_track_bone_indices()
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
                bone_data_type=bone_data_type,
            )
        except Exception as ex:
            traceback.print_exc()
            raise AnimationImportError(f"Cannot import HKX animation: {name}. Error: {ex}")
        operator.info(f"Created animation Blender action in {time.perf_counter() - p:.3f} s.")

        return bl_animation

    @classmethod
    def new_from_transform_frames(
        cls,
        context: Context,
        action_name: str,
        armature_obj: ArmatureObject,
        arma_frames: list[dict[str, TRSTransform]] | None,
        root_motion: np.ndarray | None = None,  # shape (n_frames, 4) or None
        bone_data_type: FLVERBoneDataType = FLVERBoneDataType.OMITTED,
    ) -> SoulstructAnimation:
        """Import single animation HKX.

        `arma_frames` is a list of dictionaries mapping bone names to `TRSTransform` objects that represent transforms
        in game armature space. It is necessary to use the computed armature space transforms, rather than the raw local
        HKX frame transforms given in the parent bone's space, because the FLVER skeleton that we are animating here
        may NOT have the same hierarchy as the HKX skeleton used by the animation.

        TODO: This animation should apply directly to a separate HKX skeleton, which drives the FLVER skeleton via
         1:1 bone-mapping constraints.

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
            `Bone.matrix_local` matrices are *already in armature space*, which is slightly non-obvious from the name.
            That means that the matrix product `parent_bone.matrix_local.inverted() @ bone.matrix_local` is just a way
            of getting the 'rest pose' of `bone` in its parent space (originally set using transient `EditBone`
            instances), which is the correct matrix to use for left-multipling the `matrix_basis` to get the
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
            action, action_slot, channelbag = create_action_slot_channelbag(armature_obj, action_name)

            if arma_frames:

                try:
                    bone_data_type = BlenderFLVER.from_armature_or_mesh(armature_obj).bone_data_type
                except SoulstructTypeError:
                    # Assume no CoB in edit bones.
                    bone_data_type = FLVERBoneDataType.CUSTOM

                bone_basis_samples = cls.get_bone_basis_samples(
                    armature_obj,
                    arma_frames,
                    cls.get_armature_local_inv_matrices(armature_obj),
                    bl_frames_per_game_frame,
                    bone_data_type,
                )
            else:
                bone_basis_samples = {}

            add_keyframes_batch(
                channelbag,
                bone_basis_samples,
                root_motion,
            )

        except Exception:
            if action:
                bpy.data.actions.remove(action)
            armature_obj.location = original_location  # reset location (i.e. erase last root motion)
            raise

        # Action has been set.
        action: bpy.types.Action

        # Set Action and Slot on Armature object (NOT Armature data).
        armature_obj.animation_data.action = action
        armature_obj.animation_data.action_slot = action_slot
        # Ensure action is not deleted when not in use.
        action.use_fake_user = True
        # Update all F-curves and make them cycle.
        for fcurve in channelbag.fcurves:
            fcurve.modifiers.new("CYCLES")  # default settings are fine
            fcurve.update()

        animation = cls(action)
        # Update Blender timeline start/stop times.
        animation.set_scene_frame_range(context, reset_current_frame=True)
        return animation

    @staticmethod
    def get_armature_local_inv_matrices(armature: ArmatureObject) -> dict[str, Matrix]:
        """Return a dictionary mapping Blender bone names to their inverted `matrix_local` transforms.

        NOTE: We stay in our custom 'FromSoft bone space' coordinates here (X-forward), since this is intended only for
        use within bone transform calculations.
        """
        return {
            bone.name: bone.matrix_local.inverted()
            for bone in armature.data.bones
        }

    @staticmethod
    def get_bone_basis_samples(
        armature: ArmatureObject,
        arma_frames: list[dict[str, TRSTransform]],
        arma_local_inv_matrices: dict[str, Matrix],
        bl_frames_per_game_frame: float,
        bone_data_type: FLVERBoneDataType,
        assert_root_bone_names: tp.Container[str] = (),
    ) -> dict[str, np.ndarray]:
        """Convert a list of Armature-space frames, where each frame is a `dict[bone_name: str, TRSTransform]`, to an
        outer dictionary that maps bone names to an array of 11 bone basis-space keyframe values:
            t, location XYZ, rotation quaternion WXYZ, scale XYZ
        """

        # Convert armature-space frame data to Blender `(location, rotation_quaternion, scale)` tuples.
        # Note that we decompose the basis matrices so that quaternion discontinuities are handled properly.
        last_frame_rotations = {}  # type: dict[str, BLQuaternion]
        frame_count = len(arma_frames)

        bone_basis_samples = {
            bone_name: np.empty((frame_count, 11))
            for bone_name in arma_frames[0].keys()
        }  # type: dict[str, np.ndarray]

        keyframe_t = 0.0
        for frame_i, frame in enumerate(arma_frames):
            # `frame_i` is used to index array rows (created above).

            bl_arma_matrices = {}
            for bone_name, trs in frame.items():
                # bl_arma_matrix = game_trs_to_bl_matrix(trs)
                if bone_data_type == FLVERBoneDataType.EDIT:
                    # Account for EditBone change of basis.
                    # In practice, this only matters for root bones (including effective cutscene root bones)
                    # because child bones only have their local transforms extracted for the basis matrix anyway.
                    # bl_arma_matrices[bone_name] = bl_arma_matrix @ BONE_CoB_4x4  # TODO: use this probably
                    bl_arma_matrices[bone_name] = game_bone_transform_to_bl_bone_matrix(
                        trs.translation,
                        trs.rotation.to_matrix3(),
                        trs.scale,
                    )
                else:
                    # Standard conversion, no CoB in edit bones to account for.
                    bl_arma_matrices[bone_name] = game_trs_to_bl_matrix(trs)

            cached_arma_inv_matrices = {}  # cached for frame as needed

            for bone_name, bl_arma_matrix in bl_arma_matrices.items():
                basis_samples = bone_basis_samples[bone_name]

                bl_edit_bone = tp.cast(bpy.types.Bone, armature.data.bones[bone_name])

                if bl_edit_bone.parent is not None and bone_name not in assert_root_bone_names:
                    parent_bone_name = bl_edit_bone.parent.name
                    if parent_bone_name not in cached_arma_inv_matrices:
                        # Cache parent's inverted armature matrix (might be needed by other sibling bones this frame).
                        # Note that as FLVER and HKX skeleton hierarchies may be different, the FLVER (Blender Armature)
                        # parent bone may not even be animated, in which case we just use an identity matrix.
                        if parent_bone_name in bl_arma_matrices:
                            cached_arma_inv_matrices[parent_bone_name] = bl_arma_matrices[parent_bone_name].inverted()
                        else:
                            # We still want to use the rest pose of this parent, even though it doesn't appear
                            # in this animation frame. Assume animation pose is identity.
                            cached_arma_inv_matrices[parent_bone_name] = Matrix.Identity(4)
                else:
                    # Consider this bone as a root bone when calculating basis matrix.
                    parent_bone_name = ""

                bl_basis_matrix = get_basis_matrix(
                    armature,
                    bone_name,
                    parent_bone_name,
                    bl_arma_matrix,
                    cached_arma_inv_matrices,
                    arma_local_inv_matrices,
                )

                t, r, s = bl_basis_matrix.decompose()

                if bone_name in last_frame_rotations:
                    if last_frame_rotations[bone_name].dot(r) < 0.0:
                        r.negate()  # negate quaternion to avoid discontinuity (reverse direction of rotation)
                elif r.w < 0.0:
                    # Frame 0: canonicalize sign (W >= 0) so round-trips always start from the same hemisphere.
                    r.negate()

                basis_samples[frame_i] = [keyframe_t, *t, *r, *s]
                last_frame_rotations[bone_name] = r

            keyframe_t += bl_frames_per_game_frame

        return bone_basis_samples

    # endregion
    
    # region Export

    def to_interleaved_animation_hkx[AnimationHKXType: BaseAnimationHKX](
        self,
        operator: LoggingOperator,
        context: Context,
        armature: ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[AnimationHKXType],
    ) -> AnimationHKXType:
        """Animation data is easier to export from Blender than import, as we can just read the bone transforms on each
        frame in Armature space directly (rather than needing to compute each basis Matrix when importing).

        We still need this action to determine the name and start/end times for the animation.

        The `skeleton_hkx` Havok type version is used to determine the returned `AnimationHKX` Havok type version.
        """
        if animation_hkx_class.get_version_string().startswith("Havok_"):
            raise NotImplementedError("Cannot export Demon's Souls animations.")

        export_settings = context.scene.animation_export_settings

        # We need the bone data type to determine if we need to account for EditBone CoB.
        bone_data_type = get_armature_bone_data_type(armature)

        # TODO: Technically, animation export only needs a start/end frame range, since it samples location/bone pose
        #  on every single frame anyway and does NOT need to actually use the action FCurves!

        # Determine the frame range.
        # TODO: Export bool option to just read from current scene values, rather than checking action.
        if export_settings.selected_frames_only:
            start_frame = context.scene.frame_start
            end_frame = context.scene.frame_end
        else:
            fcurves = self.channelbag.fcurves
            start_frame = int(min(fcurve.range()[0] for fcurve in fcurves))
            end_frame = int(max(fcurve.range()[1] for fcurve in fcurves))

        # All frame interleaved transforms, in armature space.
        root_motion_samples = []  # type: list[tuple[float, float, float, float]]
        armature_space_frames = []  # type: list[list[TRSTransform]]

        # Pre-detect root motion from F-curve presence rather than sampling.  This correctly
        # preserves zero-valued root motion that would be missed by comparing consecutive samples.
        _fcurve_paths = {fc.data_path for fc in self.channelbag.fcurves}
        has_root_motion = bool(_fcurve_paths & {"location", "rotation_euler"})

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

            # Collect root motion sample (only when the action has root motion F-curves).
            if has_root_motion:
                loc = armature.location
                rot = armature.rotation_euler
                root_motion_samples.append((loc[0], loc[1], loc[2], rot[2]))

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
                    if bone_data_type == FLVERBoneDataType.EDIT:
                        # Undo bone CoB first (self-inverse).
                        armature_space_transform = bl_matrix_to_game_trs(bl_bone.matrix @ BONE_CoB_4x4)
                    else:
                        armature_space_transform = bl_matrix_to_game_trs(bl_bone.matrix)
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
        armature: ArmatureObject,
        skeleton_hkx: DES_SkeletonHKX,
        animation_hkx_class: type[DES_AnimationHKX],
    ) -> DES_AnimationHKX:
        """Convert to wavelet-compressed. Demon's Souls (DeS) animations only."""
        interleaved_animation = self.to_interleaved_animation_hkx(
            operator, context, armature, skeleton_hkx, animation_hkx_class
        )
        return interleaved_animation.to_wavelet_hkx()

    def to_spline_animation[AnimationHKXType: BaseAnimationHKX](
        self,
        operator: LoggingOperator,
        context: Context,
        armature: ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[AnimationHKXType],
    ) -> AnimationHKXType:
        interleaved_animation = self.to_interleaved_animation_hkx(
            operator, context, armature, skeleton_hkx, animation_hkx_class
        )
        return interleaved_animation.to_spline_hkx()

    def to_game_compressed_animation[AnimationHKXType: BaseAnimationHKX](
        self,
        operator: LoggingOperator,
        context: Context,
        game: Game,
        armature: ArmatureObject,
        skeleton_hkx: BaseSkeletonHKX,
        animation_hkx_class: type[AnimationHKXType],
        force_interleaved: bool = False,
    ) -> AnimationHKXType:
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

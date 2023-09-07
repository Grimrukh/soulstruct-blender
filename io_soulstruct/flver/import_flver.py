"""
Import FLVER files (with/without DCX) into Blender 3.3+ (Python 3.10+ scripting required).

Can find FLVERs in CHRBND, OBJBND, and PARTSBND binders (with or without DCX compression).

The FLVER is imported as an Armature object with all FLVER sub-meshes as Mesh children and model 'dummy points' as Empty
children.

New Blender materials will be created as needed that approximate in-game look (including conversion and loading of
located DDS textures), but existing materials with the same name as the FLVER materials will be used if the user selects
this option (on by default).

Critical FLVER information needed for export, but not represented anywhere else in Blender, is stored with custom
properties as necessary (on FLVER armatures, meshes, dummies, and materials).

NOTE: Currently only thoroughly tested for DS1/DSR.
"""
from __future__ import annotations

__all__ = ["ImportFLVER", "ImportFLVERWithMSBChoice", "ImportEquipmentFLVER", "FLVERImporter"]

import math
import re
import traceback
import typing as tp
from pathlib import Path

import bpy
import bpy.ops
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Vector, Matrix

from soulstruct.base.models.flver import FLVER
from soulstruct.containers import Binder, BinderEntry
from soulstruct.containers.tpf import TPF, TPFTexture, batch_get_tpf_texture_png_data
from soulstruct.utilities.maths import Vector3

from io_soulstruct.utilities import *
from .utilities import *
from .materials import MaterialNodeCreator
from .textures.utilities import png_to_bl_image, collect_binder_tpfs, collect_map_tpfs


FLVER_BINDER_RE = re.compile(r"^.*?\.(chr|obj|parts)bnd(\.dcx)?$")
MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")


_SETTINGS = read_settings()
_PNG_CACHE_DIR = _SETTINGS.get("PNGCacheDirectory", "")


class ImportFLVER(LoggingOperator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs."""
    bl_idname = "import_scene.flver"
    bl_label = "Import FLVER"
    bl_description = "Import a FromSoftware FLVER model file. Can import from BNDs and supports DCX-compressed files."

    # ImportHelper mixin class uses this
    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    use_existing_materials: BoolProperty(
        name="Use Existing Materials",
        description="Use existing materials with the same name as the FLVER materials (if any)",
        default=True,
    )

    png_cache_path: StringProperty(
        name="Cached PNG path",
        description="Directory to use for reading/writing cached texture PNGs",
        default=_PNG_CACHE_DIR,
    )

    read_from_png_cache: BoolProperty(
        name="Read from PNG Cache",
        description="Read cached PNGs (instead of DDS files) from the above directory if available",
        default=True,
    )

    write_to_png_cache: BoolProperty(
        name="Write to PNG Cache",
        description="Write PNGs of any loaded textures (DDS files) to the above directory for future use",
        default=True,
    )

    load_map_piece_tpfs: BoolProperty(
        name="Load Map Piece TPF Files",
        description="Look for TPF (DDS) textures in adjacent 'mAA' folder for map piece FLVERs",
        default=True,
    )

    read_msb_transform: BoolProperty(
        name="Read MSB Transform",
        description="Look for matching MSB file in adjacent `MapStudio` folder and set transform of map piece FLVER",
        default=True,
    )

    material_blend_mode: EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ('OPAQUE', "Opaque", "Opaque Blend Mode"),
            ('CLIP', "Clip", "Clip Blend Mode"),
            ('HASHED', "Hashed", "Hashed Blend Mode"),
            ('BLEND', "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        options={'HIDDEN'},
    )

    def execute(self, context):
        print("Executing FLVER import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        flvers = []
        attached_texture_sources = {}  # from multi-texture TPFs directly linked to FLVER
        loose_tpf_sources = {}  # one-texture TPFs that we only read if needed by FLVER

        for file_path in file_paths:

            if FLVER_BINDER_RE.match(file_path.name):
                binder = Binder.from_path(file_path)
                flver = get_flver_from_binder(binder, file_path)
                flvers.append(flver)
                attached_texture_sources |= collect_binder_tpfs(binder, file_path)
            else:  # e.g. loose Map Piece FLVER
                flver = FLVER.from_path(file_path)
                flvers.append(flver)
                if self.load_map_piece_tpfs:
                    # Find map piece TPFs in adjacent `mXX` directory.
                    loose_tpf_sources |= collect_map_tpfs(map_dir_path=file_path.parent)

        write_settings(PNGCacheDirectory=self.png_cache_path)
        png_cache_path = Path(self.png_cache_path) if self.png_cache_path else None

        importer = FLVERImporter(
            self,
            context,
            use_existing_materials=self.use_existing_materials,
            texture_sources=attached_texture_sources,
            loose_tpf_sources=loose_tpf_sources,
            png_cache_path=png_cache_path,
            read_from_png_cache=self.read_from_png_cache,
            write_to_png_cache=self.write_to_png_cache,
            material_blend_mode=self.material_blend_mode,
            base_edit_bone_length=self.base_edit_bone_length,
        )

        for file_path, flver in zip(file_paths, flvers, strict=True):

            transform = None  # type: tp.Optional[Transform]

            if not FLVER_BINDER_RE.match(file_path.name) and self.read_msb_transform:
                if MAP_NAME_RE.match(file_path.parent.name):
                    try:
                        transforms = get_map_piece_msb_transforms(file_path)
                    except Exception as ex:
                        self.warning(f"Could not get MSB transform. Error: {ex}")
                    else:
                        if len(transforms) > 1:
                            # Defer import through MSB choice operator's `run()` method.
                            # Note that the same `importer` object is used -- this `execute()` function will NOT be
                            # called again, TPFs will not be loaded again, etc.
                            importer.context = context
                            ImportFLVERWithMSBChoice.run(
                                importer=importer,
                                flver=flver,
                                file_path=file_path,
                                transforms=transforms,
                                use_existing_materials=self.use_existing_materials,
                                png_cache_path=png_cache_path,
                                read_from_png_cache=self.read_from_png_cache,
                                write_to_png_cache=self.write_to_png_cache,
                                load_map_piece_tpfs=self.load_map_piece_tpfs,
                                read_msb_transform=self.read_msb_transform,
                                material_blend_mode=self.material_blend_mode,
                            )
                            continue
                        transform = transforms[0][1]
                else:
                    self.warning(f"Cannot read MSB transform for FLVER in unknown directory: {file_path}.")
            try:
                name = file_path.name.split(".")[0]  # drop all extensions
                bl_flver_mesh = importer.import_flver(flver, name=name, transform=transform)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER: {file_path.name}. Error: {ex}")

            # Select newly imported mesh.
            if bl_flver_mesh:
                bpy.ops.object.select_all(action='DESELECT')
                bl_flver_mesh.select_set(True)
                bpy.context.view_layer.objects.active = bl_flver_mesh

        return {"FINISHED"}


# noinspection PyUnusedLocal
def get_msb_choices(self, context):
    return ImportFLVERWithMSBChoice.enum_options


class ImportFLVERWithMSBChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.flver_with_msb_choice"
    bl_label = "Choose MSB Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[FLVERImporter] = None
    flver: tp.Optional[FLVER] = None
    file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    transforms: tp.Sequence[Transform] = []

    use_existing_materials: bool = True
    png_cache_path: Path = Path(_PNG_CACHE_DIR)
    read_from_png_cache: bool = True
    write_to_png_cache: bool = True
    load_map_piece_tpfs: bool = True
    read_msb_transform: bool = True
    material_blend_mode: str = "HASHED"

    choices_enum: EnumProperty(items=get_msb_choices)

    # noinspection PyUnusedLocal
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "choices_enum", expand=True)

    def execute(self, context):
        choice = int(self.choices_enum)
        transform = self.transforms[choice]

        self.importer.operator = self
        self.importer.context = context

        try:
            name = self.file_path.name.split(".")[0]  # drop all extensions
            bl_armature = self.importer.import_flver(self.flver, name=name, transform=transform)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import FLVER: {self.file_path.name}. Error: {ex}")

        # Select newly imported armature.
        if bl_armature:
            bpy.ops.object.select_all(action='DESELECT')
            bl_armature.select_set(True)
            bpy.context.view_layer.objects.active = bl_armature

        return {"FINISHED"}

    @classmethod
    def run(
        cls,
        importer: FLVERImporter,
        flver: FLVER,
        file_path: Path,
        transforms: list[tuple[str, Transform]],
        use_existing_materials: bool,
        png_cache_path: Path,
        read_from_png_cache: bool,
        write_to_png_cache: bool,
        load_map_piece_tpfs: bool,
        read_msb_transform: bool,
        material_blend_mode: str,
    ):
        cls.use_existing_materials = use_existing_materials
        cls.png_cache_path = png_cache_path
        cls.read_from_png_cache = read_from_png_cache
        cls.write_to_png_cache = write_to_png_cache
        cls.load_map_piece_tpfs = load_map_piece_tpfs
        cls.read_msb_transform = read_msb_transform
        cls.material_blend_mode = material_blend_mode

        cls.importer = importer
        cls.flver = flver
        cls.file_path = file_path
        cls.enum_options = [(str(i), name, "") for i, (name, _) in enumerate(transforms)]
        cls.transforms = [tf for _, tf in transforms]
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.flver_with_msb_choice("INVOKE_DEFAULT")


class ImportEquipmentFLVER(LoggingOperator, ImportHelper):
    """Import weapon/armor FLVER from a `partsbnd` binder and attach it to selected armature (c0000)."""
    bl_idname = "import_scene.equipment_flver"
    bl_label = "Import Equipment FLVER"
    bl_description = "Import a FromSoftware FLVER equipment model file from a PARTSBND file and attach to c0000."

    filename_ext = ".partsbnd"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    use_existing_materials: BoolProperty(
        name="Use Existing Materials",
        description="Use existing materials with the same name as the FLVER materials (if any)",
        default=True,
    )

    png_cache_path: StringProperty(
        name="Cached PNG path",
        description="Directory to use for reading/writing cached texture PNGs",
        default=_PNG_CACHE_DIR,
    )

    read_from_png_cache: BoolProperty(
        name="Read from PNG Cache",
        description="Read cached PNGs (instead of DDS files) from the above directory if available",
        default=True,
    )

    write_to_png_cache: BoolProperty(
        name="Write to PNG Cache",
        description="Write PNGs of any loaded textures (DDS files) to the above directory for future use",
        default=True,
    )

    material_blend_mode: EnumProperty(
        name="Alpha Blend Mode",
        description="Alpha mode to use for new single-texture FLVER materials",
        items=[
            ('OPAQUE', "Opaque", "Opaque Blend Mode"),
            ('CLIP', "Clip", "Clip Blend Mode"),
            ('HASHED', "Hashed", "Hashed Blend Mode"),
            ('BLEND', "Blend", "Sorted Blend Mode"),
        ],
        default="HASHED",
    )

    base_edit_bone_length: FloatProperty(
        name="Base Edit Bone Length",
        description="Length of edit bones corresponding to bone scale 1",
        default=0.2,
        min=0.01,
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        """Animation's rigged armature must be selected (to extract bone names)."""
        try:
            # TODO: Could further check that selected armature is a c0000 (e.g. by checking bones).
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        print("Executing Equipment FLVER import...")

        write_settings(PNGCacheDirectory=self.png_cache_path)

        c0000_armature = context.selected_objects[0]

        file_paths = [Path(self.directory, file.name) for file in self.files]
        flvers = []
        attached_texture_sources = {}  # from multi-texture TPFs directly linked to FLVER

        for file_path in file_paths:

            if FLVER_BINDER_RE.match(file_path.name):
                binder = Binder.from_path(file_path)
                flver = get_flver_from_binder(binder, file_path)
                flvers.append(flver)
                attached_texture_sources |= collect_binder_tpfs(binder, file_path)
            else:  # loose equipment FLVER is unusual but supported, but TPFs may not be found
                flver = FLVER.from_path(file_path)
                flvers.append(flver)
                # No loose TPF sources (nowhere to look).

        png_cache_path = Path(self.png_cache_path) if self.png_cache_path else None

        importer = FLVERImporter(
            self,
            context,
            use_existing_materials=self.use_existing_materials,
            texture_sources=attached_texture_sources,
            loose_tpf_sources={},
            png_cache_path=png_cache_path,
            material_blend_mode=self.material_blend_mode,
            base_edit_bone_length=self.base_edit_bone_length,
        )

        for file_path, flver in zip(file_paths, flvers, strict=True):

            try:
                name = file_path.name.split(".")[0]  # drop all extensions
                bl_flver_mesh = importer.import_flver(flver, name=name, existing_armature=c0000_armature)
            except Exception as ex:
                # Delete any objects created prior to exception (except existing armature at index 0).
                for obj in importer.all_bl_objs[1:]:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import equipment FLVER: {file_path.name}. Error: {ex}")

            # Select newly imported mesh.
            if bl_flver_mesh:
                bpy.ops.object.select_all(action='DESELECT')
                bl_flver_mesh.select_set(True)
                bpy.context.view_layer.objects.active = bl_flver_mesh

        return {"FINISHED"}


class FLVERImporter:
    """Manages imports for a batch of FLVER files imported simultaneously.

    Call `import_flver()` to import a single FLVER file.
    """

    flver: tp.Optional[FLVER]
    name: str
    bl_images: dict[str, tp.Any]  # values can be string DDS paths or loaded Blender images

    use_existing_materials: bool
    texture_sources: dict[str, TPFTexture]
    loose_tpf_sources: dict[str, BinderEntry | TPFTexture]
    png_cache_path: Path | None
    read_from_png_cache: bool
    write_to_png_cache: bool
    material_blend_mode: str
    base_edit_bone_length: float

    def __init__(
        self,
        operator: LoggingOperator,
        context,
        use_existing_materials=True,
        texture_sources: dict[str, TPFTexture] = None,
        loose_tpf_sources: dict[str, BinderEntry | TPFTexture] = None,
        png_cache_path: Path | None = None,
        read_from_png_cache=True,
        write_to_png_cache=True,
        material_blend_mode="HASHED",
        base_edit_bone_length=0.2,
    ):
        self.operator = operator
        self.context = context

        self.use_existing_materials = use_existing_materials
        # These DDS sources/images are shared between all FLVER files imported with this `FLVERImporter` instance.
        self.texture_sources = texture_sources if texture_sources is not None else {}
        self.loose_tpf_sources = loose_tpf_sources if loose_tpf_sources is not None else {}
        self.png_cache_path = Path(png_cache_path) if png_cache_path is not None else None
        self.read_from_png_cache = read_from_png_cache
        self.write_to_png_cache = write_to_png_cache
        self.material_blend_mode = material_blend_mode
        self.base_edit_bone_length = base_edit_bone_length

        # NOT cleared for each import.
        self.bl_images = {}  # maps texture stems to loaded Blender images

        # NOTE: These are all reset/cleared for every FLVER import.
        self.flver = None
        self.name = ""
        self.all_bl_objs = []
        self.materials = {}
        self.bl_bone_names = []

    def import_flver(
        self, flver: FLVER, name: str, transform: tp.Optional[Transform] = None, existing_armature=None
    ):
        """Read a FLVER into a collection of Blender mesh objects (and one Armature).

        If `existing_armature` is passed, the skeleton of `flver` will be ignored, and its mesh will be parented to the
        bones of `existing_armature` instead (e.g. for parenting equipment models to c0000). Dummies should generally
        not be present in these FLVERs, but if they do exist, they will also be parented to the armature with their
        original FLVER name as a prefix to distinguish them from the dummies of `existing_armature`.

        TODO:
            - Not fully happy with how duplicate materials are handled.
                - If an existing material is found, but has no texture images, maybe just load those into it.
        """
        self.flver = flver
        self.name = name
        self.bl_bone_names.clear()
        self.materials = {}

        # Create FLVER bone index -> Blender bone name dictionary. (Blender names are UTF-8.)
        # This is done even when `existing_armature` is given, as the order of bones in this new FLVER may be different
        # and the vertex weight indices need to be directed to the names of bones in `existing_armature` correctly.
        for bone in self.flver.bones:
            # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
            # need to be handled with suffixes.
            self.bl_bone_names.append(f"{bone.name} <DUPE>" if bone.name in self.bl_bone_names else bone.name)

        if self.flver.gx_lists:
            self.warning(
                f"FLVER {self.name} has GX lists, which are not yet supported by the importer. They will be lost."
            )

        # TODO: Would be better to do some other basic FLVER validation here before loading the TPFs.
        if self.texture_sources or self.loose_tpf_sources or self.png_cache_path:
            self.load_texture_images()
        else:
            self.warning("No TPF files or DDS dump folder given. No textures loaded for FLVER.")

        material_creator = MaterialNodeCreator(self.operator, self.bl_images)

        # Vanilla material names are unused and essentially worthless. They can also be the same for materials that
        # actually use different lightmaps, EVEN INSIDE the same FLVER model. Names are changed here to just reflect the
        # index. The original name is NOT kept to avoid stacking up formatting on export/import and because it is so
        # useless anyway.
        self.materials = {}
        self.materials = {
            i: material_creator.create_material(
                flver_material,
                material_name=f"{self.name} Material {i}",
                use_existing=self.use_existing_materials,
                material_blend_mode=self.material_blend_mode,
            )
            for i, flver_material in enumerate(self.flver.materials)
        }

        # TODO: Testing combined mesh.
        # Create a single combined mesh for all submeshes.
        bl_flver_mesh = self.create_combined_mesh_obj(self.flver, name=self.name)
        # Assign basic FLVER header information as custom props.
        # TODO: Configure a full-exporter dropdown/choice of game version that defaults as many of these as possible.
        bl_flver_mesh["big_endian"] = self.flver.big_endian  # bool
        bl_flver_mesh["version"] = self.flver.version.name  # str
        bl_flver_mesh["unicode"] = self.flver.unicode  # bool
        bl_flver_mesh["unk_x4a"] = self.flver.unk_x4a  # bool
        bl_flver_mesh["unk_x4c"] = self.flver.unk_x4c  # int
        bl_flver_mesh["unk_x5c"] = self.flver.unk_x5c  # int
        bl_flver_mesh["unk_x5d"] = self.flver.unk_x5d  # int
        bl_flver_mesh["unk_x68"] = self.flver.unk_x68  # int

        if transform is not None:
            bl_flver_mesh.location = transform.bl_translate
            bl_flver_mesh.rotation_euler = transform.bl_rotate
            bl_flver_mesh.scale = transform.bl_scale

        self.all_bl_objs = [bl_flver_mesh]

        # for i, flver_mesh in enumerate(self.flver.meshes):
        #     mesh_name = f"{self.name} Mesh {i}"
        #     bl_mesh_obj = self.create_sub_mesh_obj(flver_mesh, mesh_name)
        #     bl_mesh_obj["face_set_count"] = len(flver_mesh.face_sets)  # custom property

        if existing_armature:
            # Do not create an armature for this FLVER; parent it to `existing_armature` instead.
            bl_armature = existing_armature
            # Parts FLVERs sometimes have extra non-c0000 bones (e.g. multiple bones with their own name), which we will
            # delete here, to ensure that any attempt to use them in the new meshes raises an error.
            for bone_index in tuple(self.bl_bone_names):
                if self.bl_bone_names[bone_index] not in bl_armature.data.bones:
                    self.bl_bone_names.pop(bone_index)
            dummy_prefix = self.name  # we generally don't expect any dummies, but will distinguish them with this
        else:
            # Create a new armature for this FLVER.
            bl_armature = self.create_armature()
            dummy_prefix = ""

        self.all_bl_objs.append(bl_armature)

        self.context.view_layer.objects.active = bl_flver_mesh
        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_flver_mesh.modifiers["Armature"]
        armature_mod.object = bl_armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

        self.create_dummies(dummy_prefix)

        return bl_flver_mesh  # might be used by other importers

    def create_armature(self):
        """Create a new Blender armature to serve as the parent object for the entire FLVER."""

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")

        bl_armature_data = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature = self.create_obj(f"{self.name} Armature", bl_armature_data)
        self.create_bones(bl_armature)

        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        return bl_armature

    def load_texture_images(self):
        """Load texture images from either `png_cache` folder, TPFs found with the FLVER, or found loose (map) TPFs."""
        textures_to_load = {}  # type: dict[str, TPFTexture]
        for texture_path in self.flver.get_all_texture_paths():
            texture_stem = texture_path.stem
            if texture_stem in self.bl_images:
                continue  # already loaded
            if texture_stem in textures_to_load:
                continue  # already queued to load below

            if self.read_from_png_cache and self.png_cache_path:
                png_path = self.png_cache_path / f"{texture_stem}.png"
                if png_path.is_file():
                    self.bl_images[texture_stem] = bpy.data.images.load(str(png_path))
                    continue

            if texture_stem in self.texture_sources:
                # Found in already-unpacked textures.
                texture = self.texture_sources[texture_path.stem]
                textures_to_load[texture_stem] = texture
                continue

            if texture_stem in self.loose_tpf_sources:
                # Found in loose TPF.
                texture_source = self.loose_tpf_sources[texture_path.stem]
                if isinstance(texture_source, BinderEntry):
                    # Source is a BinderEntry, so it's a TPF inside a Binder.
                    tpf = self.loose_tpf_sources[texture_path.stem].to_binary_file(TPF)
                    if tpf.textures[0].name != texture_path.stem:
                        self.warning(
                            f"Loose TPF '{texture_path.stem}' contained first texture with non-matching name "
                            f"'{tpf.textures[0].name}'. Ignoring."
                        )
                    else:
                        textures_to_load[texture_stem] = tpf.textures[0]
                    continue
                elif isinstance(texture_source, TPFTexture):
                    # Source is a TPFTexture loaded from a loose TPF file, not a Binder.
                    if texture_source.name != texture_path.stem:
                        self.warning(
                            f"Loose TPFTexture keyed under '{texture_stem}' has non-matching name "
                            f"'{texture_source.name}'. Ignoring."
                        )
                    else:
                        textures_to_load[texture_stem] = texture_source
                    continue
                else:
                    self.warning(f"Unexpected loose TPF source type for '{texture_stem}': {type(texture_source)}")

            self.warning(f"Could not find TPF or cached PNG '{texture_path.stem}' for FLVER '{self.name}'.")

        if textures_to_load:
            for texture_stem in textures_to_load:
                self.operator.info(f"Loading texture into Blender: {texture_stem}")
            from time import perf_counter
            t = perf_counter()
            all_png_data = batch_get_tpf_texture_png_data(list(textures_to_load.values()))
            write_png_directory = self.png_cache_path if self.write_to_png_cache else None
            print(f"# INFO: Converted PNG images in {perf_counter() - t} s (cached = {self.write_to_png_cache})")
            for texture_stem, png_data in zip(textures_to_load.keys(), all_png_data):
                bl_image = png_to_bl_image(texture_stem, png_data, write_png_directory)
                self.bl_images[texture_stem] = bl_image
                # Note that the full interroot path is stored in material custom properties.

    def create_combined_mesh_obj(self, flver: FLVER, name: str):
        """Create a single Blender mesh that combines all FLVER sub-meshes, using multiple material slots.

        EXPERIMENTAL. Have not yet confirmed (but suspect) that this will preserve all data. Breakdown:
            - Blender stores POSITION, BONE WEIGHTS, and BONE INDICES on vertices. Any differences here will require
            genuine vertex duplication in Blender.
            - Blender stores MATERIAL SLOT INDEX on faces. This is how different FLVER sub-meshes are stored.
            - Blender stores UV COORDINATES, VERTEX COLORS, and NORMALS on face loops ('vertex instances'). This gels
            with what FLVER meshes want to do.

        We iterate over every FLVER mesh and every face set in that mesh, and treat the face vertices as 'FLVER loops':
            - If a Blender vertex has not been created with the exact same position, bone weights, and GLOBAL
            (FLVER-wide) bone indices, we create it and store its index in a dictionary under the hash of those three
            members.
            - Otherwise, we use the existing Blender vertex index in the new Blender face loop.
            - We assign the FLVER UVs, vertex color(s), and normal data to the loop (normals are accumulated in a list
            the same size as the loop count and applied with `mesh.normals_split_custom_set(normals)` afterward).
        """
        # TODO: should enforce OBJECT mode

        bl_mesh = bpy.data.meshes.new(name=name)

        for material in self.materials.values():
            bl_mesh.materials.append(material)

        if any(mesh.invalid_vertex_size for mesh in flver.meshes):
            # Corrupted sub-meshes. Leave empty.
            return self.create_obj(f"{name} <INVALID>", bl_mesh, parent_to_flver_root=False)

        max_uv_count = max(
            self.flver.buffer_layouts[flver_mesh.vertex_buffers[0].layout_index].get_uv_count()
            for flver_mesh in flver.meshes
        )  # not every face loop will use all these layers (depends on material)

        verts = {}  # maps hashed (position, bone_indices, bone_weights) to Blender vertex index
        bl_verts = []  # final vertex list (positions) to pass to Mesh in one batch
        bl_vert_bone_indices = []
        bl_vert_bone_weights = []

        bl_faces = []  # final face list (vertex index triples) to pass to Mesh in one batch

        # Data to set to Mesh/BMesh loops afterward:
        bl_loop_uvs = []  # type: list[list[list[float]]]  # list of UV lists per loop
        bl_loop_colors = []  # vertex colors for each loop (BMesh layer)
        bl_loop_normals = []  # normals for each loop (passed to `mesh.normals_split_custom_set()`)
        bl_mesh_face_materials = {i: [] for i in self.materials}  # maps material indices to Blender face indices
        # NOTE: We don't import vertex tangents or bitangents. These are computable from the normals and normal UV.

        for flver_mesh in flver.meshes:

            material_face_indices = []

            for triangle in flver_mesh.face_sets[0].get_triangles(allow_primitive_restarts=False):
                bl_face = []  # vertex indices for this face
                material_face_indices.append(len(bl_faces))  # new face index for material
                for v_i in triangle:
                    v = flver_mesh.vertices[v_i]
                    # Convert local mesh bones to FLVER bones. Vertices with the same global bone indices (and weights),
                    # even across different submeshes, will be merged in Blender.
                    if flver_mesh.bone_indices:
                        global_bone_indices = tuple(flver_mesh.bone_indices[i] for i in v.bone_indices)
                    else:
                        # TODO: I *believe* that vertex bone indices are global IFF `mesh.bone_indices` is empty.
                        #  Need to check with non-DS1 games (which always have local indices).
                        global_bone_indices = tuple(v.bone_indices)
                    bl_v_key = (tuple(v.position), global_bone_indices, tuple(v.bone_weights))  # hashable
                    if bl_v_key not in verts:
                        # New Blender vert.
                        bl_v_i = verts[bl_v_key] = len(bl_verts)
                        bl_verts.append(GAME_TO_BL_VECTOR(v.position))
                        bl_vert_bone_indices.append(global_bone_indices)
                        bl_vert_bone_weights.append(v.bone_weights)
                    else:
                        bl_v_i = verts[bl_v_key]

                    bl_face.append(bl_v_i)  # 'new loop' using new or existing vertex
                    bl_loop_uvs.append([
                        [uv[0], 1.0 - uv[1]]  # Z axis discarded, Y axis inverted
                        for uv in v.uvs
                    ])
                    # TODO: Enforce single color, or warn about lost additional color layers. Or just support them.
                    bl_loop_colors.append(v.colors[0])  # FLVER supports multiple colors but never observed (in DS1)
                    bl_loop_normals.append(GAME_TO_BL_VECTOR(v.normal))

                bl_faces.append(bl_face)

            bl_mesh_face_materials[flver_mesh.material_index] = material_face_indices

        bl_mesh.from_pydata(bl_verts, [], bl_faces)
        bl_mesh.update()

        # Assign face materials (submeshes).
        for material_index, faces in bl_mesh_face_materials.items():
            for face_index in faces:
                bl_mesh.polygons[face_index].material_index = material_index

        # Create UV and vertex color data layers.
        for uv_index in range(max_uv_count):
            bl_mesh.uv_layers.new(name=f"UVMap{uv_index + 1}", do_init=False)
        bl_mesh.vertex_colors.new(name="VertexColors")

        # Access layers at their final addresses.
        uv_layers = []
        for uv_index in range(max_uv_count):
            uv_layers.append(bl_mesh.uv_layers[f"UVMap{uv_index + 1}"])
        vertex_color_layer = bl_mesh.vertex_colors["VertexColors"]

        # Set UVs and vertex colors on loops.
        for loop_index, (loop_uvs, loop_color) in enumerate(zip(bl_loop_uvs, bl_loop_colors)):
            for uv_index, uv in enumerate(loop_uvs):
                uv_layer = uv_layers[uv_index]
                uv_layer.data[loop_index].uv[:] = uv
            vertex_color_layer.data[loop_index].color[:] = loop_color

        # Enable custom split normals and assign them.
        for v in bl_loop_normals:
            v.normalize()  # WARNING: If FLVER uses byte or short compression, importing/exporting will be lossy!
        bl_mesh.create_normals_split()
        bl_mesh.normals_split_custom_set(bl_loop_normals)  # one normal per loop
        bl_mesh.use_auto_smooth = True  # required for custom split normals to actually be used (rather than just face)
        bl_mesh.calc_normals_split()  # copy custom split normal data into API mesh loops
        bl_mesh.update()

        bl_mesh_obj = self.create_obj(name, bl_mesh, parent_to_flver_root=False)

        # Naming a vertex group after a Blender bone will automatically link it in the Armature modifier below.
        bone_vertex_groups = [
            bl_mesh_obj.vertex_groups.new(name=bone_name)
            for bone_name in self.bl_bone_names
        ]  # type: list[bpy.types.VertexGroup]

        # Awkwardly, we need a separate call to `VertexGroups[bone_index].add(indices, weight)` for each combination
        # of `bone_index` and `weight`, so the dictionary keys constructed above are a tuple of those two to minimize
        # the number of `add()` calls needed below.
        bone_vertex_group_indices = {}  # type: dict[tuple[int, float], list[int]]

        for v_i, (bone_indices, bone_weights) in enumerate(zip(bl_vert_bone_indices, bl_vert_bone_weights)):
            if all(weight == 0.0 for weight in bone_weights) and len(set(bone_indices)) == 1:
                # Map Piece FLVERs use a single duplicated index and no weights.
                # TODO: May be able to assert that this is ALWAYS true for ALL vertices in map pieces.
                v_bone_index = bone_indices[0]
                bone_vertex_group_indices.setdefault((v_bone_index, 1.0), []).append(v_i)
            else:
                # Standard multi-bone weighting.
                for v_bone_index, v_bone_weight in zip(bone_indices, bone_weights):
                    if v_bone_weight == 0.0:
                        continue
                    bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(v_i)

        for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
            bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

        # Custom properties with mesh data.

        # Bool array.
        bl_mesh_obj["Material Submesh Bind Pose"] = [flver_mesh.is_bind_pose for flver_mesh in flver.meshes]

        # Bool array. We only store this setting for the first `FaceSet`.
        bl_mesh_obj["Material Submesh Cull Back Faces"] = [
            flver_mesh.face_sets[0].cull_back_faces for flver_mesh in flver.meshes
        ]

        # Int array. NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
        bl_mesh_obj["Material Submesh Default Bone Index"] = [
            flver_mesh.default_bone_index for flver_mesh in flver.meshes
        ]

        # Int array. Main face set is copied to all additional face sets on export.
        bl_mesh_obj["Face Set Count"] = [
            len(flver_mesh.face_sets) for flver_mesh in flver.meshes
        ]

        return bl_mesh_obj

    def create_bones(self, bl_armature):
        """Create FLVER bones on given `bl_armature` in Blender.

        Bones can be a little confusing in Blender. See:
            https://docs.blender.org/api/blender_python_api_2_71_release/info_gotcha.html#editbones-posebones-bone-bones

        The short story is that the "resting state" of each bone, including its head and tail position, is created in
        EDIT mode (as `EditBone` instances). This data defines the "zero deformation" state of the mesh with regard to
        bone weights, and will typically not be edited again when posing/animating a mesh that is rigged to this
        Armature. Instead, the bones are accessed as `PoseBone` instances in POSE mode, where they are treated like
        objects with transform data.

        If a FLVER bone has a parent bone, its FLVER transform is given relative to its parent's frame of reference.
        Determining the final position of any given bone in world space therefore requires all of its parents'
        transforms to be accumulated up to the root. (The same is true for HKX animation coordinates, which are local
        bone transformations in the same coordinate system.)

        Note that while bones are typically used for obvious animation cases in characters, objects, and parts (e.g.
        armor/weapons), they are also occasionally used in a fairly basic way by map pieces to position certain vertices
        in certain meshes. When this happens, so far, the bones have always been root bones, and basically function as
        shifted origins for the coordinates of certain vertices. I strongly suspect, but have not absolutely confirmed,
        that the `is_bind_pose` attribute of each mesh indicates whether FLVER bone data should be written to the
        EditBone (`is_bind_pose=True`) or PoseBone (`is_bind_pose=False`). Of course, we have to decide for each BONE,
        not each mesh, so currently I am enforcing that `is_bind_pose=False` for ALL meshes in order to write the bone
        transforms to PoseBone rather than EditBone. A warning will be logged if only some of them are `False`.

        The AABB of each bone is presumably generated to include all vertices that use that bone as a weight.
        """

        write_bone_type = ""
        warn_partial_bind_pose = False
        for mesh in self.flver.meshes:
            if mesh.is_bind_pose:  # characters, objects, parts
                if not write_bone_type:
                    write_bone_type = "EDIT"  # write bone transforms to EditBones
                elif write_bone_type == "POSE":
                    warn_partial_bind_pose = True
                    write_bone_type = "EDIT"
                    break
            else:  # map pieces
                if not write_bone_type:
                    write_bone_type = "POSE"  # write bone transforms to PoseBones
                elif write_bone_type == "EDIT":
                    warn_partial_bind_pose = True
                    break  # keep EDIT default
        if warn_partial_bind_pose:
            self.warning(
                f"Some meshes in FLVER {self.name} use `is_bind_pose` (bone data written to EditBones) and some do not "
                f"(bone data written to PoseBones). Writing all bone data to EditBones."
            )

        # TODO: Theoretically, we could handled mixed bind pose/non-bind pose meshes IF AND ONLY IF they did not use the
        #  same bones. The bind pose bones could have their data written to EditBones, and the non-bind pose bones could
        #  have their data written to PoseBones. The 'is_bind_pose' custom property of each mesh can likewise be used on
        #  export, once it's confirmed that the same bone does not appear in both types of mesh.

        self.context.view_layer.objects.active = bl_armature
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        # Create all edit bones. Head/tail are not set yet (depends on `write_bone_type` below).
        edit_bones = self.create_edit_bones(bl_armature)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        if write_bone_type == "EDIT":
            self.write_data_to_edit_bones(edit_bones)
            del edit_bones  # clear references to edit bones as we exit EDIT mode
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        elif write_bone_type == "POSE":
            # This method will change back to OBJECT mode internally before setting pose bone data.
            self.write_data_to_pose_bones(bl_armature, edit_bones)
        else:
            # Should not be possible to reach.
            raise ValueError(f"Invalid `write_bone_type`: {write_bone_type}")

    def create_edit_bones(self, bl_armature) -> list[bpy.types.EditBone]:
        """Create all edit bones from FLVER bones in `bl_armature`."""
        edit_bones = []  # all bones
        for game_bone, bl_bone_name in zip(self.flver.bones, self.bl_bone_names, strict=True):
            edit_bone = bl_armature.data.edit_bones.new(bl_bone_name)  # '<DUPE>' suffixes already added to names
            edit_bone: bpy.types.EditBone

            edit_bone["unk_x3c"] = game_bone.unk_x3c  # TODO: seems to be 1 for root bones?

            # If this is `False`, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
            # That is, pose basis translation will be interpreted as being in parent space (or object for root bones)
            # rather than in the 'rest pose space' of this bone. We don't want such behavior, particularly for FLVER
            # root bones like 'Pelvis'.
            edit_bone.use_local_location = True

            if game_bone.child_index != -1:
                # TODO: Check if this is set IFF bone has exactly one child, which can be auto-detected.
                edit_bone["child_name"] = self.bl_bone_names[game_bone.child_index]
            if game_bone.next_sibling_index != -1:
                edit_bone["next_sibling_name"] = self.bl_bone_names[game_bone.next_sibling_index]
            if game_bone.previous_sibling_index != -1:
                edit_bone["previous_sibling_name"] = self.bl_bone_names[game_bone.previous_sibling_index]
            edit_bones.append(edit_bone)
        return edit_bones

    def write_data_to_edit_bones(self, edit_bones: list[bpy.types.EditBone]):

        game_arma_transforms = self.flver.get_bone_armature_space_transforms()

        for game_bone, edit_bone, game_arma_transform in zip(
            self.flver.bones, edit_bones, game_arma_transforms, strict=True
        ):
            game_translate, game_rotmat, game_scale = game_arma_transform

            if not is_uniform(game_scale, rel_tol=0.001):
                self.warning(f"Bone {game_bone.name} has non-uniform scale: {game_scale}. Left as identity.")
                bone_length = self.base_edit_bone_length
            elif any(c < 0.0 for c in game_scale):
                self.warning(f"Bone {game_bone.name} has negative scale: {game_scale}. Left as identity.")
                bone_length = self.base_edit_bone_length
            elif math.isclose(game_scale.x, 1.0, rel_tol=0.001):
                # Bone scale is ALMOST uniform and 1. Correct it.
                bone_length = self.base_edit_bone_length
            else:
                # Bone scale is uniform and not close to 1, which we can support (though it should be rare/never).
                bone_length = game_scale.x * self.base_edit_bone_length

            bl_translate = GAME_TO_BL_VECTOR(game_translate)
            # We need to set an initial head/tail position with non-zero length for the `matrix` setter to act upon.
            edit_bone.head = bl_translate
            edit_bone.tail = bl_translate + Vector((0.0, bone_length, 0.0))  # default tail position, rotated below

            bl_rot_mat3 = GAME_TO_BL_MAT3(game_rotmat)
            bl_lrs_mat = bl_rot_mat3.to_4x4()
            bl_lrs_mat.translation = bl_translate
            edit_bone.matrix = bl_lrs_mat
            edit_bone.length = bone_length  # does not interact with `matrix`

            if game_bone.parent_index != -1:
                parent_edit_bone = edit_bones[game_bone.parent_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

    def write_data_to_pose_bones(self, bl_armature, edit_bones: list[bpy.types.EditBone]):

        for game_bone, edit_bone in zip(self.flver.bones, edit_bones, strict=True):
            # All edit bones are just Blender-Y-direction ("forward") stubs of base length.
            # This rigging makes map piece 'pose' bone data transform as expected for showing accurate vertex positions.
            edit_bone.head = Vector((0, 0, 0))
            edit_bone.tail = Vector((0, self.base_edit_bone_length, 0))

        del edit_bones  # clear references to edit bones as we exit EDIT mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        pose_bones = bl_armature.pose.bones  # type: list[bpy.types.PoseBone]
        for game_bone, pose_bone in zip(self.flver.bones, pose_bones):
            # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
            #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
            pose_bone.rotation_mode = "QUATERNION"  # should already be default, but being explicit
            game_translate, game_bone_rotate = game_bone.translate, game_bone.rotate
            pose_bone.location = GAME_TO_BL_VECTOR(game_translate)
            pose_bone.rotation_quaternion = GAME_TO_BL_EULER(game_bone_rotate).to_quaternion()
            pose_bone.scale = GAME_TO_BL_VECTOR(game_bone.scale)

    def create_dummies(self, bl_armature, dummy_prefix=""):
        """Create empty objects that represent dummies.

        The reference ID of the dummy (the value used to refer to it in other game files/code) is included in the name,
        so that it can be easily modified. The format of the dummy name should therefore not be changed. (Note that the
        order of dummies does not matter, and multiple dummies can have the same reference ID.)

        All dummies are children of the armature, and most are children of a specific bone given in 'attach_bone_name'.
        As much as I'd like to nest them under another empty object, to properly attach them to the armature, they have
        to be direct children.
        """

        for i, game_dummy in enumerate(self.flver.dummies):
            if dummy_prefix:
                name = f"[{dummy_prefix}] Dummy<{i}> [{game_dummy.reference_id}]"
            else:
                name = f"Dummy<{i}> [{game_dummy.reference_id}]"
            bl_dummy = self.create_obj(name, parent_to_flver_root=True)
            bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
            bl_dummy.empty_display_size = 0.05

            if game_dummy.use_upward_vector:
                bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, game_dummy.upward)
            else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
                bl_rotation_euler = game_forward_up_vectors_to_bl_euler(game_dummy.forward, Vector3((0, 1, 0)))

            if game_dummy.parent_bone_index != -1:
                # Bone's FLVER translate is in the space of (i.e. relative to) this parent bone.
                # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent and
                # controls how the dummy moves during armature animations.
                bl_bone_name = self.bl_bone_names[game_dummy.parent_bone_index]
                bl_dummy["parent_bone_name"] = bl_bone_name
                bl_parent_bone_matrix = bl_armature.data.bones[bl_bone_name].matrix_local
                bl_location = bl_parent_bone_matrix @ GAME_TO_BL_VECTOR(game_dummy.translate)
            else:
                # Bone's location is in armature space.
                bl_dummy["parent_bone_name"] = ""
                bl_location = GAME_TO_BL_VECTOR(game_dummy.translate)

            # Dummy moves with this bone during animations.
            if game_dummy.attach_bone_index != -1:
                bl_dummy.parent_bone = self.bl_bone_names[game_dummy.attach_bone_index]
                bl_dummy.parent_type = "BONE"

            # We need to set the dummy's world matrix, rather than its local matrix, to bypass its possible bone
            # attachment above.
            bl_dummy.matrix_world = Matrix.LocRotScale(bl_location, bl_rotation_euler, Vector((1.0, 1.0, 1.0)))

            # NOTE: Reference ID not included as a property.
            # bl_dummy["reference_id"] = dummy.reference_id  # int
            bl_dummy["color_rgba"] = game_dummy.color_rgba  # RGBA
            bl_dummy["flag_1"] = game_dummy.flag_1  # bool
            bl_dummy["use_upward_vector"] = game_dummy.use_upward_vector  # bool
            # NOTE: These two properties are only non-zero in Sekiro (and probably Elden Ring).
            bl_dummy["unk_x30"] = game_dummy.unk_x30  # int
            bl_dummy["unk_x34"] = game_dummy.unk_x34  # int

    def create_obj(self, name: str, data=None, parent_to_flver_root=True):
        """Create a new Blender object. By default, will be parented to the FLVER's armature object."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)  # add to scene's object collection
        self.all_bl_objs.append(obj)
        if parent_to_flver_root:
            obj.parent = self.flver_root
        return obj

    def warning(self, warning: str):
        print(f"# WARNING: {warning}")
        self.operator.report({"WARNING"}, warning)

    @property
    def flver_root(self):
        """Always the first object created."""
        return self.all_bl_objs[0]

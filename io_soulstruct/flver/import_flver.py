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

__all__ = ["ImportFLVER", "ImportFLVERWithMSBChoice", "ImportEquipmentFLVER"]

import math
import re
import traceback
import typing as tp
from pathlib import Path

import bpy
import bpy_types
import bmesh
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
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
        default="D:\\blender_png_cache",
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

        png_cache_path = Path(self.png_cache_path) if self.png_cache_path else None

        importer = FLVERImporter(
            self,
            context,
            use_existing_materials=self.use_existing_materials,
            texture_sources=attached_texture_sources,
            loose_tpf_sources=loose_tpf_sources,
            png_cache_path=png_cache_path,
            material_blend_mode=self.material_blend_mode,
        )

        for file_path, flver in zip(file_paths, flvers, strict=True):

            transform = None  # type: tp.Optional[Transform]

            if not FLVER_BINDER_RE.match(file_path.name) and self.read_msb_transform:
                if MAP_NAME_RE.match(file_path.parent.name):
                    try:
                        transforms = get_msb_transforms(file_path)
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
                importer.import_flver(flver, name=name, transform=transform)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER: {file_path.name}. Error: {ex}")

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
    png_cache_path: Path = Path("D:/blender_png_cache")
    read_from_png_cache: bool = True
    write_to_png_cache: bool = True
    load_map_piece_tpfs: bool = True
    read_msb_transform: bool = True
    material_blend_mode: str = "HASHED"

    choices_enum: bpy.props.EnumProperty(items=get_msb_choices)

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
            self.importer.import_flver(self.flver, name=name, transform=transform)
        except Exception as ex:
            for obj in self.importer.all_bl_objs:
                bpy.data.objects.remove(obj)
            traceback.print_exc()
            return self.error(f"Cannot import FLVER: {self.file_path.name}. Error: {ex}")

        return {'FINISHED'}

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
        default="D:\\blender_png_cache",
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

        c0000_armature = context.selected_objects[0]

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

        png_cache_path = Path(self.png_cache_path) if self.png_cache_path else None

        importer = FLVERImporter(
            self,
            context,
            use_existing_materials=self.use_existing_materials,
            texture_sources=attached_texture_sources,
            loose_tpf_sources=loose_tpf_sources,
            png_cache_path=png_cache_path,
            material_blend_mode=self.material_blend_mode,
        )

        for file_path, flver in zip(file_paths, flvers, strict=True):

            try:
                name = file_path.name.split(".")[0]  # drop all extensions
                importer.import_flver(flver, name=name, existing_armature=c0000_armature)
            except Exception as ex:
                # Delete any objects created prior to exception (except existing armature at index 0).
                for obj in importer.all_bl_objs[1:]:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import equipment FLVER: {file_path.name}. Error: {ex}")

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
    ):
        self.operator = operator
        self.context = context

        self.use_existing_materials = use_existing_materials
        # These DDS sources/images are shared between all FLVER files imported with this `FLVERImporter` instance.
        self.texture_sources = texture_sources
        self.loose_tpf_sources = loose_tpf_sources
        self.png_cache_path = png_cache_path
        self.read_from_png_cache = read_from_png_cache
        self.write_to_png_cache = write_to_png_cache
        self.material_blend_mode = material_blend_mode

        # NOT cleared for each import.
        self.bl_images = {}  # maps texture stems to loaded Blender images

        # NOTE: These are all reset/cleared for every FLVER import.
        self.flver = None
        self.name = ""
        self.all_bl_objs = []
        self.materials = {}
        self.bl_bone_names = {}  # type: dict[int, str]

    def import_flver(
        self, flver: FLVER, name: str, transform: tp.Optional[Transform] = None, existing_armature=None
    ):
        """Read a FLVER into a collection of Blender mesh objects (and one Armature).

        If `existing_armature` is passed, the skeleton of `flver` will be ignored, and its submeshes will be parented
        to the bones of `existing_armature` instead (e.g. for parenting equipment models to c0000). Dummies should
        generally not be present in these FLVERs, but if they do exist, they will also be parented to the armature with
        their original FLVER name as a prefix to distinguish them from the dummies of `existing_armature`.

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
        for bone_index, bone in enumerate(self.flver.bones):
            # Just using actual bone names to avoid the need for parsing rules on export. However, duplicate names
            # need to be handled with suffixes.
            if bone.name in self.bl_bone_names.values():
                # Name already exists. Add ' <DUPE>' suffix (may stack).
                self.bl_bone_names[bone_index] = bone.name + " <DUPE>"
            else:
                self.bl_bone_names[bone_index] = bone.name

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
            bl_armature = self.create_armature(transform)
            dummy_prefix = ""

        self.all_bl_objs = [bl_armature]

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

        for i, flver_mesh in enumerate(self.flver.meshes):
            mesh_name = f"{self.name} Mesh {i}"
            bl_mesh_obj = self.create_mesh_obj(flver_mesh, mesh_name)
            bl_mesh_obj["face_set_count"] = len(flver_mesh.face_sets)  # custom property

        self.create_dummies(dummy_prefix)

        return self.all_bl_objs[0]  # might be used by other importers

    def create_armature(self, transform: tp.Optional[Transform] = None):
        """Create a new Blender armature to serve as the parent object for the entire FLVER."""

        # Set mode to OBJECT and deselect all objects.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action="DESELECT")

        bl_armature = self.create_bones()

        if bpy.ops.object.mode_set.poll():  # just to be safe
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Assign basic FLVER header information as custom props.
        # TODO: Configure a full-exporter dropdown/choice of game version that defaults as many of these as possible.
        bl_armature["big_endian"] = self.flver.big_endian  # bool
        bl_armature["version"] = self.flver.version.name  # str
        bl_armature["unicode"] = self.flver.unicode  # bool
        bl_armature["unk_x4a"] = self.flver.unk_x4a  # bool
        bl_armature["unk_x4c"] = self.flver.unk_x4c  # int
        bl_armature["unk_x5c"] = self.flver.unk_x5c  # int
        bl_armature["unk_x5d"] = self.flver.unk_x5d  # int
        bl_armature["unk_x68"] = self.flver.unk_x68  # int

        if transform is not None:
            bl_armature.location = transform.bl_translate
            bl_armature.rotation_euler = transform.bl_rotate
            bl_armature.scale = transform.bl_scale

        return bl_armature

    def load_texture_images(self):
        """Load texture images from either `png_cache` folder, TPFs found with the FLVER, or scanned loose (map) TPFs."""
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
                    if tpf.textures[0].stem != texture_path.stem:
                        self.warning(
                            f"Loose TPF '{texture_path.stem}' contained first texture with non-matching name "
                            f"'{tpf.textures[0].stem}'. Ignoring."
                        )
                    else:
                        textures_to_load[texture_stem] = tpf.textures[0]
                    continue
                elif isinstance(texture_source, TPFTexture):
                    # Source is a TPFTexture loaded from a loose TPF file, not a Binder.
                    if texture_source.stem != texture_path.stem:
                        self.warning(
                            f"Loose TPFTexture keyed under '{texture_stem}' has non-matching name "
                            f"'{texture_source.stem}'. Ignoring."
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
            print(f"# INFO: Batch converted to PNG images in {perf_counter() - t} s (cached = {self.write_to_png_cache})")
            for texture_stem, png_data in zip(textures_to_load.keys(), all_png_data):
                bl_image = png_to_bl_image(texture_stem, png_data, write_png_directory)
                self.bl_images[texture_stem] = bl_image
                # Note that the full interroot path is stored in material custom properties.

    def create_mesh_obj(
        self,
        flver_mesh: FLVER.Mesh,
        mesh_name: str,
    ):
        """Create a Blender mesh object.

        Data is stored in the following ways:
            vertices are simply `vertex.position` remapped as (x, y, z)
            edges are not used
            faces are `face_set.get_triangles()`; only index 0 (maximum detail face set) is used
            normals are simply `vertex.normal` remapped as (-x, y, z)
                - note that normals are stored under loops, e.g. `mesh.loops[i].normal`
                - can iterate over loops and copy each normal to vertex `loop.vertex_index`

        Vertex groups are used to rig vertices to bones.
        """
        bl_mesh = bpy.data.meshes.new(name=mesh_name)

        if flver_mesh.invalid_vertex_size:
            # Corrupted mesh. Leave empty.
            return self.create_obj(f"{mesh_name} <INVALID>", bl_mesh)

        uv_count = self.flver.buffer_layouts[flver_mesh.vertex_buffers[0].layout_index].get_uv_count()

        vertices = [GAME_TO_BL_VECTOR(v.position) for v in flver_mesh.vertices]
        edges = []  # no edges in FLVER
        faces = flver_mesh.face_sets[0].get_triangles(allow_primitive_restarts=False)

        bl_mesh.from_pydata(vertices, edges, faces)
        bl_mesh.materials.append(self.materials[flver_mesh.material_index])

        bm = bmesh.new()
        if bpy.context.mode == "EDIT_MESH":
            bm.from_edit_mesh(bl_mesh)
        else:
            bm.from_mesh(bl_mesh)

        # To create normals, we create custom "split" normals, and copy them to the loop normals.
        # There is no point setting the non-custom vertex normals; Blender recomputes them very aggressively. We use
        # `calc_normals_split()` on export and use the loop normals to get what we need.
        bl_mesh.create_normals_split()
        # NOTE: X is negated, but Y and Z are not swapped here, as the global mesh transformation below will do that.
        # (Unfortunately I only discovered this bug on 2021-08-08.)
        bl_vertex_normals = [GAME_TO_BL_VECTOR(v.normal) for v in flver_mesh.vertices]
        for loop in bl_mesh.loops:
            # I think vertex normals need to be copied to loop (vertex-per-face) normals.
            loop.normal[:] = bl_vertex_normals[loop.vertex_index]
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.to_mesh(bl_mesh)

        # Note that we don't assign these UV and vertex color layers as they're created, because their address may
        # change as other layers are created, leading to random internal errors.
        for uv_index in range(uv_count):
            bl_mesh.uv_layers.new(name=f"UVMap{uv_index + 1}", do_init=False)
        bl_mesh.vertex_colors.new(name="VertexColors")

        # Access layers at their final addresses.
        uv_layers = []
        for uv_index in range(uv_count):
            uv_layers.append(bl_mesh.uv_layers[f"UVMap{uv_index + 1}"])
        vertex_colors = bl_mesh.vertex_colors["VertexColors"]

        # In Blender, UVs and vertex colors must be set per loop, whereas they are per vertex in FLVER. Every loop using
        # the same vertex will have the same UVs and vertex color, and this will also be enforced on export, so make
        # sure to preserve per-vertex data if you edit either property in Blender.
        for j, loop in enumerate(bl_mesh.loops):
            loop: bpy.types.MeshLoop
            vertex = flver_mesh.vertices[loop.vertex_index]
            for uv_index, uv in enumerate(vertex.uvs):
                uv_layers[uv_index].data[j].uv[:] = [uv[0], 1.0 - uv[1]]  # Z axis discarded, Y axis inverted
            if len(vertex.colors) != 1:
                raise FLVERImportError(
                    f"Vertex {loop.vertex_index} in FLVER mesh {mesh_name} has {len(vertex.colors)} vertex colors. "
                    f"Expected exactly one."
                )
            vertex_colors.data[j].color[:] = vertex.colors[0]

        bl_mesh.update()
        bl_mesh.calc_normals_split()

        # Delete vertices not used in face set 0. We do this after setting UVs and other layers above.
        bm = bmesh.new()
        if bpy.context.mode == "EDIT_MESH":
            bm.from_edit_mesh(bl_mesh)
        else:
            bm.from_mesh(bl_mesh)
        bm.verts.ensure_lookup_table()
        used_vertex_indices = {i for face in faces for i in face}
        unused_vertex_indices = [i for i in range(len(bm.verts)) if i not in used_vertex_indices]
        bl_vertex_normals = [n for i, n in enumerate(bl_vertex_normals) if i in used_vertex_indices]
        for bm_vert in [bm.verts[i] for i in unused_vertex_indices]:
            bm.verts.remove(bm_vert)
        bm.verts.index_update()
        bm.faces.index_update()
        bm.to_mesh(bl_mesh)

        # noinspection PyTypeChecker
        bl_mesh.normals_split_custom_set_from_vertices(bl_vertex_normals)
        bl_mesh.use_auto_smooth = False  # modifies `calc_normals_split()` outcome upon export

        bl_mesh_obj = self.create_obj(mesh_name, bl_mesh)
        self.context.view_layer.objects.active = bl_mesh_obj

        bone_vertex_groups = []  # type: list[bpy.types.VertexGroup]
        # noinspection PyTypeChecker
        bone_vertex_group_indices = {}  # type: dict[tuple[int, float], list[int]]

        # TODO: I *believe* that vertex bone indices are global if and only if `mesh.bone_indices` is empty. (In DSR,
        #  it's never empty.)
        if flver_mesh.bone_indices:
            for mesh_bone_index in flver_mesh.bone_indices:
                group = bl_mesh_obj.vertex_groups.new(name=self.bl_bone_names[mesh_bone_index])
                bone_vertex_groups.append(group)
            for i, game_vert in enumerate(flver_mesh.vertices):
                # TODO: May be able to assert that this is ALWAYS true for ALL vertices in map pieces.
                if all(weight == 0.0 for weight in game_vert.bone_weights) and len(set(game_vert.bone_indices)) == 1:
                    # Map Piece FLVERs use a single duplicated index and no weights.
                    v_bone_index = game_vert.bone_indices[0]
                    bone_vertex_group_indices.setdefault((v_bone_index, 1.0), []).append(i)
                else:
                    # Standard multi-bone weighting.
                    for v_bone_index, v_bone_weight in zip(game_vert.bone_indices, game_vert.bone_weights):
                        if v_bone_weight == 0.0:
                            continue
                        bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(i)
        else:  # vertex bone indices are global...?
            for bone_index in range(len(self.armature.pose.bones)):
                group = bl_mesh_obj.vertex_groups.new(name=self.bl_bone_names[bone_index])
                bone_vertex_groups.append(group)
            for i, game_vert in enumerate(flver_mesh.vertices):
                for v_bone_index, v_bone_weight in zip(game_vert.bone_indices, game_vert.bone_weights):
                    if v_bone_weight == 0.0:
                        continue
                    bone_vertex_group_indices.setdefault((v_bone_index, v_bone_weight), []).append(i)

        # Awkwardly, we need a separate call to `VertexGroups[bone_index].add(indices, weight)` for each combination
        # of `bone_index` and `weight`, so the dictionary keys constructed above are a tuple of those two to minimize
        # the number of `add()` calls needed below.
        for (bone_index, bone_weight), bone_vertices in bone_vertex_group_indices.items():
            bone_vertex_groups[bone_index].add(bone_vertices, bone_weight, "ADD")

        bpy.ops.object.modifier_add(type="ARMATURE")
        armature_mod = bl_mesh_obj.modifiers["Armature"]
        armature_mod.object = self.armature
        armature_mod.show_in_editmode = True
        armature_mod.show_on_cage = True

        # Custom properties with mesh data.
        bl_mesh_obj["is_bind_pose"] = flver_mesh.is_bind_pose
        # We only store this setting for the first `FaceSet`.
        bl_mesh_obj["cull_back_faces"] = flver_mesh.face_sets[0].cull_back_faces
        # NOTE: This index is sometimes invalid for vanilla map FLVERs (e.g., 1 when there is only one bone).
        bl_mesh_obj["default_bone_index"] = flver_mesh.default_bone_index

        return bl_mesh_obj

    def create_bones(self):
        """Create FLVER bones in Blender.

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
        bl_armature = bpy.data.armatures.new(f"{self.name} Armature")
        bl_armature_obj = self.create_obj(f"{self.name}", bl_armature, parent_to_armature=False)

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

        self.context.view_layer.objects.active = bl_armature_obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        edit_bones = []  # all bones
        for i, game_bone in enumerate(self.flver.bones):
            edit_bone = bl_armature_obj.data.edit_bones.new(self.bl_bone_names[i])  # '<DUPE>' suffixes already added

            # If this is disabled, then a bone's rest pose rotation will NOT affect its relative pose basis translation.
            # That is, pose basis translation will be interpreted as being in parent space (or object for root bones)
            # rather than in the 'rest pose space' of this bone. We don't want such behavior, particularly for FLVER
            # root bones like 'Pelvis'.
            edit_bone.use_local_location = True

            edit_bone["unk_x3c"] = game_bone.unk_x3c
            edit_bone: bpy_types.EditBone
            if game_bone.child_index != -1:
                # TODO: Check if this is set IFF bone has exactly one child, which can be auto-detected.
                edit_bone["child_name"] = self.bl_bone_names[game_bone.child_index]
            if game_bone.next_sibling_index != -1:
                edit_bone["next_sibling_name"] = self.bl_bone_names[game_bone.next_sibling_index]
            if game_bone.previous_sibling_index != -1:
                edit_bone["previous_sibling_name"] = self.bl_bone_names[game_bone.previous_sibling_index]
            edit_bones.append(edit_bone)

        # NOTE: Bones that have no vertices weighted to them are left as 'unused' root bones in the FLVER skeleton.
        # They may be animated by HKX animations (and will affect their children appropriately) but will not actually
        # affect any vertices in the mesh.

        for game_bone, edit_bone in zip(self.flver.bones, edit_bones):

            if write_bone_type == "POSE":
                # All edit bones are just Blender-Y-direction stubs of length 1 ("forward").
                # This rotation makes map piece 'pose' bone data transform as expected.
                edit_bone.head = Vector((0, 0, 0))
                edit_bone.tail = Vector((0, 1.0, 0))  # TODO: Import option for edit bone length.
            else:  # "EDIT"
                edit_bone.length = 0.2  # TODO: import setting (purely for visuals)

                # All Blender edit bone transforms are set in object space, with `edit_bone.parent` set below.
                game_translate, game_rot_mat3 = game_bone.get_absolute_translate_rotate(self.flver.bones)
                bl_bone_translate = GAME_TO_BL_VECTOR(game_translate)
                game_rot_euler = game_rot_mat3.to_euler_angles(radians=True)
                bl_rot_euler = GAME_TO_BL_EULER(game_rot_euler)

                # Check if scale is ALMOST one and correct it.
                # TODO: Maybe too aggressive?
                if is_uniform(game_bone.scale, rel_tol=0.001) and math.isclose(game_bone.scale.x, 1.0, rel_tol=0.001):
                    bl_bone_scale = Vector((1.0, 1.0, 1.0))
                else:
                    bl_bone_scale = GAME_TO_BL_VECTOR(game_bone.scale)

                bl_edit_bone_mat = Matrix.LocRotScale(bl_bone_translate, bl_rot_euler, bl_bone_scale)
                # TODO: Currently properly putting bone scale into 4x4 matrix, rather than `length`, though it is
                #  unlikely to be ever displayed properly OR actually used by game models/animations.
                edit_bone.matrix = bl_edit_bone_mat

                if not is_uniform(game_bone.scale, rel_tol=0.001):
                    self.warning(f"Bone {game_bone.name} has non-uniform scale: {game_bone.scale}. Left as identity.")
                elif any(c < 0.0 for c in game_bone.scale):
                    self.warning(f"Bone {game_bone.name} has negative scale: {game_bone.scale}. Left as identity.")

            if game_bone.parent_index != -1:
                parent_edit_bone = edit_bones[game_bone.parent_index]
                edit_bone.parent = parent_edit_bone
                # edit_bone.use_connect = True

        del edit_bones  # clear references to edit bones as we exit EDIT mode

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        if write_bone_type == "POSE":
            for game_bone, pose_bone in zip(self.flver.bones, bl_armature_obj.pose.bones):
                # TODO: Pose bone transforms are relative to parent (in both FLVER and Blender).
                #  Confirm map pieces still behave as expected, though (they shouldn't even have child bones).
                # game_bone_translate, game_bone_rotate_mat = game_bone.get_absolute_translate_rotate(self.flver.bones)
                # game_bone_rotate = game_bone_rotate_mat.to_euler_angles(radians=True)
                game_translate, game_bone_rotate = game_bone.translate, game_bone.rotate
                pose_bone.location = GAME_TO_BL_VECTOR(game_translate)
                pose_bone.rotation_quaternion = GAME_TO_BL_EULER(game_bone_rotate).to_quaternion()
                pose_bone.scale = GAME_TO_BL_VECTOR(game_bone.scale)

        return bl_armature_obj

    def create_dummies(self, dummy_prefix=""):
        """Create empty objects that represent dummies.

        All dummies are children of the armature, and most are children of a specific bone given in 'attach_bone_name'.
        """

        for i, dummy in enumerate(self.flver.dummies):
            if dummy_prefix:
                name = f"{dummy_prefix} Dummy<{i}> [{dummy.reference_id}]"
            else:
                name = f"Dummy<{i}> [{dummy.reference_id}]"
            bl_dummy = self.create_obj(name, parent_to_armature=True)
            bl_dummy.empty_display_type = "ARROWS"  # best display type/size I've found (single arrow not sufficient)
            bl_dummy.empty_display_size = 0.05

            if dummy.use_upward_vector:
                bl_rotation_euler = game_forward_up_vectors_to_bl_euler(dummy.forward, dummy.upward)
            else:  # TODO: I assume this is right (up-ignoring dummies only rotate around vertical axis)
                bl_rotation_euler = game_forward_up_vectors_to_bl_euler(dummy.forward, Vector3((0, 1, 0)))

            if dummy.parent_bone_index != -1:
                # Bone's location is given in the space of this parent bone.
                # NOTE: This is NOT the same as the 'attach' bone, which is used as the actual Blender parent.
                bl_bone_name = self.bl_bone_names[dummy.parent_bone_index]
                bl_dummy["parent_bone_name"] = bl_bone_name
                bl_parent_bone_matrix = self.armature.data.bones[bl_bone_name].matrix_local
                bl_location = bl_parent_bone_matrix @ GAME_TO_BL_VECTOR(dummy.translate)
            else:
                # Bone's location is in armature space.
                bl_dummy["parent_bone_name"] = ""
                bl_location = GAME_TO_BL_VECTOR(dummy.translate)

            # Dummy moves with this bone during animations.
            if dummy.attach_bone_index != -1:
                bl_dummy.parent_bone = self.bl_bone_names[dummy.attach_bone_index]
                bl_dummy.parent_type = "BONE"

            # We need to set the dummy's world matrix, rather than its local matrix, to bypass its possible bone
            # attachment above.
            bl_dummy.matrix_world = Matrix.LocRotScale(bl_location, bl_rotation_euler, Vector((1.0, 1.0, 1.0)))

            # NOTE: This property is the canonical dummy ID. You are free to rename the dummy without affecting it.
            bl_dummy["reference_id"] = dummy.reference_id  # int
            bl_dummy["color"] = dummy.color_rgba  # RGBA
            bl_dummy["flag_1"] = dummy.flag_1  # bool
            bl_dummy["use_upward_vector"] = dummy.use_upward_vector  # bool
            # NOTE: These two properties are only non-zero in Sekiro (and probably Elden Ring).
            bl_dummy["unk_x30"] = dummy.unk_x30  # int
            bl_dummy["unk_x34"] = dummy.unk_x34  # int

    def create_obj(self, name: str, data=None, parent_to_armature=True):
        """Create a new Blender object. By default, will be parented to the FLVER's armature object."""
        obj = bpy.data.objects.new(name, data)
        self.context.scene.collection.objects.link(obj)  # add to scene's object collection
        self.all_bl_objs.append(obj)
        if parent_to_armature:
            obj.parent = self.armature
        return obj

    def warning(self, warning: str):
        print(f"# WARNING: {warning}")
        self.operator.report({"WARNING"}, warning)

    @property
    def armature(self):
        """Always the first object created."""
        return self.all_bl_objs[0]

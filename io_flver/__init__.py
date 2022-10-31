from __future__ import annotations

import importlib
import re
import sys
import tempfile
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, CollectionProperty
# noinspection PyUnresolvedReferences
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper
from soulstruct.containers.dcx import DCXType

modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
import soulstruct
importlib.reload(soulstruct)

from soulstruct.base.binder_entry import BinderEntry
from soulstruct.base.models.flver import FLVER
from soulstruct.base.textures.dds import texconv
from soulstruct.containers import Binder
from soulstruct.containers.tpf import TPF

if "FLVERImporter" in locals():
    importlib.reload(sys.modules["io_flver.core"])
    importlib.reload(sys.modules["io_flver.export_flver"])
    importlib.reload(sys.modules["io_flver.import_flver"])

from io_flver.core import FLVERImportError, Transform, get_msb_transforms
from io_flver.export_flver import FLVERExporter
from io_flver.import_flver import FLVERImporter
from io_flver.textures import *

if tp.TYPE_CHECKING:
    from .import_flver import FLVERImporter


bl_info = {
    "name": "FLVER format",
    "author": "Scott Mooney (Grimrukh)",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "File > Import-Export",
    "description": "FLVER IO meshes, materials, textures, and bones",
    "warning": "",
    "doc_url": "https://github.com/Grimrukh/soulstruct-blender",
    "support": "COMMUNITY",
    "category": "Import-Export",
}


MAP_NAME_RE = re.compile(r"^(m\d\d)_\d\d_\d\d_\d\d$")
BINDER_RE = re.compile(r"^.*?\.(chr|obj|parts)bnd(\.dcx)?$")


class LoggingOperator(Operator):

    cleanup_callback: tp.Callable = None

    def info(self, msg: str):
        print(f"# INFO: {msg}")
        self.report({"INFO"}, msg)

    def warning(self, msg: str):
        print(f"# WARNING: {msg}")
        self.report({"WARNING"}, msg)

    def error(self, msg: str) -> set[str]:
        print(f"# ERROR: {msg}")
        if self.cleanup_callback:
            try:
                self.cleanup_callback()
            except Exception as ex:
                self.report({"ERROR"}, f"Error occurred during cleanup callback: {ex}")
        self.report({"ERROR"}, msg)
        return {"CANCELLED"}


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

    dds_path: StringProperty(
        name="Read Dumped DDS Files",
        description="Look for pre-dumped DDS textures in this folder, if given.",
        default="D:\\dds_dump",
    )

    load_map_piece_tpfs: BoolProperty(
        name="Load Map Piece TPF Files",
        description="Look for TPF (DDS) textures in adjacent 'mAA' folder for map piece FLVERs.",
        default=True,
    )

    read_msb_transform: BoolProperty(
        name="Read MSB Transform",
        description="Look for matching MSB file in adjacent `MapStudio` folder and set transform of map piece FLVER.",
        default=True,
    )

    enable_alpha_hashed: BoolProperty(
        name="Enable Alpha Hashed",
        description="Enable material Alpha Hashed (rather than Opaque) for single-texture FLVER materials.",
        default=True,
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        options={'HIDDEN'},
    )

    def execute(self, context):
        print("Executing import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]
        flvers = []
        texture_sources = {}

        for file_path in file_paths:

            if BINDER_RE.match(file_path.name):
                binder = Binder(file_path)

                # Find FLVER entry.
                flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
                if not flver_entries:
                    raise FLVERImportError(f"Cannot find a FLVER file in binder {file_path}.")
                elif len(flver_entries) > 1:
                    raise FLVERImportError(f"Found multiple FLVER files in binder {file_path}.")
                flver = FLVER(flver_entries[0].data)
                flvers.append(flver)

                # Find TPFs or CHRTPFBHDs inside binder, potentially using `chrtpfbdt` file if it exists.
                for tpf_entry in binder.find_entries_matching_name(TPF_RE):  # generally only one
                    tpf = TPF(tpf_entry.data)
                    # tpf.convert_dds_formats("DX10", "DXT1")  # TODO: outdated
                    for texture in tpf.textures:
                        texture_sources[texture.name] = texture
                try:
                    tpfbhd_entry = binder.find_entry_matching_name(r".*\.chrtpfbhd")
                except (binder.BinderEntryMissing, ValueError):
                    pass
                else:
                    # Search for BDT.
                    tpfbdt_path = file_path.parent / f"{tpfbhd_entry.name.split('.')[0]}.chrtpfbdt"
                    if tpfbdt_path.is_file():
                        tpfbxf = Binder(tpfbhd_entry.data, bdt_source=tpfbdt_path)
                        for tpf_entry in tpfbxf.entries:
                            match = TPF_RE.match(tpf_entry.name)
                            if match:
                                tpf = TPF(tpf_entry.data)
                                tpf.convert_dds_formats("DX10", "DXT1")
                                for texture in tpf.textures:
                                    texture_sources[texture.name] = texture
                    else:
                        self.warning(f"Could not find adjacent CHRTPFBDT for TPFs in file {file_path}.")
            else:
                # Map Piece loose FLVER.
                flver = FLVER(file_path)
                flvers.append(flver)

                if self.load_map_piece_tpfs:
                    # Find map piece TPFs in adjacent `mXX` directory.
                    directory = Path(self.directory)
                    map_directory_match = MAP_NAME_RE.match(directory.name)
                    if not map_directory_match:
                        return self.error("FLVER not located in a map folder (`mAA_BB_CC_DD`). Cannot load TPFs.")
                    tpf_directory = directory.parent / map_directory_match.group(1)
                    if not tpf_directory.is_dir():
                        return self.error(f"`mXX` TPF folder does not exist: {tpf_directory}. Cannot load TPFs.")

                    texture_sources |= TPF.collect_tpf_textures(tpf_directory)

        dds_dump_path = Path(self.dds_path) if self.dds_path else None

        importer = FLVERImporter(self, context, texture_sources, dds_dump_path, self.enable_alpha_hashed)

        for file_path, flver in zip(file_paths, flvers, strict=True):

            transform = None  # type: tp.Optional[Transform]

            if not BINDER_RE.match(file_path.name) and self.read_msb_transform:
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
                                read_tpfs=self.load_map_piece_tpfs,
                                dds_path=self.dds_path,
                                enable_alpha_blend=self.enable_alpha_hashed,
                            )
                            continue
                        transform = transforms[0][1]
                else:
                    self.warning(f"Cannot read MSB transform for FLVER in unknown directory: {file_path}.")
            try:
                importer.import_flver(flver, file_path=file_path, transform=transform)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                return self.error(f"Cannot import FLVER: {file_path.name}. Error: {ex}")

        return {"FINISHED"}


class ImportFLVERWithMSBChoice(LoggingOperator):
    """Presents user with a choice of enums from `enum_choices` class variable (set prior).

    See: https://blender.stackexchange.com/questions/6512/how-to-call-invoke-popup
    """
    bl_idname = "wm.msb_choice_operator"
    bl_label = "Choose MSB Entry"

    # For deferred import in `execute()`.
    importer: tp.Optional[FLVERImporter] = None
    flver: tp.Optional[FLVER] = None
    file_path: Path = Path()
    enum_options: list[tuple[tp.Any, str, str]] = []
    transforms: tp.Sequence[Transform] = []
    dds_path: str = "F:\\dds_dump"
    read_tpfs: bool = False

    choices_enum: bpy.props.EnumProperty(items=lambda self, context: ImportFLVERWithMSBChoice.enum_options)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

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
            self.importer.import_flver(self.flver, file_path=self.file_path, transform=transform)
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
        read_tpfs=False,
        dds_path="F:\\dds_dump",
        enable_alpha_blend=False,
    ):
        cls.dds_path = dds_path
        cls.read_tpfs = read_tpfs
        cls.enable_alpha_blend = enable_alpha_blend
        cls.importer = importer
        cls.flver = flver
        cls.file_path = file_path
        cls.enum_options = [(str(i), name, "") for i, (name, _) in enumerate(transforms)]
        cls.transforms = [tf for _, tf in transforms]
        # noinspection PyUnresolvedReferences
        bpy.ops.wm.msb_choice_operator("INVOKE_DEFAULT")


class ExportFLVER(LoggingOperator, ExportHelper):
    """Export FLVER from a Blender Armature parent."""
    bl_idname = "export_scene.flver"
    bl_label = "Export FLVER"
    bl_description = "Export a prepared Blender object hierarchy to a FromSoftware FLVER model file."

    # ExportHelper mixin class uses this
    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
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
        description="Type of DCX compression to apply to exported file"
    )

    # TODO: Options to:
    #   - Export DDS textures into BND TPF, CHRTPFBXF, or `mAA` folder BXFs.
    #       - Probably complex/useful enough to be a separate export function.
    #   - Detect appropriate MSB and update transform of this model instance (if unique) (low priority).

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No FLVER parent object selected.")
        elif len(selected_objs) > 1:
            return self.error("Multiple objects selected. Exactly one FLVER parent object must be selected.")
        flver_parent_obj = selected_objs[0]
        if bpy.ops.object.mode_set.poll():
            # Must be in OBJECT mode for export, as some data (e.g. UVs) is not accessible in EDIT mode.
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = FLVERExporter(self, context)

        try:
            flver = exporter.export_flver(flver_parent_obj)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")
        else:
            dcx_type = DCXType[self.dcx_type]
            flver.dcx_type = dcx_type
            try:
                # Will create a `.bak` file automatically if absent.
                flver.write(Path(self.filepath))
            except Exception as ex:
                traceback.print_exc()
                return self.error(f"Cannot write exported FLVER. Error: {ex}")

        return {"FINISHED"}


class ExportFLVERIntoBinder(LoggingOperator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs."""
    bl_idname = "export_scene.flver_binder"
    bl_label = "Export FLVER Into Binder"
    bl_description = "Export a FLVER model file into a FromSoftware Binder (BND/BHD)"

    # ImportHelper mixin class uses this
    filename_ext = ".chrbnd"

    filter_glob: StringProperty(
        default="*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
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
        description="Type of DCX compression to apply to exported file"
    )

    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        description="Overwrite first existing '.flver{.dcx}' entry in Binder.",
        default=True,
    )

    default_entry_id: IntProperty(
        name="Default ID",
        description="Binder entry ID to use if a '.flver{.dcx}' entry does not already exist in Binder. If left as -1, "
                    "an existing entry MUST be found for export to proceed.",
        default=-1,
        min=-1,
    )

    default_entry_flags: IntProperty(
        name="Default Flags",
        description="Flags to set to Binder entry if it needs to be created.",
        default=0x2,
    )

    default_entry_path: StringProperty(
        name="Default Path",
        description="Path prefix to use for Binder entry if it needs to be created. Use {name} as a format "
                    "placeholder for the name of this FLVER object. Default is for DS1R `chrbnd.dcx` files.",
        default="N:\\FRPG\\data\\INTERROOT_x64\\chr\\{name}\\{name}.flver",
    )

    # TODO: DCX compression option (defaults to None).

    @classmethod
    def poll(cls, context):
        try:
            return context.selected_objects[0].type == "ARMATURE"
        except IndexError:
            return False

    def execute(self, context):
        print("Executing export...")

        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            return self.error("No FLVER parent object selected.")
        elif len(selected_objs) > 1:
            return self.error("Multiple objects selected. Exactly one FLVER parent object must be selected.")
        flver_parent_obj = selected_objs[0]
        if bpy.ops.object.mode_set.poll():
            # Must be in OBJECT mode for export, as some data (e.g. UVs) is not accessible in EDIT mode.
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        exporter = FLVERExporter(self, context)

        try:
            flver = exporter.export_flver(flver_parent_obj)
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot get exported FLVER. Error: {ex}")

        try:
            binder = Binder(self.filepath)
        except Exception as ex:
            return self.error(f"Could not load Binder file. Error: {ex}.")

        flver_entries = binder.find_entries_matching_name(r".*\.flver(\.dcx)?")
        if not flver_entries:
            if self.default_entry_id == -1:
                return self.error("No FLVER files found in Binder and default entry ID was left as -1.")
            if self.default_entry_id in binder.entries_by_id:
                if not self.overwrite_existing:
                    return self.error(
                        f"Binder entry {self.default_entry_id} already exists in Binder and overwrite is disabled."
                    )
                flver_entry = binder.entries_by_id[self.default_entry_id]
            else:
                # Create new entry. TODO: Currently no DCX.
                entry_path = self.default_entry_path.format(name=flver_parent_obj.name)
                flver_entry = BinderEntry(
                    b"", entry_id=self.default_entry_id, path=entry_path, flags=self.default_entry_flags
                )
        else:
            if not self.overwrite_existing:
                return self.error("FLVER file already exists in Binder and overwrite is disabled.")

            if len(flver_entries) > 1:
                self.warning(f"Multiple FLVER files found in Binder. Replacing first: {flver_entries[0].name}")
            flver_entry = flver_entries[0]

        dcx_type = DCXType[self.dcx_type]
        flver.dcx_type = dcx_type

        try:
            flver_entry.set_uncompressed_data(flver.pack_dcx())  # DCX will default to None here from exporter function
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write exported FLVER. Error: {ex}")

        try:
            # Will create a `.bak` file automatically if absent.
            binder.write()
        except Exception as ex:
            traceback.print_exc()
            return self.error(f"Cannot write Binder with new FLVER. Error: {ex}")

        return {"FINISHED"}


class ImportDDS(LoggingOperator, ImportHelper):
    """Import a DDS file (as a PNG) into a selected `Image` node."""
    bl_idname = "import_image.dds"
    bl_label = "Import DDS"
    bl_description = (
        "Import a DDS texture or single-DDS TPF binder as a PNG image, and optionally set it to all selected Image "
        "Texture nodes. (Does not save the PNG.)"
    )

    filename_ext = ".dds"

    filter_glob: StringProperty(
        default="*.dds;*.tpf;*.tpf.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    set_to_selected_image_nodes: BoolProperty(
        name="Set to Selected Image Node(s)",
        description="Set loaded PNG texture to any selected Image nodes.",
        default=True,
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        options={'HIDDEN'},
    )

    # TODO: Option to replace Blender Image with same name, if present.

    def execute(self, context):
        print("Executing DDS import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]

        for file_path in file_paths:

            if TPF_RE.match(file_path.name):
                tpf = TPF(file_path)
                if len(tpf.textures) > 0:
                    # TODO: Could load all and assign to multiple selected Image Texture nodes if names match?
                    return self.error(f"Cannot import TPF file containing more than one texture: {file_path}")

                bl_image = load_tpf_texture_as_png(tpf.textures[0])
                self.info(f"Loaded DDS file from TPF as PNG: {file_path.name}")
            else:
                # Loose DDS file.
                with tempfile.TemporaryDirectory() as png_dir:
                    temp_dds_path = Path(png_dir, file_path.name)
                    temp_dds_path.write_bytes(file_path.read_bytes())  # copy
                    texconv_result = texconv("-o", png_dir, "-ft", "png", "-f", "RGBA", temp_dds_path)
                    png_path = Path(png_dir, file_path.with_suffix(".png"))
                    if png_path.is_file():
                        bl_image = bpy.data.images.load(str(png_path))
                        bl_image.pack()  # embed PNG in `.blend` file
                        self.info(f"Loaded DDS file as PNG: {file_path.name}")
                    else:
                        stdout = "\n    ".join(texconv_result.stdout.decode().split("\r\n")[3:])  # drop copyright lines
                        return self.error(f"Could not convert texture DDS to PNG:\n    {stdout}")

            # TODO: Option to iterate over ALL materials in .blend and replace a given named image with this new one.
            if self.set_to_selected_image_nodes:
                try:
                    material_nt = context.active_object.active_material.node_tree
                except AttributeError:
                    self.warning("No active object/material node tree detected to set texture to.")
                else:
                    sel = [node for node in material_nt.nodes if node.select and node.bl_idname == "ShaderNodeTexImage"]
                    if not sel:
                        self.warning("No selected Image Texture nodes to set texture to.")
                    else:
                        for image_node in sel:
                            image_node.image = bl_image
                            self.info("Set imported DDS (PNG) texture to Image Texture node.")

        return {"FINISHED"}


class ExportTexturesIntoBinder(LoggingOperator, ImportHelper):
    bl_idname = "export_image.texture_binder"
    bl_label = "Export Textures Into Binder"
    bl_description = (
        "Export image textures from selected Image Texture node(s) into a FromSoftware TPF or TPF-containing Binder "
        "(BND/BHD)"
    )

    # ImportHelper mixin class uses this
    filename_ext = ".chrbnd"

    filter_glob: StringProperty(
        default="*.tpf;*.tpf.dcx;*.tpfbhd;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    replace_texture_name: StringProperty(
        name="Replace Texture Name",
        description="Replace texture/TPF with this name (defaults to exported texture name)",
        default="",
    )

    rename_matching_tpfs: BoolProperty(
        name="Rename Matching TRFs",
        description="Also change name of any TPF wrappers if they match the name being replaced."
    )

    # TODO: Option: if texture name is changed, update that texture path in FLVER (in Binder and custom Blender prop).

    @classmethod
    def poll(cls, context):
        try:
            # TODO: What if you just want to export an image from the Image Viewer? Different operator?
            sel_tex_nodes = [
                node for node in context.active_object.active_material.node_tree.nodes
                if node.select and node.bl_idname == "ShaderNodeTexImage"
            ]
            return bool(sel_tex_nodes)
        except (AttributeError, IndexError):
            return False

    def execute(self, context):
        print("Executing texture export...")

        sel_tex_nodes = [
            node for node in context.active_object.active_material.node_tree.nodes
            if node.select and node.bl_idname == "ShaderNodeTexImage"
        ]
        if not sel_tex_nodes:
            return self.error("No Image Texture material node selected.")
        if len(sel_tex_nodes) > 1 and self.replace_texture_name:
            return self.error("Cannot override 'Replace Texture Name' when exporting multiple textures.")

        try:
            texture_export_info = get_texture_export_info(self.filepath)
        except Exception as ex:
            return self.error(str(ex))

        rename_tpf = self.rename_matching_tpfs and self.replace_texture_name
        for tex_node in sel_tex_nodes:
            bl_image = tex_node.image
            if not bl_image:
                self.warning("Ignoring Image Texture node with no image assigned.")
                continue
            image_stem = Path(bl_image.name).stem

            if self.replace_texture_name:  # will only be allowed if one Image Texture is being exported
                repl_name = f"{Path(self.replace_texture_name).stem}.dds"
            else:
                repl_name = image_stem

            image_exported, dds_format = texture_export_info.inject_texture(bl_image, image_stem, repl_name, rename_tpf)
            if image_exported:
                print(f"Replacing name: {repl_name}")
                self.info(f"Exported '{bl_image.name}' into '{self.filepath}' with DDS format {dds_format}")
            else:
                self.warning(f"Could not find any TPF textures to replace with Blender image: '{image_stem}'")

        # TPFs have all been updated. Now pack modified ones back to their Binders.
        try:
            write_msg = texture_export_info.write_files()
        except Exception as ex:
            return self.error(str(ex))

        self.info(write_msg)
        return {"FINISHED"}


class BakeLightmapTexturse(LoggingOperator):

    bl_idname = "bake.lightmaps"
    bl_label = "Bake Selected Lightmaps"
    bl_description = "Bake lightmap image textures from all materials of all selected FLVERs"

    @classmethod
    def poll(cls, context):
        """FLVER armature(s) must be selected."""
        return context.selected_objects and all(obj.type == "ARMATURE" for obj in context.selected_objects)

    def execute(self, context):
        print("Executing lightmap texture bake...")

        # Get active materials of all submeshes of all selected objects.
        flver_submeshes = []
        for sel_flver_armature in context.selected_objects:
            submeshes = [
                obj for obj in bpy.data.objects
                if obj.parent is sel_flver_armature
                and obj.type == "MESH"
                and not obj.hide_render  # do NOT bake render-hidden objects (eg transparent decals)
            ]
            if not submeshes:
                return self.error(f"Selected object '{sel_flver_armature.name}' has no submesh children.")
            flver_submeshes += submeshes

        # Find texture nodes and set them to active, and get UV layer names.
        original_active_uv_layers = []  # UVLayer objects
        original_lightmap_strengths = []  # pairs of `(node, value)`

        def restore_originals():
            # for _layer in original_active_uv_layers:
            #     _layer.active = True
            for _node, _strength in original_lightmap_strengths:
                _node.inputs["Fac"].default_value = _strength

        self.cleanup_callback = restore_originals

        texture_names = []
        submeshes_to_bake = []
        for submesh in flver_submeshes:
            if not submesh.active_material:
                return self.error(f"Submesh '{submesh.name}' has no active material.")

            # Find Image Texture node of lightmap and its UV layer input.
            for node in submesh.active_material.node_tree.nodes:
                if node.bl_idname == "ShaderNodeTexImage" and node.name.startswith("g_Lightmap |"):
                    # Found Image Texture node.
                    if node.image.name not in texture_names:
                        texture_names.append(node.image.name)
                    try:
                        uv_name = node.inputs["Vector"].links[0].from_node.attribute_name
                    except (AttributeError, IndexError):
                        return self.error(
                            f"Could not find UVMap attribute for image texture node '{node.name}' in material of "
                            f"submesh {submesh.name}."
                        )
                    # Activate texture (for bake target).
                    submesh.active_material.node_tree.nodes.active = node
                    node.select = True
                    original_active_uv_layers.append(submesh.data.uv_layers.active)
                    submesh.data.uv_layers[uv_name].active = True  # active UV layer

                    # Set overlay values to zero while baking.
                    try:
                        overlay_node_fac = node.outputs["Color"].links[0].to_node.inputs["Fac"]
                    except (AttributeError, IndexError):
                        return self.error(
                            f"Could not find `MixRGB` node connected to output of image texture node '{node.name}' "
                            f"in material of submesh {submesh.name}. Aborting for safety; please fix node tree."
                        )
                    overlay_node = node.outputs["Color"].links[0].to_node
                    original_lightmap_strengths.append((overlay_node, overlay_node_fac.default_value))
                    # Detect which mix slot lightmap is using and set factor to disable lightmap while baking.
                    if overlay_node.inputs[1].links[0].from_node == node:  # input 1
                        overlay_node_fac.default_value = 1.0
                    else:  # input 2
                        overlay_node_fac.default_value = 0.0

                    submeshes_to_bake.append(submesh)
                    break
            else:
                self.warning(
                    f"Could not find a `g_Lightmap` texture in active material of mesh '{submesh.name}'. "
                    f"Ignoring submesh."
                )

        if not texture_names or not submeshes_to_bake:
            return self.error("No lightmap textures found to bake into.")

        # Select all submeshes (and only them).
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = submeshes_to_bake[0]  # just in case
        for submesh in submeshes_to_bake:
            submesh.select_set(True)

        # Bake with Cycles. TODO: Reset settings afterward?
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.device = "GPU"
        bpy.context.scene.cycles.samples = 128
        bpy.ops.object.bake(type="SHADOW", use_selected_to_active=False)
        self.info(f"Baked {len(texture_names)} lightmap textures: {', '.join(texture_names)}")
        try:
            self.cleanup_callback()
        except Exception as ex:
            self.warning(f"Error during cleanup callback after operation finished: {ex}")
        return {"FINISHED"}


class ExportLightmapTextures(LoggingOperator, ImportHelper):
    bl_idname = "export_image.lightmaps"
    bl_label = "Export Selected Lightmaps"
    bl_description = (
        "Export lightmap image textures from all materials of all selected FLVERs into a FromSoftware TPF/Binder "
        "(usually a TPFBHD Binder in 'mAA' folder)"
    )

    filename_ext = ".tpfbhd"

    filter_glob: StringProperty(
        default="*.tpf;*.tpf.dcx;*.tpfbhd;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    @classmethod
    def poll(cls, context):
        """FLVER armature(s) must be selected."""
        return context.selected_objects and all(obj.type == "ARMATURE" for obj in context.selected_objects)

    def execute(self, context):
        print("Executing lightmap texture export...")

        # TODO: Check all active materials, find 'g_Lightmap' nodes, and export those images into selected TPFBHD.

        # Get active materials of all submeshes of all selected objects.
        flver_submeshes = []
        for sel_flver_armature in context.selected_objects:
            submeshes = [obj for obj in bpy.data.objects if obj.parent is sel_flver_armature and obj.type == "MESH"]
            if not submeshes:
                return self.error(f"Selected object '{sel_flver_armature.name}' has no submesh children.")
            flver_submeshes += submeshes

        bl_images = []

        for submesh in flver_submeshes:
            if not submesh.active_material:
                return self.error(f"Submesh '{submesh.name}' has no active material.")

            # Find Image Texture node of lightmap.
            for node in submesh.active_material.node_tree.nodes:
                if node.bl_idname == "ShaderNodeTexImage" and node.name.startswith("g_Lightmap |"):
                    # Found Image Texture node.
                    if not node.image:
                        self.warning(
                            f"Ignoring Image Texture node in material of mesh '{submesh.name}' with no image assigned."
                        )
                        continue  # keep searching same material
                    if node.image not in bl_images:
                        bl_images.append(node.image)
                    break  # do not look for more than one lightmap
            else:
                self.warning(f"Could not find a `g_Lightmap` Image Texture node in material of mesh '{submesh.name}'.")

        if not bl_images:
            return self.error(f"No lightmap textures found to export across selected FLVERs.")

        try:
            texture_export_info = get_texture_export_info(self.filepath)
        except Exception as ex:
            return self.error(str(ex))

        rename_tpf = self.rename_matching_tpfs and self.replace_texture_name
        for bl_image in bl_images:
            if not bl_image:
                self.warning("Ignoring Image Texture node with no image assigned.")
                continue
            image_stem = Path(bl_image.name).stem

            if self.replace_texture_name:  # will only be allowed if one Image Texture is being exported
                repl_name = f"{Path(self.replace_texture_name).stem}.dds"
            else:
                repl_name = image_stem

            image_exported, dds_format = texture_export_info.inject_texture(bl_image, image_stem, repl_name, rename_tpf)
            if image_exported:
                print(f"Replacing name: {repl_name}")
                self.info(f"Exported '{bl_image.name}' into '{self.filepath}' with DDS format {dds_format}")
            else:
                self.warning(f"Could not find any TPF textures to replace with Blender image: '{image_stem}'")

        # TPFs have all been updated. Now pack modified ones back to their Binders.
        try:
            write_msg = texture_export_info.write_files()
        except Exception as ex:
            return self.error(str(ex))

        self.info(write_msg)
        return {"FINISHED"}


class FLVER_PT_main_panel(bpy.types.Panel):
    bl_label = "Main Panel"
    bl_idname = "FLVER_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FLVER"

    def draw(self, context):
        row = self.layout.row()
        row.label(text="FLVER importers:")
        row = self.layout.row()
        row.operator("import_scene.flver")

        row = self.layout.row()
        row.label(text="FLVER exporters:")
        row = self.layout.row()
        row.operator("export_scene.flver")
        row = self.layout.row()
        row.operator("export_scene.flver_binder")

        row = self.layout.row()
        row.label(text="Utilities:")
        row = self.layout.row()
        row.operator("import_image.dds")
        row = self.layout.row()
        row.operator("export_image.texture_binder")
        row = self.layout.row()
        row.operator("bake.lightmaps")
        row = self.layout.row()
        row.operator("export_image.lightmaps")


def menu_func_import(self, context):
    self.layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver/.*bnd)")


def menu_func_export(self, context):
    self.layout.operator(ExportFLVER.bl_idname, text="FLVER (.flver)")


classes = (
    ImportFLVER,
    ImportFLVERWithMSBChoice,
    ExportFLVER,
    ExportFLVERIntoBinder,
    ImportDDS,
    ExportTexturesIntoBinder,
    BakeLightmapTexturse,
    ExportLightmapTextures,
    FLVER_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

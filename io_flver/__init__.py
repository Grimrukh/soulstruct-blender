from __future__ import annotations

import importlib
import re
import sys
import traceback
import typing as tp
from pathlib import Path

import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
# noinspection PyUnresolvedReferences
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

modules_path = str(Path(__file__).parent / "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
import soulstruct
importlib.reload(soulstruct)

from soulstruct.base.models.flver import FLVER
from soulstruct.containers import Binder
from soulstruct.containers.tpf import TPF

if "FLVERImporter" in locals():
    importlib.reload(sys.modules["io_flver.core"])
    importlib.reload(sys.modules["io_flver.export_flver"])
    importlib.reload(sys.modules["io_flver.import_flver"])

from io_flver.core import FLVERImportError, Transform, get_msb_transforms
from io_flver.export_flver import inject_flver_content
from io_flver.import_flver import FLVERImporter

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


MAP_NAME_RE = re.compile(r"^m\d\d_\d\d_\d\d_\d\d$")
BINDER_RE = re.compile(r"^.*?\.(chr|obj|parts)bnd(\.dcx)?$")
TPF_RE = re.compile(rf"(.*)\.tpf(\.dcx)?")


class ImportFLVER(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs."""
    bl_idname = "import_scene.flver"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import FLVER"

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
        default=False,
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
                # TODO: `.tpf` in CHRBND contains multiple textures; need to load them as separate keys (DDS -> TGA).
                for tpf_entry in binder.find_entries_matching_name(TPF_RE):  # generally only one
                    tpf = TPF(tpf_entry.data)
                    tpf.convert_dds_formats("DX10", "DXT1")
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
                        self.report({"WARNING"}, f"Could not find adjacent CHRTPFBDT for TPFs in file {file_path}.")
            else:
                # Map Piece loose FLVER.
                flver = FLVER(file_path)
                flvers.append(flver)

                if self.load_map_piece_tpfs:
                    # Find map piece TPFs in adjacent `mXX` directory.
                    directory = Path(self.directory)
                    map_directory_match = MAP_NAME_RE.match(directory.name)
                    if not map_directory_match:
                        self.report({"ERROR"}, "FLVER not located in a map folder (`mAA_BB_CC_DD`). Cannot load TPFs.")
                        return {"CANCELLED"}
                    tpf_directory = directory.parent / map_directory_match.group(1)
                    if not tpf_directory.is_dir():
                        self.report({"ERROR"}, f"`mXX` TPF folder does not exist: {tpf_directory}. Cannot load TPFs.")
                        return {"CANCELLED"}

                    texture_sources |= TPF.collect_tpfs(tpf_directory, convert_formats=("DX10", "DXT1"))

        dds_dump_path = Path(self.dds_path) if self.dds_path else None

        importer = FLVERImporter(self, context, texture_sources, dds_dump_path, self.enable_alpha_hashed)

        for file_path, flver in zip(file_paths, flvers, strict=True):

            transform = None  # type: tp.Optional[Transform]

            if not BINDER_RE.match(file_path.name) and self.read_msb_transform:
                if MAP_NAME_RE.match(file_path.parent.name):
                    try:
                        transforms = get_msb_transforms(file_path)
                    except Exception as ex:
                        self.report({"WARNING"}, str(ex))
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
                    self.report({"WARNING"}, f"Cannot read MSB transform for FLVER in unknown directory: {file_path}.")
            try:
                importer.import_flver(flver, file_path=file_path, transform=transform)
            except Exception as ex:
                # Delete any objects created prior to exception.
                for obj in importer.all_bl_objs:
                    bpy.data.objects.remove(obj)
                traceback.print_exc()  # for inspection in Blender console
                self.report({"ERROR"}, f"Cannot import FLVER: {file_path.name}. Error: {ex}")
        return {"FINISHED"}


class ImportFLVERWithMSBChoice(bpy.types.Operator):
    """Presents user with a choice of enums from `CHOICES` global list.

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
            import traceback
            traceback.print_exc()
            self.report({"ERROR"}, f"Cannot import FLVER: {self.file_path.name}. Error: {ex}")

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


# TODO: Complete self-sufficient FLVER export!
"""
- Dummies, bone information, material information, mesh information, buffer layout information all needed.
    - Can use empties for dummies.
    - Can use empties with custom properties for buffer layout and header information.
    - Can validate buffer layout against materials...?
- Blender function that generates the "Info Empty" just mentioned, with appropriate defaults. 
- Will NOT support GX Lists (initially).
- Will NOT support LOD "face set subsets" (too complicated and weird). LOD face sets will be duplicates of main set. 
"""


class ExportFLVERMeshes(Operator, ImportHelper):
    """Export FLVER meshes only into an existing FLVER file.

    Note that this class uses `ImportHelper` still, since we are choosing an existing file with it.
    """
    bl_idname = "export_scene.flver_meshes"
    bl_label = "Export FLVER Meshes"

    # ExportHelper mixin class uses this
    filename_ext = ".flver"

    filter_glob: StringProperty(
        default="*.flver;*.flver.dcx",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects]
        if not selected_objs:
            self.report({"ERROR"}, f"No FLVER parent object selected.")
            return {"CANCELLED"}
        elif len(selected_objs) > 1:
            self.report({"ERROR"}, f"Multiple objects selected. Exactly one FLVER parent object must be selected.")
            return {"CANCELLED"}
        flver_parent_obj = selected_objs[0]
        if bpy.ops.object.mode_set.poll():
            # Must be in OBJECT mode for export, as some data (e.g. UVs) is not accessible in EDIT mode.
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        try:
            inject_flver_content(flver_parent_obj, self.filepath)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self.report({"ERROR"}, f"Cannot export mesh to FLVER. Error: {ex}")
        return {"FINISHED"}


def menu_func_import(self, context):
    self.layout.operator(ImportFLVER.bl_idname, text="FLVER (.flver)")  # TODO: or .chrbnd, etc.


def menu_func_export(self, context):
    self.layout.operator(ExportFLVERMeshes.bl_idname, text="FLVER Meshes (.flver)")


classes = (
    ImportFLVER,
    ImportFLVERWithMSBChoice,
    ExportFLVERMeshes,
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

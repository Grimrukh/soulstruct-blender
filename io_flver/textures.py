from __future__ import annotations

__all__ = [
    "ImportDDS",
    "ExportTexturesIntoBinder",
    "LightmapBakeProperties",
    "BakeLightmapTextures",
    "ExportLightmapTextures",
]

import tempfile
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from soulstruct.base.textures.dds import texconv
from soulstruct.containers import DCXType, TPF

from .core import *
from .textures_utils import *


class ImportDDS(LoggingOperator, ImportHelper):
    """Import a DDS file (as a PNG) into a selected `Image` node."""
    bl_idname = "import_image.dds"
    bl_label = "Import DDS"
    bl_description = (
        "Import a DDS texture or single-DDS TPF binder as a PNG image, and optionally set it to all selected Image "
        "Texture nodes (does not save the PNG)"
    )

    filename_ext = ".dds"

    filter_glob: bpy.props.StringProperty(
        default="*.dds;*.tpf;*.tpf.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    set_to_selected_image_nodes: bpy.props.BoolProperty(
        name="Set to Selected Image Node(s)",
        description="Set loaded PNG texture to any selected Image nodes",
        default=True,
    )

    files: bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: bpy.props.StringProperty(
        options={'HIDDEN'},
    )

    # TODO: Option to replace Blender Image with same name, if present.

    def execute(self, context):
        print("Executing DDS import...")

        file_paths = [Path(self.directory, file.name) for file in self.files]

        for file_path in file_paths:

            if TPF_RE.match(file_path.name):
                tpf = TPF(file_path)
                if len(tpf.textures) > 1:
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

    filter_glob: bpy.props.StringProperty(
        default="*.tpf;*.tpf.dcx;*.tpfbhd;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    replace_texture_name: bpy.props.StringProperty(
        name="Replace Texture Name",
        description="Replace texture/TPF with this name (defaults to exported texture name)",
        default="",
    )

    rename_matching_tpfs: bpy.props.BoolProperty(
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


class LightmapBakeProperties(bpy.types.PropertyGroup):

    bake_device: bpy.props.EnumProperty(
        name="Bake Device",
        items=[
            ("CPU", "CPU", "Use Cycles engine with CPU"),
            ("GPU", "GPU", "Use Cycles engine with GPU"),
        ],
        default="GPU",
        description="Device (CPU/GPU) to use for Cycles bake render"
    )

    bake_samples: bpy.props.IntProperty(
        name="Bake Samples",
        description="Number of Cycles render samples to use while baking",
        default=128,
    )

    bake_margin: bpy.props.IntProperty(
        name="Bake Margin",
        description="Texture margin (in pixels) for 'UV islands' in bake",
        default=0,
    )

    bake_edge_shaders: bpy.props.BoolProperty(
        name="Bake Edge Shaders",
        description="If enabled, meshes with 'Edge'-type materials (eg decals) will not affect the bake render (but "
                    "may still use them in their materials)",
        default=False,
    )

    bake_rendered_only: bpy.props.BoolProperty(
        name="Bake Render-Visible Only",
        description="If enabled, only meshes with render visibility (camera icon) will affect the bake render",
        default=False,
    )

    # NOTE: [We] water shaders are NEVER baked.


class BakeLightmapTextures(LoggingOperator):

    bl_idname = "bake.lightmaps"
    bl_label = "Bake FLVER Lightmaps"
    bl_description = "Bake rendered lightmap image textures from all materials of all selected FLVERs"

    @classmethod
    def poll(cls, context):
        """FLVER armature(s) must be selected."""
        return context.selected_objects and all(obj.type == "ARMATURE" for obj in context.selected_objects)

    def execute(self, context):
        print("Executing lightmap texture bake...")

        try:
            options = context.scene.lightmap_bake_props
        except AttributeError:
            return self.error(
                "Could not retrieve Bake Lightmap property options. The FLVER add-on may not be installed correctly."
            )

        # Get active materials of all submeshes of all selected objects.
        flver_submeshes = []
        for sel_flver_armature in context.selected_objects:
            submeshes = [
                obj for obj in bpy.data.objects
                if obj.parent is sel_flver_armature
                and obj.type == "MESH"
            ]
            if not submeshes:
                return self.error(f"Selected object '{sel_flver_armature.name}' has no submesh children.")
            flver_submeshes += submeshes

        # Find texture nodes and set them to active, and get UV layer names.
        original_lightmap_strengths = []  # pairs of `(node, value)`
        render_settings = {}

        def restore_originals():
            # NOTE: Does NOT restore old active UV layer, as you most likely want to immediately see the bake result!
            for _node, _strength in original_lightmap_strengths:
                _node.inputs["Fac"].default_value = _strength
            # Restore render settings.
            if "engine" in render_settings:
                bpy.context.scene.render.engine = render_settings["engine"]
            if bpy.context.scene.render.engine == "CYCLES":
                if "device" in render_settings:
                    bpy.context.scene.cycles.device = render_settings["device"]
                if "samples" in render_settings:
                    bpy.context.scene.cycles.samples = render_settings["samples"]

        self.cleanup_callback = restore_originals

        texture_names = []
        submeshes_to_bake = []
        for submesh in flver_submeshes:
            if not submesh.active_material:
                return self.error(f"Submesh '{submesh.name}' has no active material.")

            bl_material = submesh.active_material
            if "material_mtd_path" not in bl_material.__dict__:
                return self.error(
                    f"Submesh '{submesh.name}' material '{bl_material.name}' has no 'material_mtd_path' custom prop "
                    f"(required by FLVER plugin)."
                )

            # Find Image Texture node of lightmap and its UV layer input.
            for node in bl_material.node_tree.nodes:
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

                    mtd_name = Path(bl_material["material_mtd_path"]).name
                    if options.bake_rendered_only and submesh.hide_render:
                        self.info(
                            f"Bake will NOT include material '{bl_material.name}' of submesh '{submesh.name}' that "
                            f"is hidden from rendering."
                        )
                    if "[We]" in mtd_name:
                        self.info(
                            f"Bake will NOT include material '{bl_material.name}' of submesh '{submesh.name}' with "
                            f"[We] water shader: {mtd_name}."
                        )
                    elif not options.bake_edge_shaders and "_Edge" in mtd_name:
                        self.info(
                            f"Bake will NOT include material '{bl_material.name}' of submesh '{submesh.name}' with "
                            f"'Edge' type shader: {mtd_name}."
                        )
                    else:
                        submeshes_to_bake.append(submesh)
                    break
            else:
                self.warning(
                    f"Could not find a `g_Lightmap` texture in active material of mesh '{submesh.name}'. "
                    f"Ignoring submesh."
                )

        if not texture_names or not submeshes_to_bake:
            return self.error("No lightmap textures found to bake into.")

        # Select all submeshes to be baked (and only them).
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = submeshes_to_bake[0]  # just in case
        for submesh in submeshes_to_bake:
            submesh.select_set(True)

        # Bake with Cycles.
        render_settings = {
            "engine": bpy.context.scene.render.engine,
        }
        bpy.context.scene.render.engine = "CYCLES"
        render_settings |= {
            "device": bpy.context.scene.cycles.device,
            "samples": bpy.context.scene.cycles.samples,
        }
        bpy.context.scene.cycles.device = options.bake_device
        bpy.context.scene.cycles.samples = options.bake_samples
        bpy.ops.object.bake(type="SHADOW", margin=options.bake_margin, use_selected_to_active=False)
        self.info(f"Baked {len(texture_names)} lightmap textures: {', '.join(texture_names)}")
        try:
            self.cleanup_callback()
        except Exception as ex:
            self.warning(f"Error during cleanup callback after operation finished: {ex}")
        return {"FINISHED"}


class ExportLightmapTextures(LoggingOperator, ImportHelper):
    bl_idname = "export_image.lightmaps"
    bl_label = "Export FLVER Lightmaps"
    bl_description = (
        "Export lightmap image textures from all materials of all selected FLVERs into a FromSoftware TPF/Binder "
        "(usually a `.tpfbhd` Binder in `mAA` folder)"
    )

    filename_ext = ".tpfbhd"

    filter_glob: bpy.props.StringProperty(
        default="*.tpf;*.tpf.dcx;*.tpfbhd;*.chrbnd;*.chrbnd.dcx;*.objbnd;*.objbnd.dcx;*.partsbnd;*.partsbnd.dcx",
        options={'HIDDEN'},
        maxlen=255,
    )

    create_new_if_missing: bpy.props.BoolProperty(
        name="Create New TPF If Missing",
        description="If enabled, exporter will create a new TPF using default DS1 lightmap settings if an existing "
                    "TPF is not found (TPFBHD files only). Disable for safety if you expect to replace an existing "
                    "lightmap",
        default=True,
    )

    new_texture_dds_format: bpy.props.StringProperty(
        name="New Texture DDS Format",
        description="DDS format to use for any newly created TPFs. Default is suitable for Dark Souls 1",
        default="BC7_UNORM",
    )

    new_tpf_dcx_type: bpy.props.EnumProperty(
        name="New TPF Compression",
        items=[
            ("Null", "None", "Export without any DCX compression"),
            ("DCX_EDGE", "DES", "Demon's Souls compression"),
            ("DCX_DFLT_10000_24_9", "DS1/DS2", "Dark Souls 1/2 compression"),
            ("DCX_DFLT_10000_44_9", "BB/DS3", "Bloodborne/Dark Souls 3 compression"),
            ("DCX_DFLT_11000_44_9", "Sekiro", "Sekiro compression (requires Oodle DLL)"),
            ("DCX_KRAK", "Elden Ring", "Elden Ring compression (requires Oodle DLL)"),
        ],
        default="DCX_DFLT_10000_24_9",
        description="Type of DCX compression to apply to any newly created TPFs. Default is suitable for Dark Souls 1 "
                    "map textures going into TPFBHD Binders"
    )

    @classmethod
    def poll(cls, context):
        """FLVER armature(s) must be selected."""
        return context.selected_objects and all(obj.type == "ARMATURE" for obj in context.selected_objects)

    def execute(self, context):
        print("Executing lightmap texture export...")

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

        for bl_image in bl_images:
            if not bl_image:
                self.warning("Ignoring Image Texture node with no image assigned.")
                continue
            image_stem = Path(bl_image.name).stem
            image_exported, dds_format = texture_export_info.inject_texture(
                bl_image, image_stem, image_stem, rename_tpf=False
            )
            if image_exported:
                self.info(f"Exported '{bl_image.name}' into '{self.filepath}' with DDS format {dds_format}")
            elif self.create_new_if_missing:
                if isinstance(texture_export_info, SplitBinderTPFTextureExport):
                    new_tpf = get_lightmap_tpf(bl_image, dds_format=self.new_texture_dds_format)
                    new_tpf.dcx_type = DCXType[self.new_tpf_dcx_type]
                    new_tpf_entry_path = Path(bl_image.name).name + ".tpf"
                    if new_tpf.dcx_type != DCXType.Null:
                        new_tpf_entry_path += ".dcx"
                    texture_export_info.chrtpfbxf.add_entry(
                        texture_export_info.chrtpfbxf.BinderEntry(
                            data=new_tpf.pack_dcx(),
                            entry_id=texture_export_info.chrtpfbxf.highest_entry_id + 1,
                            path=new_tpf_entry_path,
                            flags=0x2,  # TODO: DS1 default
                        )
                    )
                else:
                    self.warning(
                        f"Could not find any TPF textures to replace with Blender image (and new TPF creation not "
                        f"supported for export to existing BND/TPF): '{image_stem}'"
                    )

            else:
                self.warning(
                    f"Could not find any TPF textures to replace with Blender image (and new TPF creation is "
                    f"disabled): '{image_stem}'"
                )

        # TPFs have all been updated. Now pack modified ones back to their Binders.
        try:
            write_msg = texture_export_info.write_files()
        except Exception as ex:
            return self.error(str(ex))

        self.info(write_msg)
        return {"FINISHED"}

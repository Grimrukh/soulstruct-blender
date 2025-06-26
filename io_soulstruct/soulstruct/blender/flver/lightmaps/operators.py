from __future__ import annotations

__all__ = [
    "BakeLightmapSettings",
    "BakeLightmapTextures",
]

import typing as tp
from pathlib import Path

import bpy

from soulstruct.base.models.mtd import MTDBND
from soulstruct.darksouls1r.models.shaders import MatDef as DS1R_MatDef
from soulstruct.games import DARK_SOULS_DSR

from soulstruct.blender.bpy_base.property_group import SoulstructPropertyGroup
from soulstruct.blender.exceptions import SoulstructTypeError
from soulstruct.blender.flver.material.types import BlenderFLVERMaterial
from soulstruct.blender.flver.models.types import BlenderFLVER
from soulstruct.blender.utilities import LoggingOperator


class BakeLightmapSettings(SoulstructPropertyGroup):

    # Currently only for DSR.
    GAME_PROP_NAMES = {
        DARK_SOULS_DSR: (),  # all properties are supported
    }

    uv_layer_name: bpy.props.StringProperty(
        name="UV Layer Name",
        description="Name of UV layer to use for baking (leave empty to use active UV layer)",
        default="UVLightmap",
    )

    texture_node_name: bpy.props.StringProperty(
        name="Texture Node Name",
        description="Name of texture node to search for when choosing image to bake into. Unlikely to change",
        default="g_Lightmap",
    )

    bake_image_size: bpy.props.IntProperty(
        name="Bake Image Size",
        description="Size of image texture to bake (0 = use existing texture size)",
        default=512,  # NOTE: default is twice the original DS1 lightmap size of 256x256
    )

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
        description="Number of Cycles render samples to use while baking (determines quality)",
        default=128,
    )

    bake_margin: bpy.props.IntProperty(
        name="Bake Margin",
        description="Texture margin (in pixels) for 'UV islands' in bake",
        default=0,
    )

    bake_edge_shaders: bpy.props.BoolProperty(
        name="Bake Edge Shaders",
        description="If disabled, meshes with 'Edge'-type materials (which are often decals) will not affect the bake "
                    "render (but may still use lightmaps in their materials)",
        default=False,
    )

    bake_rendered_only: bpy.props.BoolProperty(
        name="Bake Render-Enabled Only",
        description="If enabled, only meshes with render visibility enabled (camera icon) will affect the bake render",
        default=False,
    )


class BakeLightmapTextures(LoggingOperator):

    bl_idname = "bake.lightmaps"
    bl_label = "Bake FLVER Lightmaps"
    bl_description = "Bake rendered lightmap image textures from all materials of all selected FLVERs"

    @classmethod
    def poll(cls, context) -> bool:
        """FLVER meshes must be selected."""
        try:
            BlenderFLVER.from_selected_objects(context)
        except SoulstructTypeError:
            return False
        return True

    def execute(self, context):
        """
        TODO: Fix up.
            - Remember, a bake operation will use ALL visible geometry and bake the result into a selected Image using
            the active UV layer and all SELECTED meshes (materials?).
            - No need to select lightmap textures. Just look for 'g_Lightmap' texture nodes.
                - Check that the input UV name for these matches the UV layer name in bake settings.
                - Temporarily disable the output strength of these nodes during new bake.
            - To exclude 'Edge' materials, we need to temporarily convert those materials' shaders to Holdout, to
            essentially erase those faces from the rendered scene. Or disable the output node or whatever is easiest.
        """
        self.info("Baking FLVER lightmap textures...")

        mat_settings = context.scene.flver_material_settings
        mtdbnd = mat_settings.get_mtdbnd(self, context)
        bake_settings = context.scene.bake_lightmap_settings

        bl_flvers = BlenderFLVER.from_selected_objects(context, sort=True)  # type: list[BlenderFLVER]

        # Set up variables/function to restore original state after bake.
        original_lightmap_strengths = []  # pairs of `(node, value)`
        render_settings = {}

        def restore_originals():
            # NOTE: Does NOT restore old active UV layer, as you most likely want to immediately see the bake result
            # in the Image Viewer.
            for _node, _strength in original_lightmap_strengths:
                _node.inputs["Fac"].default_value = _strength
            # Restore render settings.
            if "engine" in render_settings:
                context.scene.render.engine = render_settings["engine"]
            if context.scene.render.engine == "CYCLES":
                if "device" in render_settings:
                    context.scene.cycles.device = render_settings["device"]
                if "samples" in render_settings:
                    context.scene.cycles.samples = render_settings["samples"]

        self.cleanup_callback = restore_originals

        target_image = None  # type: bpy.types.Image | None
        for bl_flver in bl_flvers:

            for material_slot in bl_flver.mesh.material_slots:
                material_target_image = self.parse_flver_material(
                    bl_flver,
                    material_slot,
                    mtdbnd,
                    bake_settings,
                    original_lightmap_strengths,
                    assert_lightmap_image=target_image,
                )
                if material_target_image:
                    target_image = material_target_image

        if target_image is None:  # don't think this can happen
            return self.error("No lightmap textures found to bake into.")

        # We already know that only the meshes to be baked are currently selected.

        try:
            self.bake(context, bake_settings, render_settings)
        except Exception as ex:
            try:
                self.cleanup_callback()
            except Exception as ex2:
                self.warning(f"Error during cleanup callback after Bake Lightmap operation failed: {ex2}")
            return self.error(f"Error occurred during Cycles bake operation: {ex}")

        self.info(f"Baked lightmap texture for {len(bl_flvers)} FLVERs: {target_image.name}")
        try:
            self.cleanup_callback()
        except Exception as ex:
            self.warning(f"Error during cleanup callback after Bake Lightmap operation succeeded: {ex}")

        return {"FINISHED"}

    def parse_flver_material(
        self,
        bl_flver: BlenderFLVER,
        material_slot: bpy.types.MaterialSlot,
        mtdbnd: MTDBND,
        bake_settings: BakeLightmapSettings,
        original_lightmap_strengths: list[tuple[bpy.types.Node, float]],
        assert_lightmap_image: bpy.types.Image = None,
    ) -> bpy.types.Image:
        """Ensures that the appropriate lightmap texture node is selected and that the appropriate UV layer is active.

        Depending on `bake_settings`, this material may be temporarily 'disabled' by modifying its shader nodes, so that
        it does not cast shadows that affect baking (e.g. 'Edge' decals, water, render-hidden meshes). However, it will
        still be a bake TARGET and will have its lightmap data written.

        TODO: Non-selected meshes that aren't bake targets will still cast shadows from their water, Edge decals, etc.
         Operator might need to check every material in the scene and temporarily disable these shaders!

        Returns the name of the Blender image assigned to the lightmap texture node. The caller will ensure that all
        selected meshes/materials are using the same lightmap texture. If no lightmap texture node is found, an error
        will be raised, to ensure that the user is fully aware of what meshes they are trying to bake.
        """
        mesh = bl_flver.mesh
        bl_material = BlenderFLVERMaterial(material_slot.material)
        if not bl_material.mat_def_path:
            raise ValueError(f"Material '{bl_material.name}' of mesh {mesh.name} has no MTD path set.")
        mtd_name = Path(bl_material.mat_def_path).name
        matdef = DS1R_MatDef.from_mtdbnd_or_name(mtd_name, mtdbnd)

        texture_node_name = bake_settings.texture_node_name

        try:
            # noinspection PyTypeChecker
            lightmap_node = bl_material.node_tree.nodes[texture_node_name]
        except KeyError:
            raise ValueError(
                f"Material '{bl_material.name}' of mesh {mesh.name} has no texture node named '{texture_node_name}'."
            )
        if lightmap_node.type != "TEX_IMAGE":
            raise ValueError(
                f"Material '{bl_material.name}' of mesh {mesh.name} has a node named '{texture_node_name}', but it is "
                f"not an Image Texture node."
            )
        lightmap_node: bpy.types.ShaderNodeTexImage

        lightmap_image = lightmap_node.image
        if not lightmap_image:
            raise ValueError(
                f"Material '{bl_material.name}' of mesh {mesh.name} has no image assigned to its "
                f"'{texture_node_name}' texture node."
            )
        if lightmap_image.name != assert_lightmap_image.name:
            raise ValueError(
                f"Material '{bl_material.name}' of mesh {mesh.name} has image '{lightmap_image.name}' assigned to its "
                f"'{texture_node_name}' texture node, but '{assert_lightmap_image.name}' was expected."
            )

        # Activate and select lightmap texture for bake target of this mesh/material.
        bl_material.node_tree.nodes.active = lightmap_node
        lightmap_node.select = True

        # Activate UV layer used by lightmap.
        try:
            uv_name = lightmap_node.inputs["Vector"].links[0].from_node.attribute_name
        except (AttributeError, IndexError):
            raise ValueError(
                f"Could not find UVMap attribute for '{texture_node_name}' texture node in material "
                f"'{bl_material.name}' of mesh {mesh.name}."
            )
        mesh.data.uv_layers[uv_name].active = True

        # Set overlay values to zero while baking - we don't want the existing lightmap to affect the bake!
        try:
            overlay_node = lightmap_node.outputs["Color"].links[0].to_node
            overlay_node_fac = overlay_node.inputs["Fac"]
        except (AttributeError, IndexError):
            self.warning(
                f"Could not find `MixRGB` node connected to output of '{texture_node_name}' node "
                f"in material '{bl_material.name}' of mesh {mesh.name}. Will not modify this shader for new bake!"
            )
        else:
            original_lightmap_strengths.append((overlay_node, overlay_node_fac.default_value))
            # Detect which mix slot lightmap is using and set factor to disable lightmap while baking.
            if overlay_node.inputs[1].links[0].from_node == lightmap_node:  # input 1
                overlay_node_fac.default_value = 1.0
            else:  # input 2 (expected)
                overlay_node_fac.default_value = 0.0

        if bake_settings.bake_rendered_only and mesh.hide_render:
            self.info(
                f"Bake render will NOT include material '{bl_material.name}' of mesh {mesh.name} that "
                f"is hidden from rendering."
            )

        if matdef.is_water:
            self.info(
                f"Bake will NOT include material '{bl_material.name}' of mesh {mesh.name} with "
                f"water MTD shader: {mtd_name}"
            )
        elif not bake_settings.bake_edge_shaders and matdef.edge:
            self.info(
                f"Bake will NOT include material '{bl_material.name}' of mesh {mesh.name} with "
                f"'Edge' MTD shader: {mtd_name}"
            )

        return lightmap_image

    @staticmethod
    def bake(context, bake_settings: BakeLightmapSettings, render_settings: dict[str, tp.Any]):
        """Perform SHADOW bake operation with Cycles.

        Also modifies a dict of render settings that were changed during the bake, so that they can be restored later.
        """
        render_settings |= {
            "engine": context.scene.render.engine,
        }
        context.scene.render.engine = "CYCLES"
        render_settings |= {
            "device": context.scene.cycles.device,
            "samples": context.scene.cycles.samples,
        }
        context.scene.cycles.device = bake_settings.bake_device
        context.scene.cycles.samples = bake_settings.bake_samples
        bpy.ops.object.bake(type="SHADOW", margin=bake_settings.bake_margin, use_selected_to_active=False)

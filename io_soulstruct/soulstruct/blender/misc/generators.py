"""Operators that generate convenient types of primitive meshes, mostly for FLVER modeling."""
from __future__ import annotations

__all__ = [
    "GenerateRock",
    "GenerateBrick",
    "GenerateSlab",
]

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

from ..base.operators import LoggingOperator
from ..base.register import io_soulstruct_class
from ..types import MeshObject


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _cursor_local(obj: MeshObject, context: bpy.types.Context) -> Vector:
    """Return the 3D cursor position in the object's local space."""
    return obj.matrix_world.inverted() @ context.scene.cursor.location


def _deselect_bmesh(bm: bmesh.types.BMesh) -> None:
    for v in bm.verts:
        v.select = False
    for e in bm.edges:
        e.select = False
    for f in bm.faces:
        f.select = False


def _faces_of_verts(verts) -> set:
    """Collect all BMFaces touching any of the given BMVerts."""
    faces = set()
    for v in verts:
        for f in v.link_faces:
            faces.add(f)
    return faces


def _assign_active_material(obj: MeshObject, faces) -> None:
    idx = obj.active_material_index or 0
    for f in faces:
        f.material_index = idx


def _select_geometry(verts, faces) -> None:
    for v in verts:
        v.select = True
    for f in faces:
        f.select = True


def _assign_vertex_group(obj: MeshObject, vg_name: str, vert_indices: list[int]) -> None:
    """Create-or-get a vertex group and assign all indices at weight 1 (requires object mode round-trip)."""
    vg = obj.vertex_groups.get(vg_name)
    if vg is None:
        vg = obj.vertex_groups.new(name=vg_name)
    bpy.ops.object.mode_set(mode="OBJECT")
    vg.add(vert_indices, 1.0, "REPLACE")
    bpy.ops.object.mode_set(mode="EDIT")


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

@io_soulstruct_class
class GenerateRock(LoggingOperator):
    bl_idname = "mesh.generate_rock"
    bl_label = "Generate Rock"
    bl_description = (
        "Spawn an icosphere or subdivided cube at the 3D cursor in Edit Mode, assign it to a vertex group, and set "
        "up a Displace modifier using global noise coordinates so that each rock's position gives it a unique shape"
    )

    base_shape: bpy.props.EnumProperty(
        name="Base Shape",
        description="Starting primitive — determines the overall character of the rock",
        items=[
            ("ICOSPHERE", "Icosphere", "Smooth sphere base — rounded, organic rocks"),
            ("CUBE", "Cube", "Subdivided cube base — angular, blocky, cliff-like rocks"),
        ],
        default="ICOSPHERE",
    )
    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Radius (icosphere) or half-size (cube) of the base primitive",
        default=0.5,
        min=0.01,
    )
    subdivisions: bpy.props.IntProperty(
        name="Subdivisions",
        description="Icosphere subdivision level (higher = more displacement detail)",
        default=2,
        min=1,
        max=6,
    )
    cube_subdivisions: bpy.props.IntProperty(
        name="Cube Subdivisions",
        description="Edge cuts applied to the cube before displacement (0 = sharp box, 2–3 = increasingly rounded)",
        default=2,
        min=0,
        max=5,
    )
    vertex_group: bpy.props.StringProperty(
        name="Vertex Group",
        description="Vertex group to assign and use as the Displace modifier mask (created if absent)",
        default="rock",
    )
    scale_x: bpy.props.FloatProperty(name="Scale X", default=1.0, min=0.01)
    scale_y: bpy.props.FloatProperty(name="Scale Y", default=1.0, min=0.01)
    scale_z: bpy.props.FloatProperty(
        name="Scale Z",
        description="Z scale relative to radius (use < 1 for flat rocks)",
        default=0.7,
        min=0.01,
    )
    displace_strength: bpy.props.FloatProperty(
        name="Displace Strength",
        description="Strength of the Displace modifier",
        default=0.1,
        min=0.0,
    )
    noise_scale: bpy.props.FloatProperty(
        name="Noise Scale",
        description="Scale of the noise texture (larger = bigger displacement features)",
        default=1.0,
        min=0.01,
    )
    uv_strategy: bpy.props.EnumProperty(
        name="UV Strategy",
        description="How to UV-unwrap the new rock faces",
        items=[
            ("CUBE", "Cube Projection",
             "Project UVs from 6 cube faces — best for tiling rock textures with minimal distortion"),
            ("SPHERE", "Sphere Projection",
             "Mathematical sphere projection — works well for smooth, round rocks"),
            ("EQUATOR_SEAM", "Unwrap (Equator Seam)",
             "Mark the lower boundary of the equatorial face band as a seam, then angle-based unwrap — "
             "clean two-hemisphere UV layout"),
            ("SMART", "Smart UV Project",
             "Automatic island-based unwrap — good for heavily scaled or irregular rocks"),
            ("NONE", "None",
             "Skip UV unwrapping entirely (e.g. for triplanar shaders)"),
        ],
        default="EQUATOR_SEAM",
    )

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.mode == "EDIT_MESH"
            and context.edit_object is not None
            and context.edit_object.type == "MESH"
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        if not layout:
            return

        layout.prop(self, "base_shape")
        layout.prop(self, "radius")
        if self.base_shape == "ICOSPHERE":
            layout.prop(self, "subdivisions")
        else:
            layout.prop(self, "cube_subdivisions")
        layout.prop(self, "vertex_group")
        layout.separator()
        layout.label(text="Shape:")
        layout.prop(self, "scale_x")
        layout.prop(self, "scale_y")
        layout.prop(self, "scale_z")
        layout.separator()
        layout.label(text="Displace Modifier:")
        layout.prop(self, "displace_strength")
        layout.prop(self, "noise_scale")
        layout.separator()
        layout.prop(self, "uv_strategy")

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: MeshObject
        mesh = obj.data
        vg_name = self.vertex_group

        bm = bmesh.from_edit_mesh(mesh)
        _deselect_bmesh(bm)

        cursor_local = _cursor_local(obj, context)
        orig_vert_count = len(bm.verts)

        # --- 1. Create base primitive ---
        if self.base_shape == "ICOSPHERE":
            bmesh.ops.create_icosphere(
                bm,
                subdivisions=self.subdivisions,
                radius=self.radius,
                matrix=Matrix.Translation(cursor_local),
                calc_uvs=False,
            )
        else:  # CUBE
            bmesh.ops.create_cube(
                bm,
                size=self.radius * 2.0,
                matrix=Matrix.Translation(cursor_local),
                calc_uvs=False,
            )
            if self.cube_subdivisions > 0:
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                cube_edges = [
                    e for e in bm.edges
                    if all(v.index >= orig_vert_count for v in e.verts)
                ]
                bmesh.ops.subdivide_edges(
                    bm,
                    edges=cube_edges,
                    cuts=self.cube_subdivisions,
                    use_single_edge=False,
                    use_grid_fill=True,
                )

        bm.verts.ensure_lookup_table()
        new_verts = list(bm.verts[orig_vert_count:])
        new_faces = _faces_of_verts(new_verts)

        if not new_verts:
            return self.error("Primitive creation produced no new vertices.")

        # --- 2. Non-uniform scale around cursor ---
        for v in new_verts:
            offset = v.co - cursor_local
            offset.x *= self.scale_x
            offset.y *= self.scale_y
            offset.z *= self.scale_z
            v.co = cursor_local + offset

        _assign_active_material(obj, new_faces)

        # --- 3. UV unwrap ---
        _select_geometry(new_verts, new_faces)
        new_vert_set = set(new_verts)

        if self.uv_strategy == "EQUATOR_SEAM":
            # Mark the lower boundary of the equatorial face band as a seam:
            # edges where both verts are at-or-below the equator but at least one
            # neighbouring face reaches above it.  Produces a clean horizontal loop.
            eq_z = cursor_local.z
            eps = 1e-6
            for e in bm.edges:
                if e.verts[0] not in new_vert_set or e.verts[1] not in new_vert_set:
                    continue
                if e.verts[0].co.z > eq_z + eps or e.verts[1].co.z > eq_z + eps:
                    continue
                if any(v.co.z > eq_z + eps for f in e.link_faces for v in f.verts):
                    e.seam = True

        bmesh.update_edit_mesh(mesh)

        if self.uv_strategy == "CUBE":
            bpy.ops.uv.cube_project(correct_aspect=True, scale_to_bounds=False)
        elif self.uv_strategy == "SPHERE":
            bpy.ops.uv.sphere_project(correct_aspect=True, clip_to_bounds=False, scale_to_bounds=True)
        elif self.uv_strategy == "EQUATOR_SEAM":
            bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)
        elif self.uv_strategy == "SMART":
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02, scale_to_bounds=False)
        # NONE: skip

        # --- 4. Vertex group ---
        _assign_vertex_group(obj, vg_name, [v.index for v in new_verts])

        # --- 5. Displace modifier + noise texture ---
        texture_name = vg_name
        tex = bpy.data.textures.get(texture_name)
        if tex is None:
            tex = bpy.data.textures.new(name=texture_name, type="DISTORTED_NOISE")
            tex.noise_scale = self.noise_scale
            tex.distortion = 1.0
            tex.noise_basis = "BLENDER_ORIGINAL"
            tex.noise_distortion = "BLENDER_ORIGINAL"
            self.info(f"Created Distorted Noise texture '{texture_name}'.")
        else:
            self.info(f"Reusing existing texture '{texture_name}'.")

        displace_mod = next(
            (m for m in obj.modifiers if m.type == "DISPLACE" and m.vertex_group == vg_name),
            None,
        )
        if displace_mod is None:
            displace_mod = obj.modifiers.new(name=f"Displace_{vg_name}", type="DISPLACE")
            displace_mod.texture = tex
            displace_mod.vertex_group = vg_name
            displace_mod.texture_coords = "GLOBAL"
            displace_mod.strength = self.displace_strength
            displace_mod.direction = "NORMAL"
            displace_mod.show_on_cage = True
            displace_mod.show_in_editmode = True
            self.info(f"Created Displace modifier 'Displace_{vg_name}'.")
        else:
            self.info(f"Reusing existing Displace modifier for vertex group '{vg_name}'.")

        self.info(
            f"{self.base_shape} rock spawned at cursor, vertex group '{vg_name}'."
        )
        return {"FINISHED"}


@io_soulstruct_class
class GenerateBrick(LoggingOperator):
    bl_idname = "mesh.generate_brick"
    bl_label = "Generate Brick"
    bl_description = (
        "Spawn a bevelled rectangular brick at the 3D cursor in Edit Mode. Edges are chamfered and each vertex is "
        "randomly displaced along its normal to give subtle surface roughness. UVs are cube-projected."
    )

    width: bpy.props.FloatProperty(
        name="Width", description="X extent of the brick", default=0.4, min=0.01,
    )
    height: bpy.props.FloatProperty(
        name="Height", description="Y extent of the brick (depth into wall)", default=0.2, min=0.01,
    )
    depth: bpy.props.FloatProperty(
        name="Depth", description="Z extent of the brick", default=0.18, min=0.01,
    )
    bevel_amount: bpy.props.FloatProperty(
        name="Bevel Amount",
        description="Size of the chamfered corners. 0 = sharp box",
        default=0.015,
        min=0.0,
    )
    bevel_segments: bpy.props.IntProperty(
        name="Bevel Segments",
        description="Edge loops in the bevel (1 = single chamfer, 2+ = rounded)",
        default=1,
        min=1,
        max=4,
    )
    surface_noise: bpy.props.FloatProperty(
        name="Surface Noise",
        description="Maximum random displacement of each vertex along its normal (subtle stone roughness)",
        default=0.008,
        min=0.0,
    )
    uv_tile_size: bpy.props.FloatProperty(
        name="UV Tile Size",
        description=(
            "World-space size (in metres) that maps to one full texture repeat on the side faces. "
            "Smaller = more tiling. Set to roughly the width of your brick texture's real-world content"
        ),
        default=0.4,
        min=0.001,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.mode == "EDIT_MESH"
            and context.edit_object is not None
            and context.edit_object.type == "MESH"
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: MeshObject
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)
        _deselect_bmesh(bm)

        cursor_local = _cursor_local(obj, context)
        orig_vert_count = len(bm.verts)

        # --- 1. Create unit cube at cursor, then scale verts to brick dimensions ---
        # A unit cube (size=1.0) has verts at ±0.5, so multiplying the offset by the
        # desired dimension gives verts at ±dim/2, i.e. total extent = dim.
        bmesh.ops.create_cube(
            bm, size=1.0, matrix=Matrix.Translation(cursor_local), calc_uvs=False,
        )

        bm.verts.ensure_lookup_table()
        new_verts = list(bm.verts[orig_vert_count:])
        new_vert_set = set(new_verts)

        for v in new_verts:
            offset = v.co - cursor_local
            offset.x *= self.width
            offset.y *= self.height
            offset.z *= self.depth
            v.co = cursor_local + offset

        # --- 2. Bevel all new edges ---
        if self.bevel_amount > 0.0:
            new_edges = [e for e in bm.edges if all(v in new_vert_set for v in e.verts)]
            bmesh.ops.bevel(
                bm,
                geom=new_edges,
                offset=self.bevel_amount,
                offset_type="OFFSET",
                segments=self.bevel_segments,
                profile=0.5,
                affect="EDGES",
            )
            # Re-collect: bevel creates additional vertices.
            bm.verts.ensure_lookup_table()
            new_verts = list(bm.verts[orig_vert_count:])
            new_vert_set = set(new_verts)

        new_faces = _faces_of_verts(new_verts)

        # --- 3. Random surface noise along vertex normals ---
        if self.surface_noise > 0.0:
            bm.normal_update()
            for v in new_verts:
                v.co += v.normal * random.uniform(-self.surface_noise, self.surface_noise)

        _assign_active_material(obj, new_faces)

        # --- 4. Seams + two-phase UV ---
        # Identify the single top and bottom cap faces (most extreme centre Z).
        sorted_by_z = sorted(new_faces, key=lambda f: f.calc_center_median().z)
        cap_faces = {sorted_by_z[0], sorted_by_z[-1]}   # bottom cap, top cap
        side_faces = new_faces - cap_faces

        # Mark seams on every edge that borders a cap face and a non-cap face so
        # the cap islands are cleanly separated from the side/bevel island.
        for cap_face in cap_faces:
            for edge in cap_face.edges:
                if any(lf not in cap_faces for lf in edge.link_faces):
                    edge.seam = True

        # Cap faces → flat angle-based unwrap (clean rectangular island).
        _deselect_bmesh(bm)
        for f in cap_faces:
            f.select = True
            for v in f.verts:
                v.select = True
        bmesh.update_edit_mesh(mesh)
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)

        # Side + bevel faces → cube projection with user-controlled tiling scale.
        _deselect_bmesh(bm)
        for f in side_faces:
            f.select = True
            for v in f.verts:
                v.select = True
        bmesh.update_edit_mesh(mesh)
        bpy.ops.uv.cube_project(cube_size=self.uv_tile_size, correct_aspect=True, scale_to_bounds=False)

        self.info(
            f"Brick spawned at cursor "
            f"({self.width:.3f} × {self.height:.3f} × {self.depth:.3f})."
        )
        return {"FINISHED"}


@io_soulstruct_class
class GenerateSlab(LoggingOperator):
    bl_idname = "mesh.generate_slab"
    bl_label = "Generate Slab"
    bl_description = (
        "Spawn a flat polygonal stone slab (flagstone / cobblestone) at the 3D cursor in Edit Mode. "
        "The rim vertices are randomly pushed/pulled for an irregular outline, and the surface has baked-in Z noise."
    )

    radius: bpy.props.FloatProperty(
        name="Radius", description="Approximate radius of the slab", default=0.6, min=0.05,
    )
    thickness: bpy.props.FloatProperty(
        name="Thickness", description="Height (Z extent) of the slab", default=0.12, min=0.01,
    )
    segments: bpy.props.IntProperty(
        name="Segments",
        description="Number of sides: 6–8 for angular flagstones, 10–16 for rounder cobblestones",
        default=8,
        min=3,
        max=32,
    )
    perimeter_irregularity: bpy.props.FloatProperty(
        name="Perimeter Irregularity",
        description="Random radial push/pull applied independently to each rim edge (intentionally jagged)",
        default=0.18,
        min=0.0,
    )
    perimeter_tilt: bpy.props.FloatProperty(
        name="Perimeter Tilt",
        description=(
            "Smoothly varying radial delta between the top and bottom vertex of each rim edge, giving the "
            "side faces a natural lean/taper. Uses sinusoidal harmonics so it is always smooth and periodic"
        ),
        default=0.08,
        min=0.0,
    )
    surface_noise: bpy.props.FloatProperty(
        name="Surface Noise",
        description="Maximum random Z displacement on rim vertices, giving an uneven top/bottom surface",
        default=0.025,
        min=0.0,
    )

    @classmethod
    def poll(cls, context) -> bool:
        return (
            context.mode == "EDIT_MESH"
            and context.edit_object is not None
            and context.edit_object.type == "MESH"
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # noinspection PyTypeChecker
        obj = context.edit_object  # type: MeshObject
        mesh = obj.data

        bm = bmesh.from_edit_mesh(mesh)
        _deselect_bmesh(bm)

        cursor_local = _cursor_local(obj, context)
        orig_vert_count = len(bm.verts)

        # --- 1. Create cylinder with n-gon caps ---
        # cap_tris=False → n-gon caps, no centre pole vertex.  With equal radii all new
        # verts are rim verts at z = cursor_z ± thickness/2, so perimeter ops are simple.
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=self.segments,
            radius1=self.radius,
            radius2=self.radius,
            depth=self.thickness,
            matrix=Matrix.Translation(cursor_local),
            calc_uvs=False,
        )

        bm.verts.ensure_lookup_table()
        new_verts = list(bm.verts[orig_vert_count:])

        if not new_verts:
            return self.error("Slab creation produced no new vertices.")

        # --- 2. Perimeter irregularity + smooth tilt + surface noise ---
        # Split the new verts into top and bottom rings and sort each by angle so they
        # can be paired: the i-th top vert and i-th bottom vert share the same edge.
        eps = 1e-6
        mid_z = cursor_local.z
        top_verts = sorted(
            [v for v in new_verts if v.co.z > mid_z],
            key=lambda v: math.atan2(v.co.y - cursor_local.y, v.co.x - cursor_local.x),
        )
        bottom_verts = sorted(
            [v for v in new_verts if v.co.z <= mid_z],
            key=lambda v: math.atan2(v.co.y - cursor_local.y, v.co.x - cursor_local.x),
        )

        # Independent random base push per edge — intentionally jagged for a rough outline.
        base_pushes = [
            random.uniform(-self.perimeter_irregularity, self.perimeter_irregularity) * self.radius
            for _ in range(len(top_verts))
        ]

        # Smooth tilt delta using summed sinusoidal harmonics over θ.  The top vert gets
        # +tilt and the bottom vert gets -tilt, so the side face leans naturally without
        # kinking.  Sinusoids are periodic so there is no seam at θ = ±π.
        tilt_harmonics = [
            (random.uniform(0.0, 2.0 * math.pi), random.uniform(-1.0, 1.0))
            for _ in range(3)
        ]

        for i, (tv, bv) in enumerate(zip(top_verts, bottom_verts)):
            theta = math.atan2(tv.co.y - cursor_local.y, tv.co.x - cursor_local.x)
            base_push = base_pushes[i]
            tilt = (
                sum(amp * math.sin((k + 1) * theta + phase)
                    for k, (phase, amp) in enumerate(tilt_harmonics))
                / 3.0 * self.perimeter_tilt * self.radius
            )
            for v, sign in ((tv, +1.0), (bv, -1.0)):
                dx = v.co.x - cursor_local.x
                dy = v.co.y - cursor_local.y
                r = math.sqrt(dx * dx + dy * dy)
                if r > eps:
                    push = base_push + sign * tilt
                    v.co.x += dx / r * push
                    v.co.y += dy / r * push
                if self.surface_noise > 0.0:
                    v.co.z += random.uniform(-self.surface_noise, self.surface_noise)

        new_faces = _faces_of_verts(new_verts)
        _assign_active_material(obj, new_faces)

        # --- 3. Seams + two-phase UV ---
        # Identify the single top and bottom cap faces (most extreme centre Z).
        sorted_by_z = sorted(new_faces, key=lambda f: f.calc_center_median().z)
        cap_faces = {sorted_by_z[0], sorted_by_z[-1]}
        side_faces = new_faces - cap_faces

        # Mark seams on edges where cap faces meet side faces.
        for cap_face in cap_faces:
            for edge in cap_face.edges:
                if any(lf not in cap_faces for lf in edge.link_faces):
                    edge.seam = True

        # Triangulate side faces before UV unwrapping.  After perimeter irregularity and
        # Z noise the side quads are frequently non-planar, which causes shading artefacts
        # and export issues. Cap n-gons stay as-is (the user can triangulate those later
        # or the exporter will handle it). SHORT_EDGE tends to produce the best
        # result for irregular quads; the op replaces the originals with tris in-place.
        bmesh.ops.triangulate(
            bm,
            faces=list(side_faces),
            quad_method="SHORT_EDGE",
            ngon_method="BEAUTY",
        )
        bm.faces.ensure_lookup_table()
        # Re-collect side faces: the original quads are gone, replaced by tris.
        side_faces = _faces_of_verts(new_verts) - cap_faces

        # Cap faces → flat unwrap (top and bottom as separate clean islands).
        _deselect_bmesh(bm)
        for f in cap_faces:
            f.select = True
            for v in f.verts:
                v.select = True
        bmesh.update_edit_mesh(mesh)
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)

        # Side faces → unwrap as a single perimeter strip island.
        _deselect_bmesh(bm)
        for f in side_faces:
            f.select = True
            for v in f.verts:
                v.select = True
        bmesh.update_edit_mesh(mesh)
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.02)

        self.info(
            f"Slab spawned at cursor (radius={self.radius:.3f}, thickness={self.thickness:.3f})."
        )
        return {"FINISHED"}

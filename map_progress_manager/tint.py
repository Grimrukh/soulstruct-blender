from __future__ import annotations

__all__ = [

]

import bpy

from soulstruct.blender.utilities.operators import LoggingOperator

from .config import TINT_GROUP_NAME, TINT_WRAP_LABEL, PROGRESS_PASS_INDICES
from .properties import on_global_tint_toggle
from .utils import iter_tracked_objects


# region Interface helpers

def _iface_socket(ng: bpy.types.NodeTree, name: str, in_out: str, socket_type: str):
    for s in ng.interface.items_tree:
        if getattr(s, "name", None) == name and getattr(s, "in_out", None) == in_out:
            return s
    return ng.interface.new_socket(name=name, description="", in_out=in_out, socket_type=socket_type)

def _ensure_group_io_nodes(ng: bpy.types.NodeTree):
    gin = next((n for n in ng.nodes if n.bl_idname == "NodeGroupInput"), None)
    if gin is None:
        gin = ng.nodes.new("NodeGroupInput"); gin.location = (-900, 0)
    gout = next((n for n in ng.nodes if n.bl_idname == "NodeGroupOutput"), None)
    if gout is None:
        gout = ng.nodes.new("NodeGroupOutput"); gout.location = (860, 100)
    return gin, gout

def _get_or_make_node(ng: bpy.types.NodeTree, bl_idname: str, name: str, loc=(0, 0)):
    n = ng.nodes.get(name)
    if n:
        return n
    n = ng.nodes.new(bl_idname)
    n.name = name
    n.label = name
    n.location = loc
    return n

# endregion

# region Tint node group builder

def get_or_make_tint_node_group(
    context: bpy.types.Context,
) -> bpy.types.NodeTree:
    settings = context.scene.map_progress_manager_settings
    ng = bpy.data.node_groups.get(TINT_GROUP_NAME)
    if ng is None:
        ng = bpy.data.node_groups.new(TINT_GROUP_NAME, "ShaderNodeTree")

    _iface_socket(ng, "Enable", "INPUT", "NodeSocketFloat")
    _iface_socket(ng, "TintShader", "OUTPUT", "NodeSocketShader")
    _iface_socket(ng, "TintFactor", "OUTPUT", "NodeSocketFloat")

    gin, gout = _ensure_group_io_nodes(ng)
    ng.interface_update(context)

    obji      = _get_or_make_node(ng, "ShaderNodeObjectInfo", "MPM_OBJECT_INFO", (-700, 50))

    # Compare nodes for four indices
    cmp_todo  = _get_or_make_node(ng, "ShaderNodeMath", "MPM_CMP_TODO", (-480, 200))
    cmp_tosc  = _get_or_make_node(ng, "ShaderNodeMath", "MPM_CMP_TODO_SC", (-480, 60))
    cmp_wip   = _get_or_make_node(ng, "ShaderNodeMath", "MPM_CMP_WIP", (-480, -80))
    cmp_done  = _get_or_make_node(ng, "ShaderNodeMath", "MPM_CMP_DONE", (-480, -220))
    for cmp_node, prog_name in (
        (cmp_todo, "TODO"), (cmp_tosc, "TODO_SCENERY"), (cmp_wip, "WIP"), (cmp_done, "DONE")
    ):
        cmp_node.operation = "COMPARE"
        cmp_node.inputs[1].default_value = float(PROGRESS_PASS_INDICES[prog_name])
        cmp_node.inputs[2].default_value = 0.5
        if not cmp_node.inputs[0].is_linked:
            ng.links.new(obji.outputs["Object Index"], cmp_node.inputs[0])

    # Strength Values
    val_todo  = _get_or_make_node(ng, "ShaderNodeValue", "MPM_TODO_STRENGTH", (-350, 200))
    val_tosc  = _get_or_make_node(ng, "ShaderNodeValue", "MPM_TODO_SC_STRENGTH", (-350, 60))
    val_wip   = _get_or_make_node(ng, "ShaderNodeValue", "MPM_WIP_STRENGTH", (-350, -80))
    val_done  = _get_or_make_node(ng, "ShaderNodeValue", "MPM_DONE_STRENGTH", (-350, -220))

    # mask * strength
    def mul_node(name, x, y):
        m = _get_or_make_node(ng, "ShaderNodeMath", name, (x, y))
        m.operation = "MULTIPLY"
        return m
    mul_todo  = mul_node("MPM_MUL_TODO",  -170,  200)
    mul_tosc  = mul_node("MPM_MUL_TODO_SC", -170,  60)
    mul_wip   = mul_node("MPM_MUL_WIP",   -170,  -80)
    mul_done  = mul_node("MPM_MUL_DONE",  -170, -220)

    if not mul_todo.inputs[0].is_linked: ng.links.new(cmp_todo.outputs[0], mul_todo.inputs[0])
    if not mul_todo.inputs[1].is_linked: ng.links.new(val_todo.outputs[0], mul_todo.inputs[1])
    if not mul_tosc.inputs[0].is_linked: ng.links.new(cmp_tosc.outputs[0], mul_tosc.inputs[0])
    if not mul_tosc.inputs[1].is_linked: ng.links.new(val_tosc.outputs[0], mul_tosc.inputs[1])
    if not mul_wip.inputs[0].is_linked:  ng.links.new(cmp_wip.outputs[0],  mul_wip.inputs[0])
    if not mul_wip.inputs[1].is_linked:  ng.links.new(val_wip.outputs[0],  mul_wip.inputs[1])
    if not mul_done.inputs[0].is_linked: ng.links.new(cmp_done.outputs[0], mul_done.inputs[0])
    if not mul_done.inputs[1].is_linked: ng.links.new(val_done.outputs[0], mul_done.inputs[1])

    # Colors (RGB)
    rgb_todo  = _get_or_make_node(ng, "ShaderNodeRGB", "MPM_TODO_COLOR", (-350, 320))
    rgb_tosc  = _get_or_make_node(ng, "ShaderNodeRGB", "MPM_TODO_SC_COLOR", (-350, 180))
    rgb_wip   = _get_or_make_node(ng, "ShaderNodeRGB", "MPM_WIP_COLOR", (-350, 40))
    rgb_done  = _get_or_make_node(ng, "ShaderNodeRGB", "MPM_DONE_COLOR", (-350, -100))

    # Expand scalar to vector and multiply with color (four lanes)
    def lane(mul, name_prefix, y):
        comb = _get_or_make_node(ng, "ShaderNodeCombineXYZ", f"{name_prefix}_COMB", (-60, y))
        for i in range(3):
            if not comb.inputs[i].is_linked:
                ng.links.new(mul.outputs[0], comb.inputs[i])
        math_node = _get_or_make_node(ng, "ShaderNodeVectorMath", f"{name_prefix}_VMUL", (60, y))
        math_node.operation = "MULTIPLY"
        return comb, math_node

    comb_t, vm_todo   = lane(mul_todo, "MPM_TODO",  300)
    comb_ts, vm_tosc  = lane(mul_tosc, "MPM_TODO_SC", 160)
    comb_w, vm_wip    = lane(mul_wip,  "MPM_WIP",   20)
    comb_d, vm_done   = lane(mul_done, "MPM_DONE", -120)

    for rgb, vm in ((rgb_todo, vm_todo), (rgb_tosc, vm_tosc), (rgb_wip, vm_wip), (rgb_done, vm_done)):
        if not vm.inputs[0].is_linked: ng.links.new(rgb.outputs[0], vm.inputs[0])
    if not vm_todo.inputs[1].is_linked: ng.links.new(comb_t.outputs[0], vm_todo.inputs[1])
    if not vm_tosc.inputs[1].is_linked: ng.links.new(comb_ts.outputs[0], vm_tosc.inputs[1])
    if not vm_wip.inputs[1].is_linked:  ng.links.new(comb_w.outputs[0],  vm_wip.inputs[1])
    if not vm_done.inputs[1].is_linked: ng.links.new(comb_d.outputs[0],  vm_done.inputs[1])

    # Sum the four tint vectors
    vadd1 = _get_or_make_node(ng, "ShaderNodeVectorMath", "MPM_VADD1", (260, 240)); vadd1.operation = "ADD"
    vadd2 = _get_or_make_node(ng, "ShaderNodeVectorMath", "MPM_VADD2", (420, 180)); vadd2.operation = "ADD"
    vadd3 = _get_or_make_node(ng, "ShaderNodeVectorMath", "MPM_VADD3", (580, 120)); vadd3.operation = "ADD"
    if not vadd1.inputs[0].is_linked: ng.links.new(vm_todo.outputs[0], vadd1.inputs[0])
    if not vadd1.inputs[1].is_linked: ng.links.new(vm_tosc.outputs[0], vadd1.inputs[1])
    if not vadd2.inputs[0].is_linked: ng.links.new(vadd1.outputs[0],   vadd2.inputs[0])
    if not vadd2.inputs[1].is_linked: ng.links.new(vm_wip.outputs[0],  vadd2.inputs[1])
    if not vadd3.inputs[0].is_linked: ng.links.new(vadd2.outputs[0],   vadd3.inputs[0])
    if not vadd3.inputs[1].is_linked: ng.links.new(vm_done.outputs[0], vadd3.inputs[1])

    # Vector -> Color -> Emission
    sep   = _get_or_make_node(ng, "ShaderNodeSeparateXYZ", "MPM_SEP", (740, 120))
    combc = _get_or_make_node(ng, "ShaderNodeCombineColor", "MPM_COMBC", (900, 120))
    if not sep.inputs[0].is_linked:        ng.links.new(vadd3.outputs[0], sep.inputs[0])
    if not combc.inputs["Red"].is_linked:   ng.links.new(sep.outputs[0], combc.inputs["Red"])
    if not combc.inputs["Green"].is_linked: ng.links.new(sep.outputs[1], combc.inputs["Green"])
    if not combc.inputs["Blue"].is_linked:  ng.links.new(sep.outputs[2], combc.inputs["Blue"])
    emis = _get_or_make_node(ng, "ShaderNodeEmission", "MPM_EMISSION", (1100, 120))
    if not emis.inputs["Color"].is_linked: ng.links.new(combc.outputs["Color"], emis.inputs["Color"])

    # Factor = sum strengths (4 lanes), clamped 0..1, gated by Enable
    add1 = _get_or_make_node(ng, "ShaderNodeMath", "MPM_ADD1", (60, -260)); add1.operation = "ADD"
    add2 = _get_or_make_node(ng, "ShaderNodeMath", "MPM_ADD2", (220, -260)); add2.operation = "ADD"
    add3 = _get_or_make_node(ng, "ShaderNodeMath", "MPM_ADD3", (380, -260)); add3.operation = "ADD"
    if not add1.inputs[0].is_linked: ng.links.new(mul_todo.outputs[0], add1.inputs[0])
    if not add1.inputs[1].is_linked: ng.links.new(mul_tosc.outputs[0], add1.inputs[1])
    if not add2.inputs[0].is_linked: ng.links.new(add1.outputs[0],     add2.inputs[0])
    if not add2.inputs[1].is_linked: ng.links.new(mul_wip.outputs[0],  add2.inputs[1])
    if not add3.inputs[0].is_linked: ng.links.new(add2.outputs[0],     add3.inputs[0])
    if not add3.inputs[1].is_linked: ng.links.new(mul_done.outputs[0], add3.inputs[1])

    clamp = _get_or_make_node(ng, "ShaderNodeClamp", "MPM_CLAMP", (540, -260))
    clamp.inputs["Min"].default_value = 0.0
    clamp.inputs["Max"].default_value = 1.0
    if not clamp.inputs["Value"].is_linked:
        ng.links.new(add3.outputs[0], clamp.inputs["Value"])

    mul_en = _get_or_make_node(ng, "ShaderNodeMath", "MPM_ENABLE_MUL", (700, -260))
    mul_en.operation = "MULTIPLY"
    if not mul_en.inputs[0].is_linked: ng.links.new(clamp.outputs[0], mul_en.inputs[0])
    if "Enable" in gin.outputs and not mul_en.inputs[1].is_linked:
        ng.links.new(gin.outputs["Enable"], mul_en.inputs[1])

    # Outputs
    if "TintShader" in gout.inputs and not gout.inputs["TintShader"].is_linked:
        ng.links.new(emis.outputs["Emission"], gout.inputs["TintShader"])
    if "TintFactor" in gout.inputs and not gout.inputs["TintFactor"].is_linked:
        ng.links.new(mul_en.outputs[0], gout.inputs["TintFactor"])

    # Set colors and strengths from settings
    rgb_todo.outputs[0].default_value = settings.todo_color
    rgb_tosc.outputs[0].default_value = settings.todo_sc_color
    rgb_wip .outputs[0].default_value = settings.wip_color
    rgb_done.outputs[0].default_value = settings.done_color
    val_todo.outputs[0].default_value = settings.todo_strength
    val_tosc.outputs[0].default_value = settings.todo_sc_strength
    val_wip .outputs[0].default_value = settings.wip_strength
    val_done.outputs[0].default_value = settings.done_strength

    return ng

# endregion

# region Tint operators

class ApplyProgressTintToMaterials(LoggingOperator):
    bl_idname = "mapprog.apply_tint_materials"
    bl_label = "Apply Progress Tint (Materials)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        # Sync indices for masks.
        for obj in iter(bpy.data.objects):
            if hasattr(obj, "map_progress"):
                obj.map_progress.sync_pass_index(obj)

        get_or_make_tint_node_group(context)

        mats = set()
        for obj in iter_tracked_objects():
            for slot in (obj.material_slots or []):
                if slot.material:
                    mats.add(slot.material)

        applied = 0
        for mat in mats:
            if inject_tint_into_material(context, mat):
                applied += 1

        # make sure Enable flag propagates
        on_global_tint_toggle(self, context)
        self.info(f"Applied tint injection to {applied} material(s).")
        return {"FINISHED"}


class RemoveProgressTintFromMaterials(LoggingOperator):
    bl_idname = "mapprog.remove_tint_materials"
    bl_label = "Remove Progress Tint (Materials)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mats = set()
        for obj in iter_tracked_objects():
            for slot in (obj.material_slots or []):
                if slot.material:
                    mats.add(slot.material)

        removed = 0
        for mat in mats:
            if remove_tint_from_material(mat):
                removed += 1

        self.info(f"Removed tint injection from {removed} material(s).")
        return {"FINISHED"}

# endregion

# region Tint injection / removal

def inject_tint_into_material(context: bpy.types.Context, mat: bpy.types.Material) -> bool:
    if not mat or not mat.use_nodes or not mat.node_tree:
        return False
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if not out:
        return False
    surf_in = out.inputs.get("Surface")
    if not surf_in:
        return False
    # already wrapped?
    if any(isinstance(l.from_node, bpy.types.ShaderNodeMixShader) and l.from_node.label == TINT_WRAP_LABEL
           for l in surf_in.links):
        return False

    # original
    if surf_in.is_linked:
        orig = surf_in.links[0].from_node
        orig_out = surf_in.links[0].from_socket
    else:
        orig = nt.nodes.new("ShaderNodeBsdfPrincipled"); orig.location = (out.location.x - 300, out.location.y)
        orig_out = orig.outputs["BSDF"]

    # group
    ng = get_or_make_tint_node_group(context)
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = ng; grp.label = TINT_GROUP_NAME; grp.location = (orig.location.x, orig.location.y - 220)

    # set Enable from Scene
    en_val = 1.0 if context.scene.map_progress_manager_settings.tint_enabled else 0.0
    if "Enable" in grp.inputs:
        grp.inputs["Enable"].default_value = en_val

    # wrapper mix
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.label = TINT_WRAP_LABEL; mix.location = (out.location.x + 200, out.location.y)

    while surf_in.is_linked:
        nt.links.remove(surf_in.links[0])

    nt.links.new(orig_out, mix.inputs[1])
    nt.links.new(grp.outputs["TintShader"], mix.inputs[2])
    nt.links.new(grp.outputs["TintFactor"], mix.inputs[0])
    nt.links.new(mix.outputs["Shader"], surf_in)

    return True


def remove_tint_from_material(mat: bpy.types.Material) -> bool:
    if not mat or not mat.use_nodes or not mat.node_tree:
        return False
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if not out:
        return False
    surf_in = out.inputs.get("Surface")
    if not surf_in or not surf_in.is_linked:
        return False
    mix = surf_in.links[0].from_node
    if not (isinstance(mix, bpy.types.ShaderNodeMixShader) and mix.label == TINT_WRAP_LABEL):
        return False

    orig_link = mix.inputs[1].links[0] if mix.inputs[1].is_linked else None
    if orig_link:
        nt.links.new(orig_link.from_socket, surf_in)

    grp = None
    for link in mix.inputs[2].links:
        if isinstance(link.from_node, bpy.types.ShaderNodeGroup) and getattr(link.from_node, "label", "") == TINT_GROUP_NAME:
            grp = link.from_node
    nt.nodes.remove(mix)
    if grp:
        nt.nodes.remove(grp)
    return True

# endregion

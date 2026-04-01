from __future__ import annotations

__all__ = [
    "ensure_debug_node_group",
    "add_debug_group_to_material",
    "remove_debug_group_from_material",
    "sync_material_debug_nodes",
]

import bpy

from .properties import *


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

def _ensure_node(ng: bpy.types.NodeTree, bl_idname: str, name: str, loc=(0, 0)):
    n = ng.nodes.get(name)
    if n:
        return n
    n = ng.nodes.new(bl_idname)
    n.name = name
    n.label = name
    n.location = loc
    return n

def _ensure_math_node(ng: bpy.types.NodeTree, operation: str, name: str, loc=(0, 0)):
    n = ng.nodes.get(name)
    if n:
        return n
    n = _ensure_node(ng, "ShaderNodeMath", name, loc)
    n.operation = operation
    return n


def ensure_debug_node_group(context: bpy.types.Context) -> bpy.types.NodeTree:
    """Create/return the Soulstruct material debug node group.

    Modes:
      0 = NONE      (no overlay)
      1 = PROGRESS  (object-index progress tint)
      2 = ALPHA     (vertex-color alpha heatmap from Attribute name)
      3 = UV        (high-contrast UV checker overlay)
    """

    settings = context.scene.material_debug_settings
    # Progress settings used for colors.
    progress_settings = context.scene.map_progress_settings

    ng = bpy.data.node_groups.get(DEBUG_GROUP_NAME)
    if ng is not None:
        return ng

    ng = bpy.data.node_groups.new(DEBUG_GROUP_NAME, "ShaderNodeTree")

    # --- Interface sockets ---
    _iface_socket(ng, "DebugShader",     "OUTPUT", "NodeSocketShader")
    _iface_socket(ng, "DebugFactor",     "OUTPUT", "NodeSocketFloat")

    gin, gout = _ensure_group_io_nodes(ng)
    ng.interface_update(context)

    # ========
    # INPUT VARIABLE NODES
    # ========
    enabled_input = _ensure_node(ng, "ShaderNodeValue", "DEBUG_ENABLED", (-900, 300))
    enabled_input.outputs[0].default_value = 1.0 if settings.enabled else 0.0
    mode_input    = _ensure_node(ng, "ShaderNodeValue", "DEBUG_MODE",    (-900, 100))
    mode_input.outputs[0].default_value = MaterialDebugSettings.MODE_NODE_VALUES.get(settings.mode, 0.0)
    alpha_attr    = _ensure_node(ng, "ShaderNodeAttribute", "DEBUG_ALPHA_ATTR", (-900, -300))
    alpha_attr.attribute_name = settings.alpha_attr_name  # current value
    uv_checker_scale = _ensure_node(ng, "ShaderNodeValue", "DEBUG_UV_CHECKER_SCALE", (-900, -500))
    uv_checker_scale.outputs[0].default_value = settings.uv_checker_scale

    # ============================================================================================
    # PROGRESS branch
    # ============================================================================================
    obji = _ensure_node(ng, "ShaderNodeObjectInfo", "DEBUG_OBJECT_INFO", (-700, 50))

    # Compare against the four pass indices
    cmp_todo = _ensure_math_node(ng, "COMPARE", "DEBUG_CMP_TODO", (-480, 200))
    cmp_tosc = _ensure_math_node(ng, "COMPARE", "DEBUG_CMP_TODO_SC", (-480, 60))
    cmp_wip  = _ensure_math_node(ng, "COMPARE", "DEBUG_CMP_WIP", (-480, -80))
    cmp_done = _ensure_math_node(ng, "COMPARE", "DEBUG_CMP_DONE", (-480, -220))

    for cmp_node, prog_name in (
        (cmp_todo, "TODO"),
        (cmp_tosc, "TODO_SCENERY"),
        (cmp_wip,  "WIP"),
        (cmp_done, "DONE"),
    ):
        cmp_node.inputs[1].default_value = float(progress_settings.PROGRESS_STATE_INDICES[prog_name])
        cmp_node.inputs[2].default_value = 0.5
        if not cmp_node.inputs[0].is_linked:
            ng.links.new(obji.outputs["Object Index"], cmp_node.inputs[0])

    # Strength values
    val_todo = _ensure_node(ng, "ShaderNodeValue", "DEBUG_TODO_STRENGTH", (-350, 200))
    val_tosc = _ensure_node(ng, "ShaderNodeValue", "DEBUG_TODO_SC_STRENGTH", (-350, 60))
    val_wip  = _ensure_node(ng, "ShaderNodeValue", "DEBUG_WIP_STRENGTH", (-350, -80))
    val_done = _ensure_node(ng, "ShaderNodeValue", "DEBUG_DONE_STRENGTH", (-350, -220))

    mul_todo = _ensure_math_node(ng, "MULTIPLY", "DEBUG_MUL_TODO", (-170, 200))
    mul_tosc = _ensure_math_node(ng, "MULTIPLY", "DEBUG_MUL_TODO_SC", (-170, 60))
    mul_wip  = _ensure_math_node(ng, "MULTIPLY", "DEBUG_MUL_WIP", (-170, -80))
    mul_done = _ensure_math_node(ng, "MULTIPLY", "DEBUG_MUL_DONE", (-170, -220))

    if not mul_todo.inputs[0].is_linked: ng.links.new(cmp_todo.outputs[0], mul_todo.inputs[0])
    if not mul_todo.inputs[1].is_linked: ng.links.new(val_todo.outputs[0], mul_todo.inputs[1])
    if not mul_tosc.inputs[0].is_linked: ng.links.new(cmp_tosc.outputs[0], mul_tosc.inputs[0])
    if not mul_tosc.inputs[1].is_linked: ng.links.new(val_tosc.outputs[0], mul_tosc.inputs[1])
    if not mul_wip.inputs[0].is_linked:  ng.links.new(cmp_wip.outputs[0],  mul_wip.inputs[0])
    if not mul_wip.inputs[1].is_linked:  ng.links.new(val_wip.outputs[0],  mul_wip.inputs[1])
    if not mul_done.inputs[0].is_linked: ng.links.new(cmp_done.outputs[0], mul_done.inputs[0])
    if not mul_done.inputs[1].is_linked: ng.links.new(val_done.outputs[0], mul_done.inputs[1])

    # Colors
    rgb_todo = _ensure_node(ng, "ShaderNodeRGB", "DEBUG_TODO_COLOR", (-350, 320))
    rgb_tosc = _ensure_node(ng, "ShaderNodeRGB", "DEBUG_TODO_SC_COLOR", (-350, 180))
    rgb_wip  = _ensure_node(ng, "ShaderNodeRGB", "DEBUG_WIP_COLOR", (-350, 40))
    rgb_done = _ensure_node(ng, "ShaderNodeRGB", "DEBUG_DONE_COLOR", (-350, -100))

    # Expand scalar to vector and multiply with color (4 lanes)
    def lane(mul, name_prefix, y):
        comb = _ensure_node(ng, "ShaderNodeCombineXYZ", f"{name_prefix}_COMB", (-60, y))
        for i in range(3):
            if not comb.inputs[i].is_linked:
                ng.links.new(mul.outputs[0], comb.inputs[i])
        math_node = _ensure_node(ng, "ShaderNodeVectorMath", f"{name_prefix}_VMUL", (60, y))
        math_node.operation = "MULTIPLY"
        return comb, math_node

    comb_t, vm_todo  = lane(mul_todo, "DEBUG_TODO", 300)
    comb_ts, vm_tosc = lane(mul_tosc, "DEBUG_TODO_SC", 160)
    comb_w, vm_wip   = lane(mul_wip, "DEBUG_WIP", 20)
    comb_d, vm_done  = lane(mul_done, "DEBUG_DONE", -120)

    for rgb, vm in ((rgb_todo, vm_todo), (rgb_tosc, vm_tosc), (rgb_wip, vm_wip), (rgb_done, vm_done)):
        if not vm.inputs[0].is_linked:
            ng.links.new(rgb.outputs[0], vm.inputs[0])
    if not vm_todo.inputs[1].is_linked: ng.links.new(comb_t.outputs[0],  vm_todo.inputs[1])
    if not vm_tosc.inputs[1].is_linked: ng.links.new(comb_ts.outputs[0], vm_tosc.inputs[1])
    if not vm_wip.inputs[1].is_linked:  ng.links.new(comb_w.outputs[0],  vm_wip.inputs[1])
    if not vm_done.inputs[1].is_linked: ng.links.new(comb_d.outputs[0],  vm_done.inputs[1])

    # Sum the 4 tint vectors
    vadd1 = _ensure_node(ng, "ShaderNodeVectorMath", "DEBUG_VADD1", (260, 240)); vadd1.operation = "ADD"
    vadd2 = _ensure_node(ng, "ShaderNodeVectorMath", "DEBUG_VADD2", (420, 180)); vadd2.operation = "ADD"
    vadd3 = _ensure_node(ng, "ShaderNodeVectorMath", "DEBUG_VADD3", (580, 120)); vadd3.operation = "ADD"
    if not vadd1.inputs[0].is_linked: ng.links.new(vm_todo.outputs[0], vadd1.inputs[0])
    if not vadd1.inputs[1].is_linked: ng.links.new(vm_tosc.outputs[0], vadd1.inputs[1])
    if not vadd2.inputs[0].is_linked: ng.links.new(vadd1.outputs[0],   vadd2.inputs[0])
    if not vadd2.inputs[1].is_linked: ng.links.new(vm_wip.outputs[0],  vadd2.inputs[1])
    if not vadd3.inputs[0].is_linked: ng.links.new(vadd2.outputs[0],   vadd3.inputs[0])
    if not vadd3.inputs[1].is_linked: ng.links.new(vm_done.outputs[0], vadd3.inputs[1])

    # Vector -> Color -> Emission
    sep = _ensure_node(ng, "ShaderNodeSeparateXYZ", "DEBUG_SEP", (740, 120))
    combc = _ensure_node(ng, "ShaderNodeCombineColor", "DEBUG_COMBC", (900, 120))
    if not sep.inputs[0].is_linked:            ng.links.new(vadd3.outputs[0], sep.inputs[0])
    if not combc.inputs["Red"].is_linked:      ng.links.new(sep.outputs[0], combc.inputs["Red"])
    if not combc.inputs["Green"].is_linked:    ng.links.new(sep.outputs[1], combc.inputs["Green"])
    if not combc.inputs["Blue"].is_linked:     ng.links.new(sep.outputs[2], combc.inputs["Blue"])
    emis = _ensure_node(ng, "ShaderNodeEmission", "DEBUG_EMISSION", (1100, 120))
    if not emis.inputs["Color"].is_linked:     ng.links.new(combc.outputs["Color"], emis.inputs["Color"])

    # Factor for PROGRESS = clamp(sum strengths) * Enable
    add1 = _ensure_node(ng, "ShaderNodeMath", "DEBUG_ADD1", (60, -260));   add1.operation = "ADD"
    add2 = _ensure_node(ng, "ShaderNodeMath", "DEBUG_ADD2", (220, -260));  add2.operation = "ADD"
    add3 = _ensure_node(ng, "ShaderNodeMath", "DEBUG_ADD3", (380, -260));  add3.operation = "ADD"
    if not add1.inputs[0].is_linked: ng.links.new(mul_todo.outputs[0], add1.inputs[0])
    if not add1.inputs[1].is_linked: ng.links.new(mul_tosc.outputs[0], add1.inputs[1])
    if not add2.inputs[0].is_linked: ng.links.new(add1.outputs[0],     add2.inputs[0])
    if not add2.inputs[1].is_linked: ng.links.new(mul_wip.outputs[0],  add2.inputs[1])
    if not add3.inputs[0].is_linked: ng.links.new(add2.outputs[0],     add3.inputs[0])
    if not add3.inputs[1].is_linked: ng.links.new(mul_done.outputs[0], add3.inputs[1])
    clamp = _ensure_node(ng, "ShaderNodeClamp", "DEBUG_CLAMP", (540, -260))
    clamp.inputs["Min"].default_value = 0.0
    clamp.inputs["Max"].default_value = 1.0
    if not clamp.inputs["Value"].is_linked:
        ng.links.new(add3.outputs[0], clamp.inputs["Value"])

    # ============================================================================================
    # ALPHA branch (vertex color heatmap)
    # ============================================================================================

    # TODO: Would be neat to be able to visualize vertex color RGB here too.

    clamp_a = _ensure_node(ng, "ShaderNodeClamp", "DEBUG_ALPHA_CLAMP", (-90, -540))
    clamp_a.inputs["Min"].default_value, clamp_a.inputs["Max"].default_value = 0.0, 1.0
    if not clamp_a.inputs["Value"].is_linked:
        ng.links.new(alpha_attr.outputs["Alpha"], clamp_a.inputs["Value"])

    ramp = _ensure_node(ng, "ShaderNodeValToRGB", "DEBUG_ALPHA_RAMP", (100, -540))
    if len(ramp.color_ramp.elements) == 2:
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.0, 0.2, 1.0, 1.0)
        mid = ramp.color_ramp.elements.new(0.5); mid.color = (0.0, 1.0, 1.0, 1.0)
        ramp.color_ramp.elements[1].position = 1.0
        ramp.color_ramp.elements[1].color = (1.0, 0.0, 0.0, 1.0)
    if not ramp.inputs["Fac"].is_linked:
        ng.links.new(clamp_a.outputs["Result"], ramp.inputs["Fac"])

    emis_alpha = _ensure_node(ng, "ShaderNodeEmission", "DEBUG_ALPHA_EMISSION", (320, -540))
    if not emis_alpha.inputs["Color"].is_linked:
        ng.links.new(ramp.outputs["Color"], emis_alpha.inputs["Color"])

    # ============================================================================================
    # UV branch (checker + thin grid lines)
    # ============================================================================================
    uvmap = _ensure_node(ng, "ShaderNodeUVMap", "DEBUG_UV_MAP", (-480, -860))
    uvmap.uv_map = ""  # active UV map

    uv_scale = _ensure_node(ng, "ShaderNodeVectorMath", "DEBUG_UV_SCALE", (-300, -860))
    uv_scale.operation = "SCALE"
    # VectorMath.SCALE uses input[3] for scalar
    if not uv_scale.inputs[3].is_linked:
        ng.links.new(uv_checker_scale.outputs[0], uv_scale.inputs[3])
    if not uv_scale.inputs[0].is_linked:
        ng.links.new(uvmap.outputs["UV"], uv_scale.inputs[0])

    checker = _ensure_node(ng, "ShaderNodeTexChecker", "DEBUG_UV_CHECKER", (-90, -860))
    checker.inputs["Scale"].default_value = 1.0  # scale driven upstream
    checker.inputs["Color1"].default_value = (0.1, 0.1, 0.1, 1.0)
    checker.inputs["Color2"].default_value = (0.9, 0.9, 0.9, 1.0)
    if not checker.inputs["Vector"].is_linked:
        ng.links.new(uv_scale.outputs["Vector"], checker.inputs["Vector"])

    wave_u = _ensure_node(ng, "ShaderNodeTexWave", "DEBUG_UV_LINES_U", (90, -980))
    wave_u.wave_type, wave_u.bands_direction = 'BANDS', 'X'
    wave_u.inputs["Scale"].default_value = 1.0
    wave_u.inputs["Distortion"].default_value = 0.0
    wave_u.inputs["Detail"].default_value = 0.0
    if not wave_u.inputs["Vector"].is_linked:
        ng.links.new(uv_scale.outputs["Vector"], wave_u.inputs["Vector"])

    wave_v = _ensure_node(ng, "ShaderNodeTexWave", "DEBUG_UV_LINES_V", (90, -1140))
    wave_v.wave_type, wave_v.bands_direction = 'BANDS', 'Y'
    wave_v.inputs["Scale"].default_value = 1.0
    wave_v.inputs["Distortion"].default_value = 0.0
    wave_v.inputs["Detail"].default_value = 0.0
    if not wave_v.inputs["Vector"].is_linked:
        ng.links.new(uv_scale.outputs["Vector"], wave_v.inputs["Vector"])

    mix_lines = _ensure_node(ng, "ShaderNodeMixRGB", "DEBUG_UV_LINES_MIX", (300, -1060))
    mix_lines.blend_type = 'ADD'
    mix_lines.inputs["Fac"].default_value = 1.0
    if not mix_lines.inputs["Color1"].is_linked: ng.links.new(wave_u.outputs["Color"], mix_lines.inputs["Color1"])
    if not mix_lines.inputs["Color2"].is_linked: ng.links.new(wave_v.outputs["Color"], mix_lines.inputs["Color2"])

    darken = _ensure_node(ng, "ShaderNodeMixRGB", "DEBUG_UV_COMBINE", (520, -920))
    darken.blend_type = 'MULTIPLY'
    darken.inputs["Fac"].default_value = 0.5
    if not darken.inputs["Color1"].is_linked: ng.links.new(checker.outputs["Color"], darken.inputs["Color1"])
    if not darken.inputs["Color2"].is_linked: ng.links.new(mix_lines.outputs["Color"], darken.inputs["Color2"])

    emis_uv = _ensure_node(ng, "ShaderNodeEmission", "DEBUG_UV_EMISSION", (720, -920))
    if not emis_uv.inputs["Color"].is_linked:
        ng.links.new(darken.outputs["Color"], emis_uv.inputs["Color"])

    # ============================================================================================
    # MODE selection and outputs
    # ============================================================================================
    # Build masks for modes: PROGRESS(1), ALPHA(2), UV(3)
    mode_sub_1 = _ensure_math_node(ng, "SUBTRACT", "DEBUG_SUB_1", (-120, -120))
    mode_abs_1 = _ensure_math_node(ng, "ABSOLUTE", "DEBUG_ABS_M1", (60, -120))
    cmp_prog   = _ensure_math_node(ng, "LESS_THAN", "DEBUG_IS_PROG", (240, -120))
    cmp_prog.inputs[1].default_value = 0.5

    mode_sub_2 = _ensure_math_node(ng, "SUBTRACT", "DEBUG_SUB_2", (-120, -300))
    mode_abs_2 = _ensure_math_node(ng, "ABSOLUTE", "DEBUG_ABS_M2", (60, -300))
    cmp_alpha  = _ensure_math_node(ng, "LESS_THAN", "DEBUG_IS_ALPHA",(240, -300))
    cmp_alpha.inputs[1].default_value = 0.5

    mode_sub_3 = _ensure_math_node(ng, "SUBTRACT", "DEBUG_SUB_3", (-120, -480))
    mode_abs_3 = _ensure_math_node(ng, "ABSOLUTE", "DEBUG_ABS_M3", (60, -480))
    cmp_uv     = _ensure_math_node(ng, "LESS_THAN", "DEBUG_IS_UV",   (240, -480))
    cmp_uv.inputs[1].default_value = 0.5

    if not mode_sub_1.inputs[0].is_linked: ng.links.new(mode_input.outputs[0], mode_sub_1.inputs[0])
    if not mode_sub_2.inputs[0].is_linked: ng.links.new(mode_input.outputs[0], mode_sub_2.inputs[0])
    if not mode_sub_3.inputs[0].is_linked: ng.links.new(mode_input.outputs[0], mode_sub_3.inputs[0])
    mode_sub_1.inputs[1].default_value = 1.0
    mode_sub_2.inputs[1].default_value = 2.0
    mode_sub_3.inputs[1].default_value = 3.0
    if not mode_abs_1.inputs[0].is_linked: ng.links.new(mode_sub_1.outputs[0], mode_abs_1.inputs[0])
    if not mode_abs_2.inputs[0].is_linked: ng.links.new(mode_sub_2.outputs[0], mode_abs_2.inputs[0])
    if not mode_abs_3.inputs[0].is_linked: ng.links.new(mode_sub_3.outputs[0], mode_abs_3.inputs[0])
    if not cmp_prog.inputs[0].is_linked:    ng.links.new(mode_abs_1.outputs[0], cmp_prog.inputs[0])
    if not cmp_alpha.inputs[0].is_linked:   ng.links.new(mode_abs_2.outputs[0], cmp_alpha.inputs[0])
    if not cmp_uv.inputs[0].is_linked:      ng.links.new(mode_abs_3.outputs[0], cmp_uv.inputs[0])

    # Choose emission: first between PROGRESS/ALPHA, then vs UV
    mix_emis = _ensure_node(ng, "ShaderNodeMixShader", "DEBUG_PICK_EMIS", (420, -540))
    if not mix_emis.inputs[0].is_linked: ng.links.new(cmp_alpha.outputs[0], mix_emis.inputs[0])
    if not mix_emis.inputs[1].is_linked: ng.links.new(emis.outputs["Emission"], mix_emis.inputs[1])       # PROGRESS
    if not mix_emis.inputs[2].is_linked: ng.links.new(emis_alpha.outputs["Emission"], mix_emis.inputs[2]) # ALPHA

    mix_pick_uv = _ensure_node(ng, "ShaderNodeMixShader", "DEBUG_PICK_UV", (740, -620))
    if not mix_pick_uv.inputs[0].is_linked: ng.links.new(cmp_uv.outputs[0], mix_pick_uv.inputs[0])
    if not mix_pick_uv.inputs[1].is_linked: ng.links.new(mix_emis.outputs["Shader"], mix_pick_uv.inputs[1])
    if not mix_pick_uv.inputs[2].is_linked: ng.links.new(emis_uv.outputs["Emission"], mix_pick_uv.inputs[2])

    # Gate by any active mode (PROGRESS|ALPHA|UV)
    add_masks_1 = _ensure_math_node(ng, "ADD", "DEBUG_ADD_MASKS1", (540, -360))
    add_masks_2 = _ensure_math_node(ng, "ADD", "DEBUG_ADD_MASKS2", (700, -360))
    if not add_masks_1.inputs[0].is_linked: ng.links.new(cmp_prog.outputs[0], add_masks_1.inputs[0])
    if not add_masks_1.inputs[1].is_linked: ng.links.new(cmp_alpha.outputs[0], add_masks_1.inputs[1])
    if not add_masks_2.inputs[0].is_linked: ng.links.new(add_masks_1.outputs[0], add_masks_2.inputs[0])
    if not add_masks_2.inputs[1].is_linked: ng.links.new(cmp_uv.outputs[0],    add_masks_2.inputs[1])

    emis_black = _ensure_node(ng, "ShaderNodeEmission", "DEBUG_BLACK", (540, -540))
    emis_black.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)

    mix_any = _ensure_node(ng, "ShaderNodeMixShader", "DEBUG_MIX_ANY", (940, -540))
    if not mix_any.inputs[0].is_linked: ng.links.new(add_masks_2.outputs[0], mix_any.inputs[0])
    if not mix_any.inputs[1].is_linked: ng.links.new(emis_black.outputs["Emission"], mix_any.inputs[1])
    if not mix_any.inputs[2].is_linked: ng.links.new(mix_pick_uv.outputs["Shader"],  mix_any.inputs[2])

    # --- DebugShader out ---
    if "DebugShader" in gout.inputs and not gout.inputs["DebugShader"].is_linked:
        ng.links.new(mix_any.outputs["Shader"], gout.inputs["DebugShader"])

    # --- DebugFactor out ---
    # PROGRESS uses 'clamp'; ALPHA/UV use 1.0; all multiplied by Enable.
    fac_prog  = _ensure_math_node(ng, "MULTIPLY", "DEBUG_FAC_PROG", (540, -40))
    fac_alpha = _ensure_math_node(ng, "MULTIPLY", "DEBUG_FAC_ALPHA", (540, -200))
    fac_uv    = _ensure_math_node(ng, "MULTIPLY", "DEBUG_FAC_UV", (540, -260))

    if not fac_prog.inputs[0].is_linked:  ng.links.new(cmp_prog.outputs[0],  fac_prog.inputs[0])
    if not fac_prog.inputs[1].is_linked:  ng.links.new(clamp.outputs[0],     fac_prog.inputs[1])
    if not fac_alpha.inputs[0].is_linked: ng.links.new(cmp_alpha.outputs[0], fac_alpha.inputs[0])
    fac_alpha.inputs[1].default_value = 1.0
    if not fac_uv.inputs[0].is_linked:    ng.links.new(cmp_uv.outputs[0],    fac_uv.inputs[0])
    fac_uv.inputs[1].default_value = 1.0

    fac_add1 = _ensure_math_node(ng, "ADD", "DEBUG_FAC_ADD1", (700, -120))
    if not fac_add1.inputs[0].is_linked: ng.links.new(fac_prog.outputs[0],  fac_add1.inputs[0])
    if not fac_add1.inputs[1].is_linked: ng.links.new(fac_alpha.outputs[0], fac_add1.inputs[1])

    fac_add2 = _ensure_math_node(ng, "ADD", "DEBUG_FAC_ADD2", (860, -140))
    if not fac_add2.inputs[0].is_linked: ng.links.new(fac_add1.outputs[0],  fac_add2.inputs[0])
    if not fac_add2.inputs[1].is_linked: ng.links.new(fac_uv.outputs[0],    fac_add2.inputs[1])

    fac_enable = _ensure_math_node(ng, "MULTIPLY", "DEBUG_FAC_ENABLE", (1020, -120))
    if not fac_enable.inputs[0].is_linked: ng.links.new(fac_add2.outputs[0], fac_enable.inputs[0])
    if not fac_enable.inputs[1].is_linked:
        ng.links.new(enabled_input.outputs[0], fac_enable.inputs[1])

    if "DebugFactor" in gout.inputs and not gout.inputs["DebugFactor"].is_linked:
        ng.links.new(fac_enable.outputs[0], gout.inputs["DebugFactor"])

    # Set defaults from Map Progress settings for colors/strengths.
    rgb_todo.outputs[0].default_value = progress_settings.todo_color
    rgb_tosc.outputs[0].default_value = progress_settings.todo_sc_color
    rgb_wip .outputs[0].default_value = progress_settings.wip_color
    rgb_done.outputs[0].default_value = progress_settings.done_color
    val_todo.outputs[0].default_value = progress_settings.todo_strength
    val_tosc.outputs[0].default_value = progress_settings.todo_sc_strength
    val_wip .outputs[0].default_value = progress_settings.wip_strength
    val_done.outputs[0].default_value = progress_settings.done_strength

    return ng


def add_debug_group_to_material(context: bpy.types.Context, mat: bpy.types.Material) -> bool:
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
    if any(isinstance(l.from_node, bpy.types.ShaderNodeMixShader) and l.from_node.label == DEBUG_WRAP_LABEL
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
    ng = ensure_debug_node_group(context)
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = ng
    grp.label = DEBUG_GROUP_NAME
    grp.location = (orig.location.x, orig.location.y - 220)

    # set current enabled state
    en_val = 1.0 if context.scene.material_debug_settings.enabled else 0.0
    if "Enable" in grp.inputs:
        grp.inputs["Enable"].default_value = en_val

    # wrapper mix
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.label = DEBUG_WRAP_LABEL
    mix.location = (out.location.x + 200, out.location.y)

    while surf_in.is_linked:
        nt.links.remove(surf_in.links[0])

    nt.links.new(orig_out, mix.inputs[1])
    nt.links.new(grp.outputs["DebugShader"], mix.inputs[2])
    nt.links.new(grp.outputs["DebugFactor"], mix.inputs[0])
    nt.links.new(mix.outputs["Shader"], surf_in)

    return True


def remove_debug_group_from_material(mat: bpy.types.Material) -> bool:
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
    if not (isinstance(mix, bpy.types.ShaderNodeMixShader) and mix.label == DEBUG_WRAP_LABEL):
        return False

    orig_link = mix.inputs[1].links[0] if mix.inputs[1].is_linked else None
    if orig_link:
        nt.links.new(orig_link.from_socket, surf_in)

    grp = None
    for link in mix.inputs[2].links:
        if isinstance(link.from_node, bpy.types.ShaderNodeGroup) and getattr(link.from_node, "label", "") == DEBUG_GROUP_NAME:
            grp = link.from_node
    nt.nodes.remove(mix)
    if grp:
        nt.nodes.remove(grp)
    return True

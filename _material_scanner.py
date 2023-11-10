"""Inspection tool that scans every FLVER in DSR to understand more about the rules for material/shader data."""
import re
from pathlib import Path

from soulstruct.base.models.flver import FLVER
from soulstruct.containers import Binder


VANILLA_CHR_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/chr")
VANILLA_MAP_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup)/map")


TEXTURE_TYPES = {
    "D": "g_Diffuse",
    "S": "g_Specular",
    "B": "g_Bumpmap",
    "H": "g_Height",
    "L": "g_Lightmap",
    "X": "g_DetailBumpmap",
}


# One UV, no Bitangent. Most common layout by far.
CHR_DEFAULT = (
    "Position<12, Float3>, "
    "BoneIndices<4, Byte4B>, "
    "BoneWeights<8, Short4ToFloat4A>, "
    "Normal<4, Byte4C>, "
    "Tangent<4, Byte4C>, "
    "VertexColor<4, Byte4C>, "
    "UV<4, UV>"
)
# Two-UV is the ONLY case (for CHRs) where Bitangent is given.
CHR_UV_PAIR_BITANGENT_LAYOUT = (
    "Position<12, Float3>, "
    "BoneIndices<4, Byte4B>, "
    "BoneWeights<8, Short4ToFloat4A>, "
    "Normal<4, Byte4C>, "
    "Tangent<4, Byte4C>, "
    "Bitangent<4, Byte4C>, "
    "VertexColor<4, Byte4C>, "
    "UV<8, UVPair>"
)

MAP_DEFAULT = "P, BI, N, T, C, UV"
MAP_DEFAULT_NO_TANGENT = "P, BI, N, C, UV"
MAP_DEFAULT_UVPAIR = "P, BI, N, T, C, UVPair"

MTD_DICT = {
    "A10_00_Water_slope": "DSBX",
    "A10_01_Water[B]": "B",
    "A10_02_m9000_M[D]": "DSBX",
    "A10_02_m9000_Sky[Dn]_LS": "DX",
    "A10_02_m9000_cloud[DB]_Alp": "DBX",
    "A10_BG_cloud[Dn]_Add": "D",
    "A10_BG_shaft[Dn]_Add": "D",
    "A10_BG_shaft[Dn]_Add_LS": "D",
    "A10_M_4Stone[DSB][L]_Alp_Spec": "DSBL",
    "A10_Metal[DS][L]": "DSBLX",
    "A10_Sky[Dn]": "D",
    "A10_Sky[Dn]_LS": "DX",
    "A10_Sky_Night[Dn]": "D",
    "A10_Stone[DSB][L]": "DSBLX",
    "A10_Stone[DSB][L]_DetB": "DSBLX",
    "A10_Water_lake[We]": "B",
    "A10_Water_sewer2[We]": "B",
    "A10_Water_sewer3[We]": "B",
    "A10_Water_sewer4[We]": "B",
    "A10_Water_sewer[We]": "B",
    "A10_Watercourse[We]": "B",
    "A10_Wet[DSB][L]_Alp": "DSBLX",
    "A10_cloud[DB]_Alp": "DBX",
    "A10_cloud[Dn]_Add": "DX",
    "A10_lightshaft[Dn]_Add": "D",
    "A10_mist[Dn]_Alp": "D",
    "A10_mist_02[Dn]_Alp": "D",
    "A10_muddiness[D]_Edge": "DSBX",
    "A10_slime[D][L]": "DSBBBL",
    "A10_slime[D][L]_Edge": "DSBLX",
    "A10_sludge[DSB][L]": "DSBLX",
    "A10_sludge[DSB][L]_Alp": "DSBLX",
    "A10_waterfall[DSB]_Alp": "DSB",
    "A11_Sky[Dn]": "D",
    "A11_Snow": "DBB",
    "A11_Snow[L]": "DSBBBL",
    "A11_Snow_stair": "DSBBB",
    "A11_Snow_stair[L]": "DSBBBL",
    "A11_Water[W]": "B",
    "A11_cloud[Dn]_Add": "D",
    "A11_lightshaft[Dn]_Add": "D",
    "A12_DarkRiver": "B",
    "A12_DarkWater": "B",
    "A12_Grass[DS][L]_Edg": "DSLX",
    "A12_Grass[D][L]_Edge": "DSBLX",
    "A12_Ground[DSB]": "DSBX",
    "A12_Ground[DSB][L]": "DSBLX",
    "A12_Ground[DSB][L]_Alp": "DSBLX",
    "A12_Ground[DSB]_Alp": "DSBX",
    "A12_Ground[D[L]]": "DSBLX",
    "A12_Ground[D]": "DSBX",
    "A12_Little River": "B",
    "A12_Little waterfall[DSB]_Alp": "DSBX",
    "A12_NewWater": "B",
    "A12_River_No reflect": "B",
    "A12_Wall+Ground[DSB][M][L]": "DSBMLX",
    "A12_Wall[DSB][L]": "DSBLX",
    "A12_Water": "B",
    "A12_Water_boss": "B",
    "A12_Water_lake": "B",
    "A12_Wet Ground[DSB][L]": "DSBLX",
    "A12_waterfall[DSB]_Alp": "DSBX",
    "A13_M[D]_Alp": "DSBX",
    "A13_Water_B1syounyuu[We]": "B",
    "A13_Water_lake3[We]": "B",
    "A13_Water_lake[We]": "B",
    "A13_fog[D]_Alp": "DSBX",
    "A13_musi_02[DSB]_edge_": "DSBX",
    "A13_waterfall[DSB]_Alp": "DSB",
    "A13_waterfall[DSB]_Alp_sc1.8": "DSB",
    "A13_waterfall[DSB]_Alp_sc2": "DSB",
    "A14_lava_M[DB]": "DSBX",
    "A14_lava_M[DB]alp": "DSBX",
    "A14_lava_M_02[DB]": "DSBX",
    "A14_lava_M_03[DB]": "DSBX",
    "A14_numa": "DBB",
    "A14_numa2": "DSBBB",
    "A15_BG_cloud[Dn]_Alp": "DX",
    "A15_M[D]": "DSBX",
    "A15_Stainedglass[DSB]_Alp": "DSBX",
    "A15_Tar": "DSBBB",
    "A15_Water_river[We]": "B",
    "A16_M[DBH][M]_Spec": "DSBMXH",
    "A16_M[DB]_Edge_Spec": "DSBX",
    "A16_M[DB]_fix": "DSBX",
    "A16_M_9Glass[DSBH][M]_Spec": "DSBMX",
    "A16_M_9Glass[DSB][M]_Spec": "DSBM",
    "A16_M_9Glass[DSB]_Alp_Spec": "DSB",
    "A16_M_9Glass[DSB]_Spec": "DSB",
    "A16_M_9Glass[DS]_Spec": "DSBX",
    "A16_Water_lake[We]": "B",
    "A16_Water_pool[We]": "B",
    "A16_light_shaft[Dn]_Add": "D",
    "A16_mist[Dn]_Alp": "D",
    "A17_BG_cloud[Dn]_Add": "D",
    "A17_BG_shaft[Dn]_Add_LS": "D",
    "A17_Crystal[DSB]": "DSBX",
    "A17_Crystal[DSB][L]": "DSBLX",
    "A17_Crystal[DSB][L]_Alp": "DSBLX",
    "A17_Crystal[DSB]_Alp": "DSBX",
    "A17_Crystal[DSB]_Edge": "DSBX",
    "A17_Ground[DSB][L]": "DSBLX",
    "A17_Ground[DSB][L]_Alp": "DSBLX",
    "A17_Light[D]": "DSBX",
    "A17_RustyMetal2[DSB][L]_DetB": "DSBLX",
    "A17_Sky[Dn]_LS": "DX",
    "A18_M[DB][L]_Spec": "DSBLX",
    "A18_M_1Wood[DSB][L]_Alp_Spec": "DSBL",
    "A18_M_1Wood[DSB][ML]_Spec": "DSBML",
    "A18_M_9Glass[DSB][ML]_Spec": "DSBML",
    "A18_Sky[Dn]": "DX",
    "A18_WhitePassage[Dn]": "DX",
    "A18_cloud[Dn]_Alp": "DX",
    "A19_BG_shaft[Dn]_Add": "D",
    "A19_Division[D]_Alp": "DSBX",
    "A19_Fly[DSB]_edge": "DSBX",
    "A19_Sky[Dn]": "DX",
    "A19_Snow[L]": "DSBBBL",
    "A19_cloud[Dn]_Alp": "DX",
    "A19_insect[DSB]_edge": "DSBLX",
    "A19_mountains[Dn]_Edge": "DX",
    "A_17_M[DB][L]": "DSBLX",
    "A_17_M_4Stone[DSB]": "DSB",
    "A_17_M_4Stone[DSB][L]": "DSBL",
    "A_17_M_4Stone[DSB][L]_Alp": "DSBL",
    "A_17_M_4Stone[DSB][L]_Alp_a": "DSBL",
    "A_17_M_4Stone[DS]": "DSBX",
    "A_17_M_4Stone[DS][L]": "DSBLX",
    "A_17_M_4Stone[DS][L]_Alp": "DSBLX",
    "A_18_M[DB][L]_Spec": "DSBLX",
    "A_18_M_4Stone[DSB][L]_Spec": "DSBL",
    "A_19_M[DB][L]_Alp_Spec": "DSBLX",
    "A_19_M[DB][L]_Spec": "DSBLX",
    "A_19_M[DB][ML]": "DSBMLX",
    "A_19_M[DB][ML]_Spec": "DSBMLX",
    "A_19_M_4Stone[DSB][L]_Alp_Spec": "DSBL",
    "A_19_M_4Stone[DSB][L]_Spec": "DSBL",
    "A_19_M_4Stone[DSB][ML]": "DSBML",
    "A_19_M_9Glass[DSB][L]_Spec": "DSBL",
    "A_19_M_9Glass[DSB][ML]_Spec": "DSBML",
    "C5250_Fire[D]_Add": "DX",
    "C[DN]": "DSBX",
    "C[D]": "DX",
    "C[D]_Alp": "DSBX",
    "C_2231_Body[DSB]": "DSBX",
    "C_2320_Metal[DSB]": "DSBX",
    "C_2320_Metal[DSB]_Spec": "DSBX",
    "C_2680_Ghost[DSB]_Add_Depth_Edge": "DSBX",
    "C_2680_Ghost[DSB]__Add_Depth": "DSBX",
    "C_2710_Metal[DSB]": "DSBX",
    "C_2711_Metal[DSB]_Spec": "DSBX",
    "C_3230_MoonlightLeather[DSB]": "DSBX",
    "C_3230_MoonlightLeather[DSB]_Edge": "DSBX",
    "C_3460_Metal[DSB]": "DSBX",
    "C_3461_Metal[DSB]": "DSBX",
    "C_3500_Slime[DSB]": "DSBX",
    "C_3530_Unique_Wet[DSB]": "DSBX",
    "C_3530_Unique_Wet[DSB]_Edge": "DSBX",
    "C_4500_DarkArm[D]_Sub": "DSBMX",
    "C_4500_Eyes1[DSB]": "DSBX",
    "C_4500_Eyes2[DSB]_Alp": "DSBX",
    "C_5230_Unique[DSB]": "DSBX",
    "C_5250_Fire_DullLeather[DSB]": "DSBX",
    "C_5260_Leather[DSB]": "DSBX",
    "C_5260_Leather[DSB]_Spec": "DSBX",
    "C_5280_Eyes[DSB]": "DSBX",
    "C_5290_Body[DSB]": "DSBX",
    "C_5290_Body[DSB][M]_Spec": "DSBMX",
    "C_5290_Body[DSB]_Spec": "DSBX",
    "C_5290_Wing[DSB]_Alp_Spec": "DSBX",
    "C_5350_body[DSB]": "DSBX",
    "C_5350_body[DSB]_Spec": "DSBX",
    "C_5370_DullLeather[DSB]_Edge": "DSBX",
    "C_5400_Unique[DSB]": "DSBX",
    "C_DullLeatherUnShine[DSB]": "DSBX",
    "C_DullLeatherUnShine[DSB]_Edge": "DSBX",
    "C_DullLeather[DSBT]": "DSBXT",
    "C_DullLeather[DSB]": "DSBX",
    "C_DullLeather[DSB]_Alp": "DSBX",
    "C_DullLeather[DSB]_Alp_Spec": "DSBX",
    "C_DullLeather[DSB]_Edge": "DSBX",
    "C_DullLeather[DSB]_Edge_Spec": "DSBX",
    "C_DullLeather[DSB]_Spec": "DSBX",
    "C_Fire_DullLeather[DSB]": "DSBX",
    "C_Fire_DullLeather[DSB]_Edge": "DSBX",
    "C_Leather[DSBT]_Edge": "DSBXT",
    "C_Leather[DSB]": "DSBX",
    "C_Leather[DSB]_Alp": "DSBX",
    "C_Leather[DSB]_Alp_Spec": "DSBX",
    "C_Leather[DSB]_Edge": "DSBX",
    "C_Leather[DSB]_Edge_Spec": "DSBX",
    "C_Leather[DSB]_Spec": "DSBX",
    "C_Metal[DSB]": "DSBX",
    "C_Metal[DSB]_Alp": "DSBX",
    "C_Metal[DSB]_Alp_Spec": "DSBX",
    "C_Metal[DSB]_Edge": "DSBX",
    "C_Metal[DSB]_Edge_Spec": "DSBX",
    "C_Metal[DSB]_Spec": "DSBX",
    "C_RoughCloth[DSB]": "DSBX",
    "C_RoughCloth[DSB]_Edge_Spec": "DSBX",
    "C_Wet[DSBT]": "DSBXT",
    "C_Wet[DSBT]_Edge": "DSBXT",
    "C_Wet[DSB]": "DSBX",
    "C_Wet[DSB][M]": "DSBMX",
    "C_Wet[DSB]_Alp": "DSBX",
    "C_Wet[DSB]_Alp_Spec": "DSBX",
    "C_Wet[DSB]_Edge": "DSBX",
    "C_Wet[DSB]_Edge_Spec": "DSBX",
    "C_Wet[DSB]_Spec": "DSBX",
    "C_Wet[DSB]_spec": "DSBX",
    "M[DBH]": "DSBXH",
    "M[DBH][L]": "DSBLH",
    "M[DBH][L]_Alp": "DSBLH",
    "M[DBH][M]": "DSBMXH",
    "M[DB]": "DBX",
    "M[DB][L]": "DSBL",
    "M[DB][L]_Alp": "DBLX",
    "M[DB][L]_DetB": "DSBLX",
    "M[DB][L]_Edge": "DBLX",
    "M[DB][ML]": "DSBMLX",
    "M[DB][M]": "DSBMX",
    "M[DB]_Alp": "DBX",
    "M[DB]_Edge": "DSBX",
    "M[DH][ML]": "DSBMLXH",
    "M[D]": "DX",
    "M[D][L]": "DLX",
    "M[D][L]_Alp": "DLX",
    "M[D][L]_DetB": "DSBLX",
    "M[D][L]_Edge": "DLX",
    "M[D][ML]": "DSBMLX",
    "M[D][M]": "DMX",
    "M[D]_Alp": "DX",
    "M[D]_Edge": "DX",
    "M_1Wood[DSB]": "DSB",
    "M_1Wood[DSB][L]": "DSBL",
    "M_1Wood[DSB][L]_Alp": "DSBL",
    "M_1Wood[DSB][L]_Edge": "DSBL",
    "M_1Wood[DSB][ML]": "DSBML",
    "M_1Wood[DSB]_Alp": "DSB",
    "M_1Wood[DSB]_Edge": "DSB",
    "M_1Wood[DS]": "DSBX",
    "M_1Wood[DS][L]": "DSLX",
    "M_1Wood[DS][L]_Alp": "DSBLX",
    "M_2Foliage[DSB]": "DSBX",
    "M_2Foliage[DSB][L]": "DSBLX",
    "M_2Foliage[DSB][L]_Edge": "DSBLX",
    "M_2Foliage[DSB]_Edge": "DSBX",
    "M_3Ivy[DSB][L]_Edge": "DSBLX",
    "M_3Ivy[DSB]_Edge": "DSBX",
    "M_4Stone[DSB]": "DSB",
    "M_4Stone[DSB][L]": "DSBL",
    "M_4Stone[DSB][L]_Alp": "DSBL",
    "M_4Stone[DSB][L]_Edge": "DSBL",
    "M_4Stone[DSB][ML]": "DSBML",
    "M_4Stone[DSB][M]": "DSBM",
    "M_4Stone[DSB]_Alp": "DSB",
    "M_4Stone[DSB]_Edge": "DSB",
    "M_4Stone[DS]": "DSBX",
    "M_4Stone[DS][L]": "DSBLX",
    "M_4Stone[DS][L]_Alp": "DSBLX",
    "M_5Water[B]": "B",
    "M_7Metal[DSB]": "DSB",
    "M_7Metal[DSB][L]": "DSBL",
    "M_7Metal[DSB][L]_Alp": "DSBL",
    "M_7Metal[DSB][L]_DetB": "DSBLX",
    "M_7Metal[DSB][L]_Edge": "DSBL",
    "M_7Metal[DSB][M]": "DSBM",
    "M_7Metal[DSB]_DetB": "DSBX",
    "M_7Metal[DS]": "DSX",
    "M_7Metal[DS][L]": "DSBLX",
    "M_7Metal[DS][L]_Alp": "DSBLX",
    "M_7Metal[DS][ML]": "DSBMLX",
    "M_7Metal[DS][M]": "DSMX",
    "M_8Snow": "DBB",
    "M_9Glass[DSB]": "DSB",
    "M_9Glass[DSB][L]": "DSBL",
    "M_9Glass[DSB][L]_Alp": "DSBL",
    "M_9Glass[DSB][L]_Edge": "DSBL",
    "M_9Glass[DSB][ML]": "DSBML",
    "M_9Glass[DSB][M]": "DSBM",
    "M_9Glass[DSB]_Alp": "DSB",
    "M_9Glass[DSB]_Edge": "DSB",
    "M_9Glass[DS]": "DSBX",
    "M_9Glass[DS][L]": "DSBLX",
    "M_Sky[Dn]": "D",
    "M_Tree[D]_Edge": "D",
    "P_DullLeather[DSB]": "DSBX",
    "P_DullLeather[DSB]_Edge": "DSBX",
    "P_Leather[DSB]": "DSBX",
    "P_Leather[DSB]_Alp": "DSBX",
    "P_Leather[DSB]_Edge": "DSBX",
    "P_Leather[DS]": "DSBX",
    "P_Metal[DSB]": "DSBX",
    "P_Metal[DSB]_Edge": "DSBX",
    "P_Metal[DSB]_Spec": "DSBX",
    "P_Wet[DSB]": "DSBX",
    "Ps_Body[DSB]": "DSBX",
    "Ps_Hair[DS]": "DSX",
    "Ps_Hair[DS]_Alp": "DSX",
    "Ps_Hair[DS]_Edge": "DSBX",
    "Ps_Wander_Ghost": "DBD",
    "S[D]_Add": "D",
    "S[NL]": "D",
}


LAYOUT_ABBREVIATIONS = {
    "Position<12, Float3>": "P",
    "BoneIndices<4, Byte4B>": "BI",
    "BoneWeights<8, Short4ToFloat4A>": "BW",
    "Normal<4, Byte4C>": "N",
    "Tangent<4, Byte4C>": "T",
    "Bitangent<4, Byte4C>": "BT",
    "VertexColor<4, Byte4C>": "C",
    "UV<4, UV>": "UV",
    "UV<8, UVPair>": "UVPair",
}


CHR_MTD_LAYOUTS = {
    "C_Leather[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_Leather[DSB]_Alp_Spec.mtd": CHR_DEFAULT,
    "C_DullLeather[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_Wet[DSB]_Spec.mtd": CHR_DEFAULT,
    "P_Metal[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_DullLeather[DSB]_Alp_Spec.mtd": CHR_DEFAULT,
    "P_Metal[DSB].mtd": CHR_DEFAULT,
    "C_Wet[DSB].mtd": CHR_DEFAULT,
    "C_Wet[DSB]_Edge.mtd": CHR_DEFAULT,
    "P_DullLeather[DSB]_Edge.mtd": CHR_DEFAULT,
    "C_DullLeather[DSB].mtd": {'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>', 'Position<12, Float3>, BoneIndices<4, Byte4B>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>'},
    "C_DullLeather[DSB]_Edge.mtd": {'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>', 'Position<12, Float3>, BoneIndices<4, Byte4B>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>'},
    "P_Wet[DSB].mtd": CHR_DEFAULT,
    "P_DullLeather[DSB].mtd": CHR_DEFAULT,
    "C_2231_Body[DSB].mtd": CHR_DEFAULT,
    "C_Fire_DullLeather[DSB].mtd": CHR_DEFAULT,
    "C_Leather[DSB].mtd": CHR_DEFAULT,
    "C_Leather[DSB]_Edge.mtd": CHR_DEFAULT,
    "C_RoughCloth[DSB].mtd": CHR_DEFAULT,
    "C_Leather[DSB]_Alp.mtd": CHR_DEFAULT,
    "C_DullLeather[DSB]_Alp.mtd": CHR_DEFAULT,
    "C_Wet[DSBT].mtd": CHR_DEFAULT,
    "C_Wet[DSBT]_Edge.mtd": CHR_DEFAULT,
    "C_DullLeatherUnShine[DSB].mtd": CHR_DEFAULT,
    "C_Metal[DSB]_Edge.mtd": CHR_DEFAULT,
    "C_2320_Metal[DSB].mtd": CHR_DEFAULT,
    "C_DullLeather[DSB]_Edge_Spec.mtd": CHR_DEFAULT,
    "C_Metal[DSB].mtd": CHR_DEFAULT,
    "P_Metal[DSB]_Edge.mtd": CHR_DEFAULT,
    "P_Leather[DSB].mtd": CHR_DEFAULT,
    "M_4Stone[DSB].mtd": CHR_DEFAULT,
    "C_DullLeatherUnShine[DSB]_Edge.mtd": CHR_DEFAULT,
    # BoneWeights, Tangents optional?
    "C[D].mtd": {'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>', 'Position<12, Float3>, BoneIndices<4, Byte4B>, Normal<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>', 'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>'},
    "Ps_Wander_Ghost.mtd": CHR_DEFAULT,
    "C_DullLeather[DSBT].mtd": CHR_DEFAULT,
    "C_2680_Ghost[DSB]__Add_Depth.mtd": CHR_DEFAULT,
    "C_2680_Ghost[DSB]_Add_Depth_Edge.mtd": CHR_DEFAULT,
    "C_2710_Metal[DSB].mtd": CHR_DEFAULT,
    "P_Leather[DSB]_Alp.mtd": CHR_DEFAULT,
    "Ps_Body[DSB].mtd": CHR_DEFAULT,
    "Ps_Hair[DS].mtd": {'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>', 'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>'},
    "Ps_Hair[DS]_Alp.mtd": {'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, Tangent<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>', 'Position<12, Float3>, BoneIndices<4, Byte4B>, BoneWeights<8, Short4ToFloat4A>, Normal<4, Byte4C>, VertexColor<4, Byte4C>, UV<4, UV>'},
    "P_Leather[DSB]_Edge.mtd": CHR_DEFAULT,
    "C_2711_Metal[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_Metal[DSB]_Alp_Spec.mtd": CHR_DEFAULT,
    "Ps_Hair[DS]_Edge.mtd": CHR_DEFAULT,
    "C_Wet[DSB][M].mtd": CHR_UV_PAIR_BITANGENT_LAYOUT,
    "M[DB][M].mtd": CHR_UV_PAIR_BITANGENT_LAYOUT,
    "P_Leather[DS].mtd": CHR_DEFAULT,
    "C_Wet[DSB]_Alp.mtd": CHR_DEFAULT,
    "C_Wet[DSB]_Alp_Spec.mtd": CHR_DEFAULT,
    "C_Wet[DSB]_spec.mtd": CHR_DEFAULT,
    "C_3230_MoonlightLeather[DSB]_Edge.mtd": CHR_DEFAULT,
    "C_3230_MoonlightLeather[DSB].mtd": CHR_DEFAULT,
    "C_Wet[DSB]_Edge_Spec.mtd": CHR_DEFAULT,
    "C_5260_Leather[DSB].mtd": CHR_DEFAULT,
    "C_Leather[DSBT]_Edge.mtd": CHR_DEFAULT,
    "C_3460_Metal[DSB].mtd": CHR_DEFAULT,
    "C_Metal[DSB]_Edge_Spec.mtd": CHR_DEFAULT,
    "C_Metal[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_3461_Metal[DSB].mtd": CHR_DEFAULT,
    "C_Leather[DSB]_Edge_Spec.mtd": CHR_DEFAULT,
    "C[DN].mtd": CHR_DEFAULT,
    "C_3500_Slime[DSB].mtd": CHR_DEFAULT,
    "C_Metal[DSB]_Alp.mtd": CHR_DEFAULT,
    "C_3530_Unique_Wet[DSB].mtd": CHR_DEFAULT,
    "C_3530_Unique_Wet[DSB]_Edge.mtd": CHR_DEFAULT,
    "M_4Stone[DSB][M].mtd": CHR_UV_PAIR_BITANGENT_LAYOUT,
    "C_4500_Eyes1[DSB].mtd": CHR_DEFAULT,
    "C_4500_DarkArm[D]_Sub.mtd": CHR_UV_PAIR_BITANGENT_LAYOUT,
    "C_4500_Eyes2[DSB]_Alp.mtd": CHR_DEFAULT,
    "C_Fire_DullLeather[DSB]_Edge.mtd": CHR_DEFAULT,
    "C[D]_Alp.mtd": CHR_DEFAULT,
    "C_5230_Unique[DSB].mtd": CHR_DEFAULT,
    "C_5250_Fire_DullLeather[DSB].mtd": CHR_DEFAULT,
    "C_5260_Leather[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_5280_Eyes[DSB].mtd": CHR_DEFAULT,
    "C_5290_Body[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_5290_Wing[DSB]_Alp_Spec.mtd": CHR_DEFAULT,
    "C_5290_Body[DSB][M]_Spec.mtd": CHR_UV_PAIR_BITANGENT_LAYOUT,
    "C_5290_Body[DSB].mtd": CHR_DEFAULT,
    "C_5350_body[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_RoughCloth[DSB]_Edge_Spec.mtd": CHR_DEFAULT,
    "C_2320_Metal[DSB]_Spec.mtd": CHR_DEFAULT,
    "C_5350_body[DSB].mtd": CHR_DEFAULT,
    "C_5370_DullLeather[DSB]_Edge.mtd": CHR_DEFAULT,
    "C_5400_Unique[DSB].mtd": CHR_DEFAULT,
    "C5250_Fire[D]_Add.mtd": CHR_DEFAULT,
    "M_1Wood[DSB].mtd": CHR_DEFAULT,
    "M_1Wood[DSB]_Edge.mtd": CHR_DEFAULT,
    "A15_Stainedglass[DSB]_Alp.mtd": CHR_DEFAULT,
    "A12_NewWater.mtd": CHR_DEFAULT,
}


MAP_MTD_LAYOUTS = {
   "A10_00_Water_slope.mtd": MAP_DEFAULT,
   "A10_01_Water[B].mtd": MAP_DEFAULT,
   "A10_02_m9000_M[D].mtd": MAP_DEFAULT,
   "A10_02_m9000_Sky[Dn]_LS.mtd": MAP_DEFAULT_NO_TANGENT,
   "A10_02_m9000_cloud[DB]_Alp.mtd": MAP_DEFAULT,
   "A10_BG_cloud[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A10_BG_shaft[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A10_BG_shaft[Dn]_Add_LS.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "A10_M_4Stone[DSB][L]_Alp_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A10_Metal[DS][L].mtd": MAP_DEFAULT_UVPAIR,
   "A10_Sky[Dn].mtd": MAP_DEFAULT_NO_TANGENT,
   "A10_Sky[Dn]_LS.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "A10_Sky_Night[Dn].mtd": MAP_DEFAULT_NO_TANGENT,
   "A10_Stone[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A10_Stone[DSB][L]_DetB.mtd": MAP_DEFAULT_UVPAIR,
   "A10_Water_lake[We].mtd": MAP_DEFAULT,
   "A10_Water_sewer2[We].mtd": MAP_DEFAULT,
   "A10_Water_sewer3[We].mtd": MAP_DEFAULT,
   "A10_Water_sewer4[We].mtd": MAP_DEFAULT,
   "A10_Water_sewer[We].mtd": MAP_DEFAULT,
   "A10_Watercourse[We].mtd": MAP_DEFAULT,
   "A10_Wet[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A10_cloud[DB]_Alp.mtd": MAP_DEFAULT,
   "A10_cloud[Dn]_Add.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "A10_lightshaft[Dn]_Add.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "A10_mist[Dn]_Alp.mtd": MAP_DEFAULT_NO_TANGENT,
   "A10_mist_02[Dn]_Alp.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "A10_muddiness[D]_Edge.mtd": MAP_DEFAULT,
   "A10_slime[D][L].mtd": MAP_DEFAULT_UVPAIR,
   "A10_slime[D][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "A10_sludge[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A10_sludge[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A10_waterfall[DSB]_Alp.mtd": MAP_DEFAULT,
   "A11_Sky[Dn].mtd": MAP_DEFAULT_NO_TANGENT,
   "A11_Snow.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, T, C, UVPair'},
   "A11_Snow[L].mtd": MAP_DEFAULT_UVPAIR,
   "A11_Snow_stair.mtd": MAP_DEFAULT,
   "A11_Snow_stair[L].mtd": MAP_DEFAULT_UVPAIR,
   "A11_Water[W].mtd": MAP_DEFAULT,
   "A11_cloud[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A11_lightshaft[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A12_DarkRiver.mtd": MAP_DEFAULT,
   "A12_DarkWater.mtd": MAP_DEFAULT,
   "A12_Grass[DS][L]_Edg.mtd": {'P, BI, N, T, C, UVPair', 'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, VertexColor<4, Byte4A>, UVPair', 'P, BI, N, C, UVPair'},
   "A12_Grass[D][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "A12_Ground[DSB].mtd": MAP_DEFAULT,
   "A12_Ground[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A12_Ground[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A12_Ground[DSB]_Alp.mtd": MAP_DEFAULT,
   "A12_Ground[D[L]].mtd": MAP_DEFAULT_UVPAIR,
   "A12_Ground[D].mtd": MAP_DEFAULT,
   "A12_Little River.mtd": MAP_DEFAULT,
   "A12_Little waterfall[DSB]_Alp.mtd": MAP_DEFAULT,
   "A12_NewWater.mtd": MAP_DEFAULT,
   "A12_River_No reflect.mtd": MAP_DEFAULT,
   "A12_Wall+Ground[DSB][M][L].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "A12_Wall[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A12_Water.mtd": MAP_DEFAULT,
   "A12_Water_boss.mtd": MAP_DEFAULT,
   "A12_Water_lake.mtd": MAP_DEFAULT,
   "A12_Wet Ground[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A12_waterfall[DSB]_Alp.mtd": MAP_DEFAULT,
   "A13_M[D]_Alp.mtd": MAP_DEFAULT,
   "A13_Water_B1syounyuu[We].mtd": MAP_DEFAULT,
   "A13_Water_lake3[We].mtd": MAP_DEFAULT,
   "A13_Water_lake[We].mtd": MAP_DEFAULT,
   "A13_fog[D]_Alp.mtd": MAP_DEFAULT,
   "A13_musi_02[DSB]_edge_.mtd": MAP_DEFAULT,
   "A13_waterfall[DSB]_Alp.mtd": MAP_DEFAULT,
   "A13_waterfall[DSB]_Alp_sc1.8.mtd": MAP_DEFAULT,
   "A13_waterfall[DSB]_Alp_sc2.mtd": MAP_DEFAULT,
   "A14_lava_M[DB].mtd": MAP_DEFAULT,
   "A14_lava_M[DB]alp.mtd": MAP_DEFAULT,
   "A14_lava_M_02[DB].mtd": MAP_DEFAULT,
   "A14_lava_M_03[DB].mtd": MAP_DEFAULT,
   "A14_numa.mtd": MAP_DEFAULT,
   "A14_numa2.mtd": MAP_DEFAULT,
   "A15_BG_cloud[Dn]_Alp.mtd": MAP_DEFAULT_NO_TANGENT,
   "A15_M[D].mtd": MAP_DEFAULT,
   "A15_Stainedglass[DSB]_Alp.mtd": MAP_DEFAULT,
   "A15_Tar.mtd": MAP_DEFAULT,
   "A15_Water_river[We].mtd": MAP_DEFAULT,
   "A16_M[DBH][M]_Spec.mtd": "P, BI, N, T, BT, C, UVPair",
   "A16_M[DB]_Edge_Spec.mtd": MAP_DEFAULT,
   "A16_M[DB]_fix.mtd": MAP_DEFAULT,
   "A16_M_9Glass[DSBH][M]_Spec.mtd": "P, BI, N, T, BT, C, UVPair",
   "A16_M_9Glass[DSB][M]_Spec.mtd": "P, BI, N, T, BT, C, UVPair",
   "A16_M_9Glass[DSB]_Alp_Spec.mtd": MAP_DEFAULT,
   "A16_M_9Glass[DSB]_Spec.mtd": MAP_DEFAULT,
   "A16_M_9Glass[DS]_Spec.mtd": MAP_DEFAULT,
   "A16_Water_lake[We].mtd": MAP_DEFAULT,
   "A16_Water_pool[We].mtd": MAP_DEFAULT,
   "A16_light_shaft[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A16_mist[Dn]_Alp.mtd": MAP_DEFAULT_NO_TANGENT,
   "A17_BG_cloud[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A17_BG_shaft[Dn]_Add_LS.mtd": MAP_DEFAULT_NO_TANGENT,
   "A17_Crystal[DSB].mtd": MAP_DEFAULT,
   "A17_Crystal[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A17_Crystal[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A17_Crystal[DSB]_Alp.mtd": MAP_DEFAULT,
   "A17_Crystal[DSB]_Edge.mtd": MAP_DEFAULT,
   "A17_Ground[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A17_Ground[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A17_Light[D].mtd": MAP_DEFAULT,
   "A17_RustyMetal2[DSB][L]_DetB.mtd": MAP_DEFAULT_UVPAIR,
   "A17_Sky[Dn]_LS.mtd": MAP_DEFAULT_NO_TANGENT,
   "A18_M[DB][L]_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A18_M_1Wood[DSB][L]_Alp_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A18_M_1Wood[DSB][ML]_Spec.mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "A18_M_9Glass[DSB][ML]_Spec.mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "A18_Sky[Dn].mtd": MAP_DEFAULT_NO_TANGENT,
   "A18_WhitePassage[Dn].mtd": MAP_DEFAULT_NO_TANGENT,
   "A18_cloud[Dn]_Alp.mtd": MAP_DEFAULT_NO_TANGENT,
   "A19_BG_shaft[Dn]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "A19_Division[D]_Alp.mtd": MAP_DEFAULT,
   "A19_Fly[DSB]_edge.mtd": MAP_DEFAULT,
   "A19_Sky[Dn].mtd": MAP_DEFAULT_NO_TANGENT,
   "A19_Snow[L].mtd": MAP_DEFAULT_UVPAIR,
   "A19_cloud[Dn]_Alp.mtd": MAP_DEFAULT_NO_TANGENT,
   "A19_insect[DSB]_edge.mtd": MAP_DEFAULT_UVPAIR,
   "A19_mountains[Dn]_Edge.mtd": MAP_DEFAULT_NO_TANGENT,
   "A_17_M[DB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A_17_M_4Stone[DSB].mtd": MAP_DEFAULT,
   "A_17_M_4Stone[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "A_17_M_4Stone[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A_17_M_4Stone[DSB][L]_Alp_a.mtd": MAP_DEFAULT_UVPAIR,
   "A_17_M_4Stone[DS].mtd": MAP_DEFAULT,
   "A_17_M_4Stone[DS][L].mtd": MAP_DEFAULT_UVPAIR,
   "A_17_M_4Stone[DS][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "A_18_M[DB][L]_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_18_M_4Stone[DSB][L]_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_19_M[DB][L]_Alp_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_19_M[DB][L]_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_19_M[DB][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "A_19_M[DB][ML]_Spec.mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "A_19_M_4Stone[DSB][L]_Alp_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_19_M_4Stone[DSB][L]_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_19_M_4Stone[DSB][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "A_19_M_9Glass[DSB][L]_Spec.mtd": MAP_DEFAULT_UVPAIR,
   "A_19_M_9Glass[DSB][ML]_Spec.mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "C5250_Fire[D]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "C[D].mtd": MAP_DEFAULT,
   "C_5230_Unique[DSB].mtd": MAP_DEFAULT,
   "C_DullLeather[DSB].mtd": MAP_DEFAULT,
   "C_DullLeather[DSB]_Edge.mtd": MAP_DEFAULT,
   "C_Leather[DSB].mtd": MAP_DEFAULT,
   "C_Leather[DSB]_Edge.mtd": MAP_DEFAULT,
   "C_Metal[DSB].mtd": MAP_DEFAULT,
   "C_Metal[DSB]_Edge.mtd": MAP_DEFAULT,
   "M[DBH].mtd": MAP_DEFAULT,
   "M[DBH][L].mtd": MAP_DEFAULT_UVPAIR,
   "M[DBH][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M[DBH][M].mtd": "P, BI, N, T, BT, C, UVPair",
   "M[DB].mtd": MAP_DEFAULT,
   "M[DB][L].mtd": {'P, BI, N, T, C, UVPair', 'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, Tangent<4, Byte4A>, VertexColor<4, Byte4A>, UVPair'},
   "M[DB][L]_Alp.mtd": {'P, BI, N, T, C, UVPair', 'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, Tangent<4, Byte4A>, VertexColor<4, Byte4A>, UVPair'},
   "M[DB][L]_DetB.mtd": MAP_DEFAULT_UVPAIR,
   "M[DB][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "M[DB][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M[DB][M].mtd": "P, BI, N, T, BT, C, UVPair",
   "M[DB]_Alp.mtd": MAP_DEFAULT,
   "M[DB]_Edge.mtd": MAP_DEFAULT,
   "M[DH][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M[D].mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "M[D][L].mtd": {'P, BI, N, T, C, UVPair', 'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, VertexColor<4, Byte4A>, UVPair', 'P, BI, N, C, UVPair'},
   "M[D][L]_Alp.mtd": {'P, BI, N, T, C, UVPair', 'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, VertexColor<4, Byte4A>, UVPair', 'P, BI, N, C, UVPair'},
   "M[D][L]_DetB.mtd": MAP_DEFAULT_UVPAIR,
   "M[D][L]_Edge.mtd": {'P, BI, N, T, C, UVPair', 'P, BI, N, C, UVPair'},
   "M[D][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M[D][M].mtd": {'P, BI, N, T, BT, C, UVPair', 'P, BI, N, C, UVPair'},
   "M[D]_Alp.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "M[D]_Edge.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "M_1Wood[DSB].mtd": MAP_DEFAULT,
   "M_1Wood[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_1Wood[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_1Wood[DSB][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "M_1Wood[DSB][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M_1Wood[DSB]_Alp.mtd": MAP_DEFAULT,
   "M_1Wood[DSB]_Edge.mtd": MAP_DEFAULT,
   "M_1Wood[DS].mtd": MAP_DEFAULT,
   "M_1Wood[DS][L].mtd": {'P, BI, N, T, C, UVPair', 'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, VertexColor<4, Byte4A>, UVPair', 'P, BI, N, C, UVPair'},
   "M_1Wood[DS][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_2Foliage[DSB].mtd": "P, BI, N, T, C, UV, UVPair",
   "M_2Foliage[DSB][L].mtd": "P, BI, N, T, C, UVPair, UVPair",
   "M_2Foliage[DSB][L]_Edge.mtd": "P, BI, N, T, C, UVPair, UVPair",
   "M_2Foliage[DSB]_Edge.mtd": "P, BI, N, T, C, UV, UVPair",
   "M_3Ivy[DSB][L]_Edge.mtd": "P, BI, N, T, C, UVPair, UVPair",
   "M_3Ivy[DSB]_Edge.mtd": {'P, BI, N, T, C, UV, UVPair', 'P, BI, N, T, C, UVPair, UVPair'},
   "M_4Stone[DSB].mtd": MAP_DEFAULT,
   "M_4Stone[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_4Stone[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_4Stone[DSB][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "M_4Stone[DSB][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M_4Stone[DSB][M].mtd": "P, BI, N, T, BT, C, UVPair",
   "M_4Stone[DSB]_Alp.mtd": {'P, BoneIndices<4, Byte4E>, Normal<4, Byte4A>, Tangent<4, Byte4A>, VertexColor<4, Byte4A>, UV', 'P, BI, N, T, C, UV'},
   "M_4Stone[DSB]_Edge.mtd": MAP_DEFAULT,
   "M_4Stone[DS].mtd": MAP_DEFAULT,
   "M_4Stone[DS][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_4Stone[DS][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_5Water[B].mtd": MAP_DEFAULT,
   "M_7Metal[DSB].mtd": MAP_DEFAULT,
   "M_7Metal[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_7Metal[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_7Metal[DSB][L]_DetB.mtd": MAP_DEFAULT_UVPAIR,
   "M_7Metal[DSB][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "M_7Metal[DSB][M].mtd": "P, BI, N, T, BT, C, UVPair",
   "M_7Metal[DSB]_DetB.mtd": MAP_DEFAULT,
   "M_7Metal[DS].mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "M_7Metal[DS][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_7Metal[DS][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_7Metal[DS][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M_7Metal[DS][M].mtd": "P, BI, N, C, UVPair",
   "M_8Snow.mtd": MAP_DEFAULT,
   "M_9Glass[DSB].mtd": MAP_DEFAULT,
   "M_9Glass[DSB][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_9Glass[DSB][L]_Alp.mtd": MAP_DEFAULT_UVPAIR,
   "M_9Glass[DSB][L]_Edge.mtd": MAP_DEFAULT_UVPAIR,
   "M_9Glass[DSB][ML].mtd": "P, BI, N, T, BT, C, UVPair, UV",
   "M_9Glass[DSB][M].mtd": "P, BI, N, T, BT, C, UVPair",
   "M_9Glass[DSB]_Alp.mtd": MAP_DEFAULT,
   "M_9Glass[DSB]_Edge.mtd": MAP_DEFAULT,
   "M_9Glass[DS].mtd": MAP_DEFAULT,
   "M_9Glass[DS][L].mtd": MAP_DEFAULT_UVPAIR,
   "M_Sky[Dn].mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "M_Tree[D]_Edge.mtd": {'P, BI, N, T, C, UV', 'P, BI, N, C, UV'},
   "S[D]_Add.mtd": MAP_DEFAULT_NO_TANGENT,
   "S[NL].mtd": MAP_DEFAULT,
}


"""
BUFFER LAYOUT RULES for MAP PIECES:
    - BoneWeights never used.
    - Tangents usually used, but sometimes omitted.
    - 'UV', 'UVPair', or 'UVPair, UV' used for standard, M | L, and M & L MTDs, respectively.
    - Bitangents used for most M MTDs.
        - But never used for non-M MTDs.
    - P, BI, N, C always used for all MTDs.
    - Standard formats for each layout member type (for DSR):
        Position<12, Float3>
        BoneIndices<4, Byte4B>
        BoneWeights<8, Short4ToFloat4A>
        Normal<4, Byte4C>
        Tangent<4, Byte4C>
        Bitangent<4, Byte4C>
        VertexColor<4, Byte4C>
        UV<4, UV>
        UV<8, UVPair>
    - Alternate formats are sometimes used, but those MTDs do always use the standard formats elsewhere.
    
    
"""


def alphabetize():
    print("MTD_DICT = {")
    for mtd in sorted(MTD_DICT):
        print(f"    \"{mtd}\": \"{MTD_DICT[mtd]}\",")
    print("}")


def abbreviate(layout_str: str):
    for long, short in LAYOUT_ABBREVIATIONS.items():
        layout_str = layout_str.replace(long, short)
    return layout_str


def scan_chr_layouts():
    """Find layout used by each chr FLVER submesh material."""
    mtd_and_layout = {}  # type: dict[str, set[str]]

    for chrbnd_path in VANILLA_CHR_PATH.glob("*.chrbnd.dcx"):
        if re.match(r"c[01]000", chrbnd_path.name):
            continue
        chrbnd = Binder.from_path(chrbnd_path)
        print(f"Reading FLVER in {chrbnd_path.name}...")
        flver = chrbnd[200].to_binary_file(FLVER)
        for submesh in flver.submeshes:
            material = submesh.material
            if material.mtd_name not in mtd_and_layout:
                mtd_and_layout[material.mtd_name] = set()
            layout = submesh.vertex_arrays[0].layout
            layout_str = ", ".join(str(m) for m in layout)
            mtd_and_layout[material.mtd_name].add(layout_str)

    print("{")
    for mtd_name, layouts in mtd_and_layout.items():
        if len(layouts) == 1:
            layout = next(iter(layouts))
            if layout == CHR_DEFAULT:
                layout = "STD_LAYOUT"
            print(f"   \"{mtd_name}\": \"{layout}\",")
        else:
            print(f"   \"{mtd_name}\": {layouts},")  # set of multiple
    print("}")


def scan_chr():
    mtd_and_texture_types = []

    for chrbnd_path in VANILLA_CHR_PATH.glob("*.chrbnd.dcx"):
        if re.match(r"c[01]000", chrbnd_path.name):
            continue
        chrbnd = Binder.from_path(chrbnd_path)
        print(f"Reading FLVER in {chrbnd_path.name}...")
        flver = chrbnd[200].to_binary_file(FLVER)
        for submesh in flver.submeshes:
            texture_types = [tex.texture_type for tex in submesh.material.textures]
            mtd_and_texture_types.append((Path(submesh.material.mtd_path).stem, texture_types))

    for mtd_texture_types in mtd_and_texture_types:
        print(mtd_texture_types)


def scan_map():

    with Path("map_mtd_textures.py").open("w") as f:
        f.write("MAP_MTD_DICT = {\n")
        for flver_path in VANILLA_MAP_PATH.rglob("*.flver.dcx"):
            if "m12_00_00_01" in str(flver_path):
                continue  # skip duplicate DLC directory (models are still read from _00 folder)
            print(f"Reading FLVER {flver_path.name}...")
            flver = FLVER.from_path(flver_path)
            for submesh in flver.submeshes:
                texture_types = [tex.texture_type for tex in submesh.material.textures]
                f.write(f"    ('{Path(submesh.material.mtd_path).stem}', {texture_types}),\n")
        f.write("}\n")


def scan_map_layouts():
    """Find layout used by each map FLVER submesh material."""
    mtd_and_layout = {}  # type: dict[str, set[str]]

    for flver_path in VANILLA_MAP_PATH.rglob("*.flver.dcx"):
        if "m12_00_00_01" in str(flver_path):
            continue  # skip duplicate DLC directory (models are still read from _00 folder)
        print(f"Reading FLVER {flver_path.name}...")
        flver = FLVER.from_path(flver_path)
        for submesh in flver.submeshes:
            material = submesh.material
            if material.mtd_name not in mtd_and_layout:
                mtd_and_layout[material.mtd_name] = set()
            layout = submesh.vertex_arrays[0].layout
            layout_str = ", ".join(str(m) for m in layout)
            mtd_and_layout[material.mtd_name].add(layout_str)

    print("{")
    for mtd_name in sorted(mtd_and_layout):
        layouts = mtd_and_layout[mtd_name]
        if len(layouts) == 1:
            layout = abbreviate(next(iter(layouts)))
            if layout == MAP_DEFAULT:
                print(f"   \"{mtd_name}\": MAP_DEFAULT,")
            elif layout == MAP_DEFAULT_UVPAIR:
                print(f"   \"{mtd_name}\": MAP_DEFAULT_UVPAIR,")
            else:
                print(f"   \"{mtd_name}\": \"{layout}\",")
        else:
            layouts = {abbreviate(layout) for layout in layouts}
            print(f"   \"{mtd_name}\": {layouts},")  # set of multiple
    print("}")


# TODO: Noting that map piece FLVER buffer layouts don't seem to even have bone weights.
#  That's probably the indicator I should use in Blender to write bones directly to pose, rather than edit?


if __name__ == '__main__':
    # scan_chr_layouts()
    # get_unique_mtds()
    scan_map_layouts()
    # alphabetize()

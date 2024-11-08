import struct
from pathlib import Path

from soulstruct import FLVER, ELDEN_RING_PATH
from soulstruct.base.models.matbin import MATBINBND

# TODO: Findings so far:
#  - Haven't seen a material that uses more than two GX Items, EXCLUDING the dummy item.
#  - In addition to the dummy item, EVERY material seems to have a ('GX00', 102) item with args:
#       (0, 0, 0, -1, 0, 0, 0, 0, 0, 0)


# NOTE: Some of these arg formats can't be confirmed (always zero) or of course, could be smaller than 4 bytes.
ER_GX_ITEM_MAPPING = {
    b"GXMD": {
        (131, 32): "3i5f",
        (131, 44): "3i5f2if",
        (132, 44): "3i5f2if",
        (133, 32): "3i5f",
        (133, 44): "3i5f2if",
        (137, 32): "3i5f",
        (162, 28): "3if3i",  # TODO: only args of GXMD not compatible with the others; suggests `index` DOES matter
        (192, 96): "3i5f2i5f2if2if2if",
        (400, 32): "3i5f",
    },
    b"GX00": {
        (102, 40): "10i",
    },
    b"GX05": {
        (100, 16): "f3i",  # TODO: only first arg confirmed
    }
}


def see_textures():
    """
    TODO:
        - To load Elden Ring map piece textures, for a given material:
            - Load the MATBIN for the map piece material (use batch `MATBINBND` instance).
            - Find the texture names. For each texture:
                - Open the relevant AET binder (obviously only open each one once for an import batch).
                - Get the DDS.
        - Note that the MATBIN texture names have '.tif' extension, which ER must convert DDS into instead of '.tga'.
        - So, I need a MATBIN class first. Thanks TKGP:
            https://github.com/JKAnderson/SoulsFormats/blob/er/SoulsFormats/Formats/MATBIN.cs
    """

    stormveil = Path(ELDEN_RING_PATH + "/map/m10/m10_00_00_00/")
    for mapbnd_path in stormveil.glob("*.mapbnd.dcx"):
        flver = FLVER.from_binder_path(mapbnd_path)
        for submesh in flver.meshes:
            print(submesh.material.mat_def_path, submesh.material.textures)
        return


def print_matbinbnd():
    matbinbnd = MATBINBND.from_path(ELDEN_RING_PATH + "/material/allmaterial.matbinbnd.dcx")
    shader_stems = set()
    for matbin_name in matbinbnd.get_entry_names():
        if matbin_name.startswith("m10_00"):
            matbin = matbinbnd.get_matbin(matbin_name)  # lazy load
            shader_stems.add(matbin.shader_stem)
            if matbin.shader_stem in {
                "M[AMSN]", "M[AMSN_V]", "M[AMSN][Ov_N]", "M[AMSN_V][Ov_N]", "M[AMSN][Ov_AN]", "M[AMSN_V][Ov_AN]"
            }:
                print(matbin)
    for stem in sorted(shader_stems):
        print(stem)


def main():
    # flver = FLVER.from_binder_path(ELDEN_RING_PATH + "/parts/am_f_2310.partsbnd.dcx", 200)
    stormveil = Path(ELDEN_RING_PATH + "/map/m10/m10_00_00_00/")
    for mapbnd_path in stormveil.glob("*.mapbnd.dcx"):
        flver = FLVER.from_binder_path(mapbnd_path)
        # print(flver.to_string())

        print(f"\nFLVER {mapbnd_path.name}")
        for submesh in flver.meshes:
            mat_printed = False
            for gx_item in submesh.material.gx_items:
                if not gx_item.data:
                    continue
                if gx_item.category == b"GX00" and gx_item.index == 102 and gx_item.size - 12 == 40:
                    if gx_item.data == struct.pack("<10i", 0, 0, 0, -1, 0, 0, 0, 0, 0, 0):
                        continue
                try:
                    fmt = ER_GX_ITEM_MAPPING[gx_item.category][gx_item.index, gx_item.size - 12]
                    if struct.calcsize(fmt) != gx_item.size - 12:
                        raise KeyError
                    # print(f"    {gx_item.category} | {gx_item.index} | {gx_item.size - 12}")
                    # print("   ", struct.unpack(f"<{fmt}", gx_item.data))
                except KeyError:
                    if not mat_printed:
                        print(f"\n  Material: {submesh.material.name}")
                        mat_printed = True

                    int_count = (gx_item.size - 12) // 4
                    print(f"    {gx_item.category} | {gx_item.index} | {gx_item.size - 12}")
                    print("   ", struct.unpack(f"<{int_count}i", gx_item.data))
                    print("   ", struct.unpack(f"<{int_count}f", gx_item.data))

    # for submesh in flver.meshes:
    #     vertex_min = submesh.vertices["position"].min(axis=0)
    #     vertex_max = submesh.vertices["position"].max(axis=0)
    #     vertex_mean = submesh.vertices["position"].mean(axis=0)
    #     vertex_center = (vertex_min + vertex_max) / 2
    #     vertex_range = vertex_max - vertex_min
    #     # print(submesh.vertices)
    #     print()
    #     print("MIN:", submesh.bounding_box_min)
    #     print("MAX:", submesh.bounding_box_max)
    #     print("CEN:", submesh.bounding_box_unknown)
    #     # print(vertex_min)
    #     # print(vertex_max)
    #     print("CEN (CALC):", vertex_center)
    #     print("MEAN:", vertex_mean)
    #     print("MEAN - MIN:", vertex_mean - vertex_min)
    #     print("RNG (HALF):", vertex_range / 2)
    #     print(submesh.vertices["position"][:5])


if __name__ == '__main__':
    # see_textures()
    print_matbinbnd()
    # main()

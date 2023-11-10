import struct
from pathlib import Path

from soulstruct import FLVER, ELDEN_RING_PATH


# TODO: Findings so far:
#  - Haven't seen a material that uses more than two GX Items, EXCLUDING the dummy item.
#  - In addition to the dummy item, EVERY material seems to have a ('GX00', 102) item with args:
#       (0, 0, 0, -1, 0, 0, 0, 0, 0, 0)


ER_GX_ITEM_MAPPING = {
    b"GXMD": {
        (131, 32): "3i5f",
        (131, 44): "3i5f2if",
        (132, 44): "3i5f2if",
        (133, 32): "3i5f",
        (133, 44): "3i5f2if",
        (137, 32): "3i5f",
        (162, 28): "3if3i",  # TODO: only instance of GXMD not compatible with the others - suggests `unk` DOES matter
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


def main():
    # flver = FLVER.from_binder_path(ELDEN_RING_PATH + "/parts/am_f_2310.partsbnd.dcx", 200)
    stormveil = Path(ELDEN_RING_PATH + "/map/m10/m10_00_00_00/")
    for mapbnd_path in stormveil.glob("*.mapbnd.dcx"):
        flver = FLVER.from_binder_path(mapbnd_path)
        # print(flver.to_string())

        print(f"\nFLVER {mapbnd_path.name}")
        for submesh in flver.submeshes:
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

    # for submesh in flver.submeshes:
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
    main()

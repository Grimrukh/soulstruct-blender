"""Inspecting various FLVER properties for testing full export."""
from pathlib import Path

from soulstruct.containers import Binder
from soulstruct.base.models.flver import FLVER


VANILLA_CHR_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup 1.03.1)/chr")
VANILLA_MAP_PATH = Path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Vanilla Backup 1.03.1)/map")
TEST_PATH = Path(__file__).parent / "tests"


def exported_flver():
    exported = FLVER.from_path("C:/Users/Scott/Documents/untitled.flver")
    print(exported.meshes)


def test_chr():

    chrbnd = Binder.from_path(VANILLA_CHR_PATH / "c1200.chrbnd.dcx")
    flver_entry = chrbnd[200]
    chr_flver = flver_entry.to_binary_file(FLVER)
    for attr in (
        "big_endian",
        "version",
        "bounding_box_min",
        "bounding_box_max",
        "vertex_indices_size",
        "unicode",
        "unk_x4a",
        "unk_x4c",
        "unk_x5c",
        "unk_x5d",
        "unk_x68",
    ):
        print(attr, getattr(chr_flver, attr))
    # exported = FLVER("C:/Users/Scott/Documents/untitled.flver")

    # for dummy in chr_flver.dummies:
    #     print(dummy)


def test():

    map_flver = FLVER.from_path(VANILLA_MAP_PATH / "m10_01_00_00/m3220B1A10.flver.dcx")

    mesh = map_flver.meshes[11]
    for v in mesh.vertices:
        print(v.uvs[1])


def test_tex_mp():
    from soulstruct.containers.tpf import TPF, batch_get_tpf_texture_png_data
    import timeit

    tpfbhd = Binder.from_path(VANILLA_MAP_PATH / "m10/m10_0000.tpfbhd")
    textures = []
    for entry in tpfbhd.entries:
        tpf = entry.to_binary_file(TPF)
        for tex in tpf.textures:
            textures.append(tex)

    count = 20

    def convert_non_parallel():
        return [t.get_png_data() for t in textures[:count]]

    def convert_parallel():
        batch_get_tpf_texture_png_data(textures[:count])

    print(timeit.timeit("convert_non_parallel()", number=1, globals=locals()))
    print(timeit.timeit("convert_parallel()", number=1, globals=locals()))

    # data = batch_get_tpf_texture_png_data(textures[:5])
    print("Success.")


def check_flver():
    working = FLVER.from_path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Nightfall)/map/m13_01_00_00/m2000E1A13.flver.dcx.bak")
    bad = FLVER.from_path("C:/Steam/steamapps/common/DARK SOULS REMASTERED (Nightfall)/map/m13_01_00_00/m2000E1A13.flver.dcx")

    working_mesh_5 = working.meshes[5]
    bad_mesh_5 = bad.meshes[5]

    print(len(working_mesh_5.vertices))
    print(len(bad_mesh_5.vertices))

    for i, (working_v, bad_v) in enumerate(zip(working_mesh_5.vertices, bad_mesh_5.vertices)):
        if working_v.uvs != bad_v.uvs:
            print(i)
            print(working_v.uvs)
            print(bad_v.uvs)
            break


if __name__ == '__main__':
    # test_chr()
    # test()
    # exported_flver()
    # test_tex_mp()

    check_flver()

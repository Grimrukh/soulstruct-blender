from pathlib import Path

from soulstruct.containers import Binder, BinderEntry, EntryNotFoundError
from soulstruct.eldenring.models.matbin import MATBIN, MATBINBND
from soulstruct.utilities.binary import BinaryReader
from soulstruct.utilities.files import write_json


def main():
    matbinbnd = MATBINBND.from_bundled()
    shaderbdlebnd_path = Path(r"C:\Steam\steamapps\common\ELDEN RING (Modding 1.10)\Game\shader\shaderbdle.shaderbdlebnd.dcx")

    shaderbdlebnd = Binder.from_path(shaderbdlebnd_path)
    sampler_infos = {}

    for matbin_entry in matbinbnd.entries:
        matbin = MATBIN.from_binder_entry(matbin_entry)
        shader_stem = matbin.shader_name.split(".")[0]
        if shader_stem in sampler_infos:
            continue  # done from previous MATBIN

        print(f"Finding metaparam for shader {shader_stem}...")
        try:
            shaderbdle_entry = shaderbdlebnd.find_entry_name(f"{shader_stem}.shaderbdle")
        except EntryNotFoundError:
            print(f"  No shaderbdle entry found for {shader_stem}.")
            sampler_infos[shader_stem] = []  # don't look again
            continue
        shaderbdle = Binder.from_binder_entry(shaderbdle_entry)
        metaparam_entry = shaderbdle.find_entry_name(f"{shader_stem}.metaparam")
        sampler_infos[shader_stem] = read_metaparam(metaparam_entry)

    write_json("shader_samplers.json", sampler_infos, indent=4)


def read_metaparam(metaparam_entry: BinderEntry) -> list[dict[str, str]]:
    metaparam = BinaryReader(metaparam_entry.get_uncompressed_data())

    res = []
    metaparam.seek(0xC)
    sampler_count = metaparam.unpack_value("i")
    for i in range(sampler_count):
        metaparam.seek(0x98 + (0x30 * i))
        sampler_name_offset = metaparam.unpack_value("q")
        metaparam.seek(8, 1)
        default_texture_path_offset = metaparam.unpack_value("q")
        sampler_group_name_offset = metaparam.unpack_value("q")
        res.append(
            {
                "name": metaparam.unpack_string(sampler_name_offset, encoding="utf-16-le"),
                "default_texture_path": metaparam.unpack_string(default_texture_path_offset, encoding="utf-16-le"),
                "group_name": metaparam.unpack_string(sampler_group_name_offset, encoding="utf-16-le"),
            }
        )
    return res


if __name__ == '__main__':
    main()

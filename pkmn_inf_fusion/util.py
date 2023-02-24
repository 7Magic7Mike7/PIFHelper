import os.path
from typing import Union, Optional

__CUSTOM_BATTLERS_PATH = os.path.join("Graphics", "CustomBattlers")
__CUSTOM_BATTLERS_INDEXED_PATH = os.path.join(__CUSTOM_BATTLERS_PATH, "indexed")


def custom_battlers_folder(base_path: str) -> str:
    # pre-auto sorting
    return os.path.join(base_path, __CUSTOM_BATTLERS_PATH)


def custom_battlers_indexed_folder(base_path: str, dex_num: Optional[int] = None) -> str:
    # new path since auto sorting
    if dex_num is None:
        return os.path.join(base_path, __CUSTOM_BATTLERS_INDEXED_PATH)

    assert is_valid_pkmn(dex_num), f"Invalid dex number: {dex_num}!"
    return os.path.join(base_path, __CUSTOM_BATTLERS_INDEXED_PATH, str(dex_num))


def min_id() -> int:
    return 1


def max_id() -> int:
    return 420


def is_valid_pkmn(pkmn: Union[str, int]) -> bool:
    if isinstance(pkmn, str):
        if pkmn.isdigit():
            pkmn = int(pkmn)
        else:
            # e.g. Alts
            return False
    return min_id() <= pkmn <= max_id()


def check_fusion(base_path: str, head: int, body: int, indexed: bool = True) -> bool:
    if indexed:
        folder_path = custom_battlers_indexed_folder(base_path)
    else:
        folder_path = custom_battlers_folder(base_path)
    file_name = f"{head}.{body}.png"
    full_path = os.path.join(folder_path, file_name)
    return os.path.exists(full_path)


def write_dex_names(gen12_file: str, gen37_file: str, output_file: str):
    # content copied from https://en.wikipedia.org/wiki/List_of_generation_I_Pok%C3%A9mon
    # and https://en.wikipedia.org/wiki/List_of_generation_II_Pok%C3%A9mon
    names = ["", ""]
    # the pokedex numbers/ids are correctly ordered for gen 1 and 2
    cur_id = 1
    gen = 1
    with open(gen12_file, "rt") as file:
        while gen <= 2:
            content = file.readline()
            if content.startswith("#"):
                content = content[1:]
            names[gen - 1] = f"#{content[:-1]}"  # carry over the original string
            cur_name = ""
            for character in content:
                if len(cur_name) > 0 and character.isupper() and cur_name not in ["Mr. ", "Ho-"]:
                    names.append(f"{cur_id}={cur_name}")
                    cur_id += 1
                    cur_name = character
                else:
                    cur_name += character
            names.append(f"{cur_id}={cur_name}")
            cur_id += 1
            gen += 1

    # pokedex numbers/ids for pokemon of gen 3 to 7 must be retrieved from an extra file
    with open(gen37_file, "rt") as file:
        line = file.readline()
        while line is not None and len(line) > 0:
            parts = line.split("\t")
            names.append(f"{parts[0]}={parts[1]}")
            line = file.readline()

    # write the result
    with open(output_file, "wt") as file:
        file.write("\n".join(names))

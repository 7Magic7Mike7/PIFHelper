import os
from typing import List, Dict, Union

from pkmn_inf_fusion import util


class FusionRetriever:
    def __init__(self, dex_names: Union[Dict[int, str], str]):
        if isinstance(dex_names, str):
            self.__names: Dict[int, str] = {}

            def store_pokemon(line: str):
                parts = line.split("=")
                id_ = parts[0]
                if id_.isdigit():
                    self.__names[int(id_)] = parts[1]
                else:
                    print(f"ERROR! Invalid id: \"{id_}\"")
            util.analyze_data_file(dex_names, store_pokemon)

        else:
            self.__names = dex_names

    def get_fusions(self, base_path: str, pkmn: int, as_head: bool = True, as_names: bool = True) -> \
            Union[List[int], List[str]]:
        fusions = []
        if as_head:
            dir_path = util.custom_battlers_indexed_folder(base_path, pkmn)
            for file in os.listdir(dir_path):
                parts = file.split(".")
                if len(parts) == 3:
                    body_id = parts[1]
                    if util.is_valid_pkmn(body_id):
                        fusions.append((int(body_id)))
        else:
            dir_path = util.custom_battlers_indexed_folder(base_path)
            for folder in os.listdir(dir_path):
                if util.is_valid_pkmn(folder):
                    full_path = os.path.join(dir_path, folder, f"{folder}.{pkmn}.png")
                    if os.path.exists(full_path):
                        fusions.append(int(folder))

        if as_names:
            return [self.get_name(id_) for id_ in fusions]
        else:
            return fusions

    def get_name(self, pkmn: int) -> str:
        if pkmn in self.__names:
            return self.__names[pkmn]
        else:
            return f"ERROR: {pkmn}"

    def get_all_names(self) -> List[str]:
        return list(self.__names.values())

    def get_id(self, name: str) -> int:
        for val in self.__names:
            if self.__names[val].lower() == name.lower():
                return val
        return -1

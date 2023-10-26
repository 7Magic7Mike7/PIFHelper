import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional

from pkmn_inf_fusion import util, Pokemon, FusedMon


class FusionRetriever(ABC):
    @staticmethod
    def from_ids(retriever: "FusionRetriever", head: int, body: int) -> Optional[FusedMon]:
        assert util.is_valid_pkmn(head), f"Head is invalid: {head}"
        assert util.is_valid_pkmn(body), f"Body is invalid: {body}"

        head_mon = retriever.get_pokemon(head)
        body_mon = retriever.get_pokemon(body)
        if head_mon is None or body_mon is None:
            return None
        else:
            return FusedMon(head_mon, body_mon)

    @abstractmethod
    def _get_fusions_internal(self, pkmn: int, as_head: bool = True, as_names: bool = True, ) -> \
            Union[List[int], List[str]]:
        pass

    def get_fusions(self, pkmn: Union[int, List[int]], as_head: bool = True, as_names: bool = True,
                    force_unique: bool = True) -> Union[List[int], List[str]]:
        """
        By default, returns a list containing the names of all pokemon that can be fused with pkmn being the head. If
        as_head is False pkmn is used as body instead. If as_names is False ids (i.e., pokedex num) are returned instead
        of names

        :param pkmn: the pokemon of which we want to retrieve fusions or a list of multiple such pokemon
        :param as_head: whether pkmn is used as head or as body
        :param as_names: whether to return a list of pokemon names or ids
        :param force_unique: whether returned Iterable should only contain unique values (i.e., effectively being a set)
                             or not (i.e., be a list)
        :return:
        """
        if isinstance(pkmn, int):
            return self._get_fusions_internal(pkmn, as_head, as_names)
        else:
            fusions = []
            for mon in pkmn:
                fusions += self._get_fusions_internal(mon, as_head, as_names)
            if force_unique:
                fusions = list(set(fusions))
            return fusions

    @abstractmethod
    def get_name(self, pkmn: int) -> str:
        pass

    @abstractmethod
    def get_all_names(self) -> List[str]:
        pass

    @abstractmethod
    def get_id(self, name: str) -> int:
        pass

    @abstractmethod
    def get_pokemon(self, id_: int) -> Optional[Pokemon]:
        pass


class DynamicFusionRetriever(FusionRetriever):
    def __init__(self, dex_names: Union[Dict[int, str], str], base_path: str):
        self.__base_path = base_path
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

    def _get_fusions_internal(self, pkmn: int, as_head: bool = True, as_names: bool = True) -> \
            Union[List[int], List[str]]:
        fusions = []
        if as_head:
            dir_path = util.custom_battlers_indexed_folder(self.__base_path, pkmn)
            for file in os.listdir(dir_path):
                parts = file.split(".")
                if len(parts) == 3:
                    body_id = parts[1]
                    if util.is_valid_pkmn(body_id):
                        fusions.append((int(body_id)))
        else:
            dir_path = util.custom_battlers_indexed_folder(self.__base_path)
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
        name = name.lstrip(" ").rstrip(" ").lower()     # normalize input
        for val in self.__names:
            if self.__names[val].lower() == name:
                return val
        return -1

    def get_pokemon(self, id_: int) -> Optional[Pokemon]:
        return None


class StaticFusionRetriever(FusionRetriever):
    def __init__(self, pif_dex_path: str, custom_fusions_path: str):
        """

        :param pif_dex_path: path to json file containing info to create all available Pokémon or path to folder
                             containing pif_dex.json
        :param custom_fusions_path: path to json file containing ids of all available fusions or path to folder
                                    containing custom_fusions.json
        """
        if not pif_dex_path.endswith(".json"):
            pif_dex_path = os.path.join(pif_dex_path, "pif_dex.json")
        if not custom_fusions_path.endswith(".json"):
            custom_fusions_path = os.path.join(custom_fusions_path, "custom_fusions.json")

        self.__mons: Dict[int, Pokemon] = {}
        for mon in Pokemon.load_from_json(pif_dex_path):
            self.__mons[mon.id] = mon

        self.__fusions: Dict[str, Dict[int, List[int]]] = {
            "Head": {},
            "Body": {}
        }
        with open(custom_fusions_path, encoding='utf-8') as file:
            # Load the JSON data
            data = json.load(file)
            for key in data["Head"]:
                id_ = int(key)
                self.__fusions["Head"][id_] = data["Head"][key]
            for key in data["Body"]:
                id_ = int(key)
                self.__fusions["Body"][id_] = data["Body"][key]

    def _get_fusions_internal(self, pkmn: int, as_head: bool = True, as_names: bool = True) -> \
            Union[List[int], List[str]]:
        origin = "Head" if as_head else "Body"

        if as_names:
            return [self.__mons[id_].name for id_ in self.__fusions[origin][pkmn]]
        else:
            return self.__fusions[origin][pkmn]

    def get_name(self, pkmn: int) -> str:
        return self.__mons[pkmn].name

    def get_all_names(self) -> List[str]:
        return [mon.name for mon in self.__mons.values()]

    def get_id(self, name: str) -> int:
        name = name.lstrip(" ").rstrip(" ").lower()  # normalize input
        for mon in self.__mons.values():
            if mon.name.lower() == name:
                return mon.id
        return -1

    def get_pokemon(self, id_: int) -> Optional[Pokemon]:
        if id_ in self.__mons:
            return self.__mons[id_]
        return None

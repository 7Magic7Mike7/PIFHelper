import json
import os
import shutil
from typing import List, Union, Dict, Any, Optional

from .fusion_retriever import FusionRetriever
from .evolution_helper import EvolutionLine, EvolutionHelper, FusedEvoLine
from .gui import GUI
from .pokemon import Pokemon
from . import util


class Helper:
    def __init__(self, base_path: str, dex_names: Union[Dict[int, str], str]):
        """

        :param base_path: path to game's root folder (ends with something like "infinitefusion_5.1.0.1-full")
        """
        self.__base_path = base_path
        self.__retriever = FusionRetriever(dex_names)

    @property
    def retriever(self) -> FusionRetriever:
        return self.__retriever

    def check_fusion(self, head: int, body: int) -> bool:
        return util.check_fusion(self.__base_path, head, body)

    def get_head_fusions(self, head: int) -> List[int]:
        return self.__retriever.get_fusions(self.__base_path, head, as_head=True)

    def get_body_fusions(self, body: int) -> List[int]:
        return self.__retriever.get_fusions(self.__base_path, body, as_head=False)

    def refresh_image_dex(self, destination: str):
        battlers_path = os.path.join(self.__base_path, "Graphics", "Battlers")
        for i in range(util.min_id(), util.max_id()):
            src = os.path.join(battlers_path, str(i), f"{i}.{i}.png")
            dst = os.path.join(destination, f"{i}.png")
            shutil.copyfile(src, dst)

    def refresh_evo_line_dex(self, evo_helper: EvolutionHelper, destination: str):
        battlers_path = os.path.join(self.__base_path, "Graphics", "Battlers")
        ids = evo_helper.dex_nums_to_evo_lines(list(range(util.min_id(), util.max_id())))
        for i in ids:
            i = i.end_stage
            src = os.path.join(battlers_path, str(i), f"{i}.{i}.png")
            dst = os.path.join(destination, f"{i}.png")
            shutil.copyfile(src, dst)

    def refresh_pif_dex_json(self, destination: str, src: Optional[str] = None):
        if not destination.endswith(".json"):
            destination = os.path.join(destination, "pif_dex.json")
        if src is None:
            src = os.path.join("data", "pokedex.json")

        mons = Pokemon.load_from_json(src)
        mon_dic: Dict[str, Pokemon] = {}
        for mon in mons: mon_dic[mon.name] = mon

        json_content: List[Dict[str, Any]] = []
        for name in self.retriever.get_all_names():
            pif_id = self.retriever.get_id(name)
            mon = mon_dic[name].to_json()
            mon["id"] = pif_id
            json_content.append(mon)

        with open(destination, "wt") as file:
            json.dump(json_content, file, indent=4)

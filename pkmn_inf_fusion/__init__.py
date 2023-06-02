import os
import shutil
from typing import List, Union, Dict

from .fusion_retriever import FusionRetriever
from .evolution_helper import EvolutionLine, EvolutionHelper, FusedEvoLine
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

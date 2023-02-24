from typing import List, Dict, Optional, Union, Tuple

from pkmn_inf_fusion import util, FusionRetriever


class _Parser:
    __BASE_SEPARATOR = "->"
    __LINE_SEPARATOR = "|"
    __EVO_SEPARATOR = ","

    @staticmethod
    def evo_list(line: str) -> List[int]:
        return [int(val) for val in line.replace(" ", "").split(_Parser.__EVO_SEPARATOR)]

    @staticmethod
    def base_split(line: str) -> Tuple[int, str]:
        base, evolution_part = line.split(_Parser.__BASE_SEPARATOR)
        return int(base), evolution_part

    @staticmethod
    def is_separable(line: str) -> bool:
        return _Parser.__BASE_SEPARATOR in line

    @staticmethod
    def line_split(evolution_part: str) -> List[str]:
        return evolution_part.split(_Parser.__LINE_SEPARATOR)


class EvolutionLine:
    def __init__(self, base_pkmn: Union[int, str], evolutions: Union[List[int], str]):
        if isinstance(base_pkmn, str):
            assert util.is_valid_pkmn(base_pkmn), f"Invalid base Pokemon: {base_pkmn}!"
            self.__base = int(base_pkmn)
        if isinstance(evolutions, str):
            evos = []
            for pkmn in _Parser.evo_list(evolutions):
                assert util.is_valid_pkmn(pkmn), f"Invalid evolution: {pkmn}!"
                evos.append(int(pkmn))
            evolutions = evos

        self.__base = base_pkmn
        self.__evos = evolutions

    @property
    def base(self) -> int:
        return self.__base

    @property
    def evo1(self) -> Optional[int]:
        if len(self.__evos) > 0:
            return self.__evos[0]
        return None

    @property
    def evo2(self) -> Optional[int]:
        if len(self.__evos) > 1:
            return self.__evos[1]
        return None

    @property
    def is_multi_stage(self) -> bool:
        return self.size > 1

    @property
    def size(self) -> int:
        return len(self)

    def named_str(self, fusion_retriever: FusionRetriever) -> str:
        text = fusion_retriever.get_name(self.__base)
        for evo in self.__evos:
            text += f" -> {fusion_retriever.get_name(evo)}"
        return text

    def __contains__(self, item):
        if isinstance(item, int):
            return item == self.__base or item in [self.__evos]
        return False

    def __len__(self) -> int:
        return 1 + len(self.__evos)

    def __str__(self) -> str:
        text = f"{self.__base}"
        for evo in self.__evos:
            text += f" -> {evo}"
        return text


class EvolutionHelper:
    def __init__(self, evolutions_file: str):
        self.__evolutions: Dict[Optional[int], List[EvolutionLine]] = {}

        def store_evolution(line: str):
            line = line.replace(" ", "")    # remove whitespace

            if _Parser.is_separable(line):
                # multi stage pokemon (= evolution(s) exist)
                base, evolution_part = _Parser.base_split(line)
                evo_lines = [
                    EvolutionLine(base, val)
                    for val in _Parser.line_split(evolution_part)
                ]

                # store the evolution line for each pokemon in it (still works if evo1 or evo2 are None)
                evo1, evo2 = evo_lines[0].evo1, evo_lines[0].evo2
                self.__evolutions[base] = evo_lines
                self.__evolutions[evo1] = evo_lines
                self.__evolutions[evo2] = evo_lines
            else:
                # single stage pokemon
                assert util.is_valid_pkmn(line), f"Invalid base Pokemon: {line}!"
                evo_line = EvolutionLine(line, [])
                self.__evolutions[evo_line.base] = [evo_line]

        util.analyze_data_file(evolutions_file, store_evolution)

    def get_evolution_lines(self, dex_num: int, exclude_parallels: bool = True) -> List[EvolutionLine]:
        """

        :param dex_num:
        :param exclude_parallels: excludes parallel evolution lines (evolution line had to branch already)
        :return:
        """
        assert util.is_valid_pkmn(dex_num), f"Invalid dex number: {dex_num}!"
        assert dex_num in self.__evolutions, f"ERROR! {dex_num} seems not to be stored!"

        if exclude_parallels:
            return list(filter(
                lambda el: dex_num in el,   # only keep lines that involve dex_num
                self.__evolutions[dex_num]
            ))
        return self.__evolutions[dex_num]

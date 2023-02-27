from typing import List, Dict, Optional, Union, Tuple, Set

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
            base_pkmn = int(base_pkmn)
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
    def end_stage(self) -> int:
        if self.evo1 is None:
            return self.base
        elif self.evo2 is None:
            return self.evo1
        else:
            return self.evo2

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

    def to_list(self) -> List[int]:
        list_ = [self.base]
        if self.evo1 is not None:
            list_.append(self.evo1)
        if self.evo2 is not None:
            list_.append(self.evo2)
        return list_

    def __contains__(self, item):
        if isinstance(item, int):
            return item == self.__base or item in self.__evos
        return False

    def __len__(self) -> int:
        return 1 + len(self.__evos)

    def __str__(self) -> str:
        text = f"{self.__base}"
        for evo in self.__evos:
            text += f" -> {evo}"
        return text

    def __hash__(self):
        val = 17 * self.base
        if self.evo1 is not None:
            val += 311 * self.evo1
        if self.evo2 is not None:
            val += 523 * self.evo2
        return val

    def __eq__(self, other):
        if isinstance(other, EvolutionLine):
            return self.base == other.base and self.evo1 == other.evo1 and self.evo2 == other.evo2


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

                for evo_line in evo_lines:
                    # store the evolution line for each pokemon in it (still works if evo1 or evo2 are None)
                    evo1, evo2 = evo_line.evo1, evo_line.evo2
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

    def dex_nums_to_evo_lines(self, dex_nums: List[int]) -> List[EvolutionLine]:
        evo_lines: Set[EvolutionLine] = set()

        for dex_num in dex_nums:
            cur_lines = self.get_evolution_lines(dex_num, exclude_parallels=True)
            for line in cur_lines:
                evo_lines.add(line)

        return list(evo_lines)


class FusedEvoLine:
    def __init__(self, base_path: str, retriever: FusionRetriever, evo_line1: EvolutionLine, evo_line2: EvolutionLine,
                 unidirectional: bool = False):
        self.__retriever = retriever
        self.__line1 = evo_line1
        self.__line2 = evo_line2

        existing: List[Tuple[int, int]] = []
        missing: List[Tuple[int, int]] = []

        def check_line(line1: EvolutionLine, line2: EvolutionLine):
            for dex_num in line1.to_list():
                fusions = retriever.get_fusions(base_path, dex_num, as_head=True, as_names=False)
                for fused_num in line2.to_list():
                    if fused_num in fusions:
                        existing.append((dex_num, fused_num))
                    else:
                        missing.append((dex_num, fused_num))

        check_line(evo_line1, evo_line2)
        if not unidirectional:
            check_line(evo_line2, evo_line1)

        self.__existing = existing
        self.__missing = missing

    @property
    def rate(self) -> float:
        return len(self.__existing) / (len(self.__existing) + len(self.__missing))

    @property
    def has_final(self) -> bool:
        return (self.__line1.end_stage, self.__line2.end_stage) in self.__existing

    def formatted_string(self, existing: bool = True, missing: bool = True, headline_ids: bool = True) -> str:
        text = "" #f"Fusions of Evolution lines "
        if headline_ids:
            text += f"#{self.__line1.end_stage} & " \
                    f"#{self.__line2.end_stage}"
        else:
            text += f"{self.__retriever.get_name(self.__line1.end_stage)} & " \
                    f"{self.__retriever.get_name(self.__line2.end_stage)}"

        if existing and len(self.__existing) > 0:
            text += "\n\tExisting:\n"
            for fusion in self.__existing:
                head, body = fusion
                text += f"\t\t- {self.__retriever.get_name(head)} + {self.__retriever.get_name(body)}\n"
            text = text[:-1]    # remove last \n

        if missing and len(self.__missing) > 0:
            text += "\n\tMissing:\n"
            for fusion in self.__missing:
                head, body = fusion
                text += f"\t\t- {self.__retriever.get_name(head)} + {self.__retriever.get_name(body)}\n"
            text = text[:-1]    # remove last \n

        return text

    def __str__(self) -> str:
        return f"EvoLine-Fusions of #{self.__line1.end_stage} & #{self.__line2.end_stage} " \
               f"({len(self.__existing)} exist, {len(self.__missing)} miss)"

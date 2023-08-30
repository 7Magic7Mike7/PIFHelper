import tkinter
from tkinter import ttk, Tk, IntVar, StringVar
from typing import List, Tuple, Set, Optional

from pkmn_inf_fusion import EvolutionHelper, FusionRetriever, EvolutionLine, FusedEvoLine, util


class GUI:
    __MON_SPLITER = ";"
    __DEFAULT_RATE = 0.5
    __SM_NAME = 0
    __SM_RATE = 1
    __SM_DEX = 2

    def __init__(self, base_path: str, retriever: FusionRetriever, evo_helper: EvolutionHelper,
                 main_mon: Optional[str] = None, available_mons: Optional[List[str]] = None):
        self.__base_path = base_path
        self.__retriever = retriever
        self.__evo_helper = evo_helper
        self.__root = Tk(screenName="Pokemon")
        self.__pokemon_list = retriever.get_all_names()
        self.__analyzed_mons: Set[int] = set()

        self.__root.title("Pokemon Infinite Fusion - Fusion Checker")
        row = 0
        frm = ttk.Frame(self.__root, width=200, height=200, padding=10)
        frm.grid()

        ttk.Label(frm, text="Main Pokemon: ").grid(column=0, row=row)
        self.__e_main_mon = ttk.Combobox(frm, values=self.__pokemon_list)
        self.__e_main_mon.grid(column=1, row=row, columnspan=1)
        row += 1

        ttk.Label(frm, text="Available Pokemon: ").grid(column=0, row=row)
        row += 1
        self.__available_mons = tkinter.Text(frm, width=20, height=15)
        self.__available_mons.grid(column=0, row=row, columnspan=2)
        row += 1

        ttk.Label(frm, text="Min rate: ").grid(column=0, row=row)
        self.__e_rate = ttk.Entry(frm, width=5)
        self.__e_rate.grid(column=1, row=row)
        self.__e_rate.insert(0, f"{GUI.__DEFAULT_RATE}")
        row += 1

        ttk.Button(frm, text="Analyse", command=self.__analyse, width=30).grid(column=0, row=row, columnspan=2)
        ttk.Button(frm, text="Reset", command=self.__reset, width=30).grid(column=2, row=row)

        ttk.Label(frm, text="Head Fusions: ").grid(column=2, row=1)
        self.__tree_head_fusions = ttk.Treeview(frm, columns=("fusions"))
        self.__tree_head_fusions.grid(column=2, row=2)

        ttk.Label(frm, text="Body Fusions: ").grid(column=3, row=1)
        self.__tree_body_fusions = ttk.Treeview(frm, columns=("fusions"))
        self.__tree_body_fusions.grid(column=3, row=2)

        if main_mon is not None:
            self.__e_main_mon.insert(0, main_mon)
        if available_mons is not None:
            self.__available_mons.insert("end", f"{GUI.__MON_SPLITER} ".join(available_mons) + "\n")

    def __reset(self):
        for id_ in self.__analyzed_mons:
            self.__tree_head_fusions.delete(f"{id_}")
            self.__tree_body_fusions.delete(f"{id_}")
        self.__analyzed_mons.clear()

    def _filter_by_availability(self, evolution_lines: List[EvolutionLine]) -> List[EvolutionLine]:
        available_ids = []
        # go through every line in our text area for available pokemon
        for line in self.__available_mons.get("1.0", "end").split("\n"):
            # there can be multiple pokemon per line
            for mon in line.split(GUI.__MON_SPLITER):
                id_ = self.__retriever.get_id(mon)
                if id_ != -1: available_ids.append(id_)

        if len(available_ids) <= 0: return evolution_lines  # don't filter if we would get an empty result
        return EvolutionHelper.availability_filter(evolution_lines, available_ids)

    def __analyse(self):
        # validate user input
        assert self.__retriever.get_id(self.__e_main_mon.get()) >= 0, f"Entry not valid: {self.__e_main_mon.get()}!"
        min_rate = float(self.__e_rate.get())
        assert 0 <= min_rate <= 1.0, f"Invalid rate: {min_rate}!"

        self.__reset()      # remove old data before we analyse

        dex_num = self.__retriever.get_id(self.__e_main_mon.get())
        evo_lines = self.__evo_helper.get_evolution_lines(dex_num)

        new_evo_lines = []
        for el in evo_lines:    # filter out every pokemon we already analyzed
            if el.end_stage not in self.__analyzed_mons:
                new_evo_lines.append(el)
                self.__analyzed_mons.add(el.end_stage)

        head_fusions = self.__retriever.get_fusions(self.__base_path, dex_num, as_head=True, as_names=False)
        head_fusions = self.__evo_helper.dex_nums_to_evo_lines(head_fusions)
        head_fusions = self._filter_by_availability(head_fusions)

        body_fusions = self.__retriever.get_fusions(self.__base_path, dex_num, as_head=False, as_names=False)
        body_fusions = self.__evo_helper.dex_nums_to_evo_lines(body_fusions)
        body_fusions = self._filter_by_availability(body_fusions)

        for evo_line in new_evo_lines:
            for data in self._get_fusion_tree_data(evo_line, head_fusions, min_rate=min_rate, are_head_fusions=True):
                parent_id, item_id, text = data
                self.__tree_head_fusions.insert(parent_id, "end", item_id, text=text)

            for data in self._get_fusion_tree_data(evo_line, body_fusions, min_rate=min_rate, are_head_fusions=False):
                parent_id, item_id, text = data
                self.__tree_body_fusions.insert(parent_id, "end", item_id, text=text)

    def _get_fusion_tree_data(self, main_line: EvolutionLine, fusion_list: List[EvolutionLine], min_rate: float,
                              are_head_fusions: bool, sort_mode: int = __SM_RATE) -> List[Tuple[str, str, str]]:
        # we need to store three levels: main pokemon,
        tree_data: List[List[Tuple[str, str, str, int, float]]] = [[], [], [],]
        elid = main_line.end_stage

        # head fusions use the head from evo_line and the bodies from head_fusions (fusions with main mon as head)
        for other_line in fusion_list:
            fid = elid * util.max_id() + other_line.end_stage

            l1 = main_line if are_head_fusions else other_line
            l2 = other_line if are_head_fusions else main_line
            fusion_line = FusedEvoLine(self.__base_path, self.__retriever, l1, l2, unidirectional=True)

            # continue with next value if fusion_line doesn't have enough coverage
            if fusion_line.rate < min_rate: continue

            tree_data[1].append((f"{elid}", f"{fid}", f"{self.__retriever.get_name(other_line.end_stage)} "
                                                      f"#{other_line.end_stage}\t[{100 * fusion_line.rate:.0f}%]",
                                 other_line.end_stage, fusion_line.rate))

            for i, fusion in enumerate(fusion_line.existing):
                head_mon, body_mon = fusion
                dex_num = body_mon if are_head_fusions else head_mon    # dex of the other pokemon for sorting
                head_mon = self.__retriever.get_name(head_mon)
                body_mon = self.__retriever.get_name(body_mon)
                tree_data[2].append((f"{fid}", f"{fid}_{i}", f"{head_mon} / {body_mon}", dex_num, 1))

        # append it at the end, so we can also display the number of fusion lines
        tree_data[0].append(("", f"{elid}", f"{self.__retriever.get_name(main_line.end_stage)} #{main_line.end_stage} "
                                            f" x{len(tree_data[1])}", elid, 1))

        if sort_mode == GUI.__SM_NAME:
            for td in tree_data: td.sort(key=lambda a: a[2])
        elif sort_mode == GUI.__SM_RATE:
            # tuples can be sorted automatically, so we use the rate first (negate to reverse the order) and on equal
            # rates we sort by name
            for td in tree_data: td.sort(key=lambda a: (-a[4], a[2]))
        else:   # sort by dex
            for td in tree_data: td.sort(key=lambda a: a[3])
        aaaa = tree_data[0] + tree_data[1] + tree_data[2]

        return [(t[0], t[1], t[2]) for t in aaaa]

    def start(self):
        self.__root.mainloop()
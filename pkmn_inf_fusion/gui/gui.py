import tkinter
from tkinter import ttk, Tk, IntVar, StringVar, DoubleVar
from typing import List, Tuple, Set, Optional, Dict, Iterable

from pkmn_inf_fusion import EvolutionHelper, FusionRetriever, EvolutionLine, FusedEvoLine, util, Pokemon, FusedMon
from pkmn_inf_fusion.gui import Filter, Safe, gui_util


class GUI:
    __MON_SPLITER = ";"
    __DEFAULT_RATE = 50
    __SM_NAME = 0
    __SM_RATE = 1
    __SM_DEX = 2

    def __init__(self, retriever: FusionRetriever, evo_helper: EvolutionHelper,
                 main_mon: Optional[str] = None, available_mons: Optional[List[str]] = None):
        self.__retriever = retriever
        self.__evo_helper = evo_helper
        self.__root = Tk(screenName="Pokemon")
        self.__pokemon_list = retriever.get_all_names()
        self.__tree_is_resettable = False

        # rough looks of the UI
        """
        Columns
        0     1     2          3      |    4                    5                 6         7      8
        ###########################################################################################################
        Main Pokemon: [________|v]         Available Pokemon: [_______________]
        Filter:                            Results:                               Selected Fusion Data:
        BST   ? -------------              -----------------------------------    -----------------------
        HP    ? -------------              |~ Head                           |    | BST:    123         |
        ATK   ? -------------              | + EvoLine1 #id xNumFusions      |    | HP:     123         |
        SPATK ? -------------              | ~ EvoLine2 #id xNumFusions      |    | ATK:    123         |
        DEF   ? -------------              |    + FusedLine1 #id %completion |    | DEF:    123         |
        SPDEF ? -------------              |    ~ FusedLine2 #id %completion |    | SPATK:  123         |
        SPD   ? -------------              |         Fusion1                 |    | SPDEF:  124         |
                                           |         Fusion2                 |    | SPD:    123         |
        TYPE [____|v]                      |         Fusion3                 |    |                     |
        Ability [____|v]                   |                                 |    | Type:    T1  (T2)   |
        Min rate 0 ---------- 100          |+ Body                           |    | Abilities:  [____|v]|
                                           |                                 |    |                     |
        Only BST > BaseMons [x]            -----------------------------------    -----------------------
                                                                                         {SAVE}
                                                                                      {SWAP FUSION}
                {ANALYZE}     {RESET}                                       {OPEN IMAGE OF SELECTED FUSION}
        """

        # title
        self.__root.title("Pokemon Infinite Fusion - Fusion Checker")
        frm = ttk.Frame(self.__root, width=500, height=300, padding=10)
        frm.grid()

        # styles
        stypeHL = ttk.Style()   # headlines
        stypeHL.configure("BW.TLabel", foreground="red", background="black")

        # ROW 0
        # main pokemon to search for fusions
        ttk.Label(frm, text="Main Pokemon: ").grid(column=0, row=0)
        self.__e_main_mon = ttk.Combobox(frm, values=self.__pokemon_list)
        self.__e_main_mon.grid(column=1, row=0, columnspan=2)

        # available pokemon to fuse with main pokemon
        ttk.Label(frm, text="Available Pokemon: ").grid(column=4, row=0)
        self.__available_mons = ttk.Entry(frm, width=60)
        self.__available_mons.grid(column=5, row=0, columnspan=3)

        # ROW 1 separator
        ttk.Separator(frm, orient="horizontal").grid(column=0, row=1, columnspan=2)     # todo not working

        # Filter section
        row = 2
        ttk.Label(frm, text="Filter: ", style="BW.TLabel").grid(column=0, row=row)
        self.__filter = Filter()

        self.__filter.add_filter(frm, "bst", from_=0, to_=600, label="BST  ", col=0, row=row+1)

        self.__filter.add_filter(frm, "hp", from_=0, to_=200, label="HP   ", col=0, row=row+2)
        self.__filter.add_filter(frm, "atk", from_=0, to_=200, label="ATK  ", col=0, row=row+3)
        self.__filter.add_filter(frm, "spatk", from_=0, to_=200, label="SPATK", col=0, row=row+4)
        self.__filter.add_filter(frm, "def", from_=0, to_=200, label="DEF  ", col=0, row=row+5)
        self.__filter.add_filter(frm, "spdef", from_=0, to_=200, label="SPDEF", col=0, row=row+6)
        self.__filter.add_filter(frm, "spd", from_=0, to_=200, label="SPD  ", col=0, row=row+7)

        row = row+9
        ttk.Label(frm, text="Type: ").grid(column=0, row=row)
        self.__type = StringVar(value="")
        ttk.Combobox(frm, width=10, values=Pokemon.types(), textvariable=self.__type).grid(column=1, row=row, columnspan=2)

        ttk.Label(frm, text="Ability:").grid(column=0, row=row+1)
        self.__ability = StringVar(value="")
        ttk.Entry(frm, width=15, textvariable=self.__ability).grid(column=1, row=row+1, columnspan=2)

        # minimum completion rate of main pokemon's and other pokemon's evolution line
        row = row+2
        ttk.Label(frm, text="Min % ").grid(column=0, row=row)
        self.__e_rate = ttk.Entry(frm, width=3)
        self.__e_rate.grid(column=1, row=row)
        self.__e_rate.insert(0, f"{GUI.__DEFAULT_RATE}")    # todo validate input?

        ttk.Label(frm, text="Naturals?").grid(column=0, row=row+1)
        self.__natural_check = IntVar(value=1)
        ttk.Checkbutton(frm, onvalue=1, offvalue=0, variable=self.__natural_check).grid(column=1, row=row+1)

        ttk.Label(frm, text="End stage?").grid(column=0, row=row+2)
        self.__require_end_stage = IntVar(value=1)
        ttk.Checkbutton(frm, onvalue=1, offvalue=0, variable=self.__require_end_stage).grid(column=1, row=row+2)

        # Result section
        row = 2
        ttk.Label(frm, text="Results: ").grid(column=4, row=row)
        self.__tree_fusions = ttk.Treeview(frm, columns="fusions")
        self.__tree_fusions.grid(column=4, row=row+1, columnspan=2, rowspan=10)
        self.__tree_fusions.insert("", "end", "safe", text="Safe")
        self.__safe = Safe(self.__retriever,
                           insert=lambda id_, text: self.__tree_fusions.insert("safe", "end", id_, text=text),
                           delete=self.__tree_fusions.delete, reset_details=self.__reset_details)

        # Pokemon details section
        row = 2
        ttk.Label(frm, text="Selected Fusion Data: ").grid(column=6, row=row)
        self.__details: Dict[str, StringVar] = {}

        def add_detail(name: str, text: str, detail_row: int):
            detail_var = StringVar(value="?")
            ttk.Label(frm, text=text).grid(column=6, row=detail_row)
            ttk.Label(frm, textvariable=detail_var).grid(column=7, row=detail_row)
            self.__details[name] = detail_var
        row += 1
        add_detail("name", "", row)
        add_detail("bst", "BST:   ", row+1)
        add_detail("hp", "HP:    ", row+2)
        add_detail("atk", "ATK:   ", row+3)
        add_detail("spatk", "SPATK: ", row+4)
        add_detail("def", "DEF:   ", row+5)
        add_detail("spdef", "SPDEF: ", row+6)
        add_detail("spd", "SPEED: ", row+7)
        add_detail("type", "Type:  ", row+8)
        add_detail("abilities", "Abilities: ", row+9)

        row = row+12
        self.__b_save = ttk.Button(frm, text="Save", command=self.__save_details, width=15)
        self.__b_save.grid(column=6, row=row, columnspan=2)
        ttk.Button(frm, text="Swap", command=self.__swap_fusion, width=15).grid(column=6, row=row+1, columnspan=2)

        self.__tree_fusions.bind("<<TreeviewSelect>>", self.__set_details)

        # buttons at the bottom
        row = 18
        ttk.Button(frm, text="Analyse", command=self.__analyse, width=30).grid(column=0, row=row, columnspan=3)
        ttk.Button(frm, text="Reset", command=self.__reset, width=30).grid(column=4, row=row)

        # insert values
        if main_mon is not None:
            self.__e_main_mon.insert(0, main_mon)
        if available_mons is not None:
            self.__available_mons.insert("end", f"{GUI.__MON_SPLITER} ".join(available_mons) + "\n")

    def __set_details(self, event):
        encoded_id = self.__tree_fusions.focus()
        parsed_ids = gui_util.parse_ids_from_tree(encoded_id)
        if parsed_ids is None: return   # no valid pokemon id

        head_id, body_id = parsed_ids
        if body_id is None:
            pokemon = self.__retriever.get_pokemon(head_id)
        else:
            pokemon = FusionRetriever.from_ids(self.__retriever, head_id, body_id)

        if pokemon is not None:
            self.__details["name"].set(pokemon.name)
            self.__details["bst"].set(str(pokemon.bst))
            self.__details["hp"].set(str(pokemon.hp))
            self.__details["atk"].set(str(pokemon.atk))
            self.__details["spatk"].set(str(pokemon.spatk))
            self.__details["def"].set(str(pokemon.def_))
            self.__details["spdef"].set(str(pokemon.spdef))
            self.__details["spd"].set(str(pokemon.speed))

            type_str = f"{pokemon.type1} / {pokemon.type2}" if pokemon.is_dual_type else pokemon.type1
            self.__details["type"].set(type_str)

            ab_str = ""
            for i, ability in enumerate(pokemon.abilities):
                if i % 3 == 0: ab_str += "\n"
                ab_str += f"{ability}, "
            self.__details["abilities"].set(ab_str[:-2])    # remove trailing ", "

            # set the text of the button correspondingly
            if self.__safe.is_saved(parsed_ids):
                self.__b_save.configure(text="Remove")
            else:
                self.__b_save.configure(text="Save")

    def __reset_details(self):
        self.__details["name"].set("?")
        self.__details["bst"].set("")
        self.__details["hp"].set("")
        self.__details["atk"].set("")
        self.__details["spatk"].set("")
        self.__details["def"].set("")
        self.__details["spdef"].set("")
        self.__details["spd"].set("")

        self.__details["type"].set("")
        self.__details["abilities"].set("")

    def __save_details(self):
        if not self.__tree_is_resettable: return    # this means there are no head or body fusions

        encoded_id = self.__tree_fusions.focus()
        parsed_ids = gui_util.parse_ids_from_tree(encoded_id)
        if parsed_ids is None: return   # no valid pokemon id

        self.__safe.invert_state(parsed_ids)

    def __swap_fusion(self):
        encoded_id = self.__tree_fusions.focus()
        parsed_ids = gui_util.parse_ids_from_tree(encoded_id)
        if parsed_ids is None: return  # no valid pokemon id

        head_id, body_id = parsed_ids

        if encoded_id.startswith(gui_util.safe_prefix()):
            # if head_id is an end-stage, head_lines only has 1 element but else we can still ignore all but the first
            # element since the fusions of pre-line-split mons are present in all evolution lines
            # e.g.: consider the fusion Eevee + Charmander
            # get_evolution_lines(eevee) returns [Eevee, Vaporeon], [Eevee, Jolteon], ...
            # the fusion Eevee + Charmander is present in the evolution line fusion Vaporeon + Charizard, Jolteon +
            # Charizard, ...
            # therefore, we can simply look at Vaporen fusions (first element in list) and don't have to consider
            # Jolteon fusions etc.
            # similar if we consider fusion Jolteon + Charmander:
            # get_evolution_lines(jolteon) only returns [Eevee, Jolteon] -> we only have one element to consider
            # therefore, we can simply look at the first element of the list again
            end_head_id = self.__evo_helper.get_evolution_lines(head_id)[0].end_stage

            # same logic as described above
            end_body_id = self.__evo_helper.get_evolution_lines(body_id)[0].end_stage

            # there are four different possibilities of the original id present in tree_fusions
            swap1 = f"h{end_head_id}-{end_body_id}_{body_id}-{head_id}"
            swap2 = f"b{end_head_id}-{end_body_id}_{body_id}-{head_id}"
            swap3 = f"h{end_body_id}-{end_head_id}_{body_id}-{head_id}"
            swap4 = f"b{end_body_id}-{end_head_id}_{body_id}-{head_id}"
            for swap_id in [swap1, swap2, swap3, swap4]:
                if self.__tree_fusions.exists(swap_id):
                    self.__tree_fusions.selection_set(swap_id)
                    self.__tree_fusions.focus(swap_id)

        else:
            if "_" in encoded_id and body_id is not None:
                # we selected a concrete fusion
                data = encoded_id.split("_")  # first part is evolution line, second part is concrete

                swap_id = data[0]
                # swap prefix "h" with "b"
                if swap_id.startswith("h"): swap_id = "b" + swap_id[1:]
                else: swap_id = "h" + swap_id[1:]

                swap_id += f"_{body_id}-{head_id}"
                self.__tree_fusions.selection_set(swap_id)
                self.__tree_fusions.focus(swap_id)

            # else we didn't select a fusion and hence cannot reverse it

    def __reset(self, delete_safe: bool = True):
        if self.__tree_is_resettable:
            self.__tree_fusions.delete("head")
            self.__tree_fusions.delete("body")
            self.__tree_is_resettable = False
        if delete_safe:
            self.__tree_fusions.delete("safe")
            self.__tree_fusions.insert("", "end", "safe", text="Safe")

    def _filter_by_availability(self, evolution_lines: Iterable[EvolutionLine]) -> Iterable[EvolutionLine]:
        available_ids = []
        # go through every line in our text area for available pokemon
        for mon in self.__available_mons.get().split(";"):
            id_ = self.__retriever.get_id(mon)
            if id_ != -1: available_ids.append(id_)

        if len(available_ids) <= 0: return evolution_lines  # don't filter if we would get an empty result
        return EvolutionHelper.availability_filter(evolution_lines, available_ids)

    def _filter_by_input(self, evolution_lines: Iterable[EvolutionLine]) -> Iterable[EvolutionLine]:
        remaining = []
        for el in evolution_lines:
            mon = self.__retriever.get_pokemon(el.end_stage)
            if mon is None or self._filter_mon_by_input(mon):
                remaining.append(el)
        return remaining

    def _filter_mon_by_input(self, mon: Pokemon) -> bool:
        if self.__filter.fulfills_criteria(mon):  # check if stats are above filter values
            # also check type and ability
            type_ = self.__type.get()
            ability = self.__ability.get().strip()
            # either no type or a present type must have been given (and same for ability)
            if (len(type_) <= 0 or type_ in [mon.type1, mon.type2]) and \
                    (len(ability) <= 0 or ability in mon.abilities):
                return True
        return False

    def __analyse(self):
        # validate user input
        assert self.__retriever.get_id(self.__e_main_mon.get()) >= 0, f"Entry not valid: {self.__e_main_mon.get()}!"
        min_rate = float(self.__e_rate.get()) / 100     # convert % to decimal
        assert 0 <= min_rate <= 1.0, f"Invalid rate: {min_rate}!"

        self.__reset(delete_safe=False)      # remove old data before we analyse

        dex_num = self.__retriever.get_id(self.__e_main_mon.get())
        evo_lines = self.__evo_helper.get_evolution_lines(dex_num)

        self.__tree_fusions.insert("", "end", "head", text=f"Head")
        self.__tree_fusions.insert("", "end", "body", text=f"Body")
        # While it might seem a good idea to calculate head_fusions and body_fusions outside the loop (i.e., base mon is
        # always the same for each evo_line so its available fusions never change), it would blow up the code and make
        # it way harder to read while only being more efficient for edge cases (i.e., most pokemon only have a single
        # evolution line, hence below loop is only executed once). We would also need more transformations from sets to
        # lists and back to sets (i.e., combine lists of base and evo1 fusions to set and then in loop back to list to
        # add evo2 fusions and again back to set to have unique values) to it might not even be faster.
        for evo_line in evo_lines:
            filter_head_flag = True

            def analysis_filter(other_evo_line: EvolutionLine) -> bool:
                if filter_head_flag:
                    fused_line = FusedEvoLine(self.__retriever, evo_line, other_evo_line)
                else:
                    fused_line = FusedEvoLine(self.__retriever, other_evo_line, evo_line)

                # check if the final fusion stage is present if the corresponding checkbox is ticked
                if self.__require_end_stage.get() == 1 and not fused_line.has_final:
                    return False

                # use natural_rate or rate for comparison based on checkbox
                line_rate = fused_line.natural_rate if self.__natural_check.get() == 1 else fused_line.rate
                if line_rate < min_rate:
                    return False
                return self._filter_mon_by_input(fused_line.last_mon)

            # 1) get all fusions that use evolution line of the main mon as head (i.e., others are bodies)
            head_fusions = self.__retriever.get_fusions(evo_line.to_list(), as_head=True, as_names=False,
                                                        force_unique=True)
            # 2) combine found fusion ids to evolution lines
            head_fusions = self.__evo_helper.dex_nums_to_evo_lines(head_fusions)
            # 3) filter evolution lines based on user input of available mons (no filter if no mon provided)
            head_fusions = self._filter_by_availability(head_fusions)
            # 4) filter based on non-specific other user input (e.g., stats, type and ability)
            head_fusions = filter(analysis_filter, head_fusions)

            filter_head_flag = False
            # now perform the same steps as before but with main mons as bodies (i.e., others are heads)
            body_fusions = self.__retriever.get_fusions(evo_line.to_list(), as_head=False, as_names=False,
                                                        force_unique=True)
            body_fusions = self.__evo_helper.dex_nums_to_evo_lines(body_fusions)
            body_fusions = self._filter_by_availability(body_fusions)
            body_fusions = filter(analysis_filter, body_fusions)

            for data in self._get_fusion_tree_data_new(evo_line, head_fusions, body_fusions, min_rate):
                parent_id, item_id, text = data
                self.__tree_fusions.insert(parent_id, "end", item_id, text=text)
        self.__tree_is_resettable = True

    def _get_fusion_tree_data(self, main_line: EvolutionLine, fusion_list: Iterable[EvolutionLine], min_rate: float,
                              are_head_fusions: bool, sort_mode: int = __SM_RATE) -> List[Tuple[str, str, str]]:
        # we need to store three levels: main pokemon,
        tree_data: List[List[Tuple[str, str, str, int, float]]] = [[], [], [],]
        # appending scheme: "parent_id", "item_id", "text", id for sorting, rate for sorting
        elid = main_line.end_stage

        prefix = "h" if are_head_fusions else "b"

        # head fusions use the head from evo_line and the bodies from head_fusions (fusions with main mon as head)
        for other_line in fusion_list:
            fid = f"{elid}-{other_line.end_stage}"  # elid * util.max_id() + other_line.end_stage  # fusion id

            l1 = main_line if are_head_fusions else other_line
            l2 = other_line if are_head_fusions else main_line
            fusion_line = FusedEvoLine(self.__retriever, l1, l2, unidirectional=True)

            # continue with next value if fusion_line doesn't have enough coverage
            if fusion_line.rate < min_rate: continue

            tree_data[1].append((f"{prefix}{elid}", f"{prefix}{fid}",
                                 f"{self.__retriever.get_name(other_line.end_stage)} "
                                 f"#{other_line.end_stage}\t[{100 * fusion_line.rate:.0f}%]",
                                 other_line.end_stage, fusion_line.rate))

            if self.__natural_check.get() == 1:
                fusion_iterator = fusion_line.naturals(include_missing=False)
            else:
                fusion_iterator = fusion_line.existing

            for i, fusion in enumerate(fusion_iterator):
                head_mon, body_mon = fusion
                dex_num = body_mon if are_head_fusions else head_mon    # dex of the other pokemon for sorting
                head_name = self.__retriever.get_name(head_mon)
                body_name = self.__retriever.get_name(body_mon)
                tree_data[2].append((f"{prefix}{fid}", f"{prefix}{fid}_{head_mon}-{body_mon}",
                                     f"{head_name} / {body_name}", dex_num, 1))

        if len(tree_data[1]) > 0:   # only append if there are children (e.g. fusions)
            # append it at the end, so we can also display the number of fusion lines
            tree_data[0].append(("", f"{prefix}{elid}", f"{self.__retriever.get_name(main_line.end_stage)} "
                                                        f"#{main_line.end_stage} x{len(tree_data[1])}", elid, 1))

        if sort_mode == GUI.__SM_NAME:
            for td in tree_data: td.sort(key=lambda a: a[2])
        elif sort_mode == GUI.__SM_RATE:
            # tuples can be sorted automatically, so we use the rate first (negate to reverse the order) and on equal
            # rates we sort by name
            for td in tree_data: td.sort(key=lambda a: (-a[4], a[2]))
        else:   # sort by dex
            for td in tree_data: td.sort(key=lambda a: a[3])

        return [(t[0], t[1], t[2]) for t in tree_data[0] + tree_data[1] + tree_data[2]]

    def _get_fusion_tree_data_new(self, main_line: EvolutionLine, head_fusions: Iterable[EvolutionLine],
                                  body_fusions: Iterable[EvolutionLine], min_rate: float, sort_mode: int = __SM_RATE) \
            -> List[Tuple[str, str, str]]:
        # this function fuses head and body data by introducing a new "head" and "body" level and wrapping the data
        # correspondingly
        head_data = self._get_fusion_tree_data(main_line, head_fusions, min_rate, True, sort_mode)
        body_data = self._get_fusion_tree_data(main_line, body_fusions, min_rate, False, sort_mode)

        tree_data: List[Tuple[str, str, str]] = []
        for label, data_list in [("head", head_data), ("body", body_data)]:
            for data in data_list:
                parent_id, item_id, text = data
                if len(parent_id) <= 0:     # top level entry if we separate head and body
                    # add "label" level, so we can display both head and body fusions
                    tree_data.append((label, item_id, text))
                else:
                    tree_data.append(data)
        return tree_data

    def start(self):
        self.__root.mainloop()
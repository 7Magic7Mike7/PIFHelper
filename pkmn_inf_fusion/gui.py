
from tkinter import ttk, Tk, IntVar, StringVar
from typing import List, Tuple, Set

from pkmn_inf_fusion import EvolutionHelper, FusionRetriever, EvolutionLine, FusedEvoLine, util


class GUI:
    __DEFAULT_RATE = 0.5
    __SM_NAME = 0
    __SM_RATE = 1
    __SM_DEX = 2

    def __init__(self, base_path: str, retriever: FusionRetriever, evo_helper: EvolutionHelper):
        self.__base_path = base_path
        self.__retriever = retriever
        self.__evo_helper = evo_helper
        self.__root = Tk(screenName="Pokemon")
        self.__pokemon_list = retriever.get_all_names()
        self.__analyzed_mons: Set[int] = set()

        row = 0
        frm = ttk.Frame(self.__root, width=200, height=200, padding=10)
        frm.grid()

        ttk.Label(frm, text="Pokemon Infinite Fusion - Fusion Checker").grid(column=0, row=row)
        row += 1

        radio_command = None
        RB_NAME, RB_DEX = 1, 2
        radio_val = IntVar(master=frm, value=RB_NAME)
        rb_name = ttk.Radiobutton(frm, variable=radio_val, value=RB_NAME, text="by name", command=radio_command)
        rb_dex = ttk.Radiobutton(frm, variable=radio_val, value=RB_DEX, text="by Dex", command=radio_command)
        rb_name.grid(column=0, row=row)
        rb_dex.grid(column=1, row=row)
        row += 1

        def define_oder():
            if radio_val.get() == RB_NAME:
                self.__pokemon_list.sort()
            else:
                self.__pokemon_list = retriever.get_all_names()
        radio_command = define_oder
        radio_command()

        ttk.Label(frm, text="Main Pokemon: ").grid(column=0, row=row)
        self.__e_main_mon = ttk.Combobox(frm, values=self.__pokemon_list)
        self.__e_main_mon.grid(column=1, row=row, columnspan=1)
        row += 1

        ttk.Label(frm, text="Min rate: ").grid(column=0, row=row)
        self.__e_rate = ttk.Entry(frm)
        self.__e_rate.grid(column=1, row=row)
        row += 1

        ttk.Button(frm, text="Analyse", command=self.__analyse).grid(column=0, row=row)
        row += 1

        self.__details = StringVar()
        ttk.Label(frm, textvariable=self.__details).grid(column=0, row=row)
        row += 1

        ttk.Label(frm, text="Head Fusions: ").grid(column=2, row=0)
        self.__tree_head_fusions = ttk.Treeview(frm, columns=("fusions"))
        self.__tree_head_fusions.grid(column=2, row=1)

        ttk.Label(frm, text="Body Fusions: ").grid(column=3, row=0)
        self.__tree_body_fusions = ttk.Treeview(frm, columns=("fusions"))
        self.__tree_body_fusions.grid(column=3, row=1)

        self.__frame = ttk.LabelFrame(frm)
        self.__frame.grid(column=0, row=row)

        ttk.Button(frm, text="Reset", command=self.__reset).grid(column=1, row=0)
        # ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)

        self.__reset()
        self.__e_main_mon.insert(0, "Charmander")

    def __analyse(self):
        # validate user input
        assert self.__retriever.get_id(self.__e_main_mon.get()) >= 0, f"Entry not valid: {self.__e_main_mon.get()}!"
        min_rate = float(self.__e_rate.get())
        assert 0 <= min_rate <= 1.0, f"Invalid rate: {min_rate}!"

        # remove old widgets
        widgets_to_destroy = []
        for widget in self.__frame.children.values(): widgets_to_destroy.append(widget)
        for widget in widgets_to_destroy: widget.after(10, widget.destroy())
        print("cleaned widget")

        dex_num = self.__retriever.get_id(self.__e_main_mon.get())
        evo_lines = self.__evo_helper.get_evolution_lines(dex_num)

        new_evo_lines = []
        for el in evo_lines:    # filter out every pokemon we already analyzed
            if el.end_stage not in self.__analyzed_mons:
                new_evo_lines.append(el)
                self.__analyzed_mons.add(el.end_stage)

        head_fusions = self.__retriever.get_fusions(self.__base_path, dex_num, as_head=True, as_names=False)
        head_fusions = self.__evo_helper.dex_nums_to_evo_lines(head_fusions)

        body_fusions = self.__retriever.get_fusions(self.__base_path, dex_num, as_head=False, as_names=False)
        body_fusions = self.__evo_helper.dex_nums_to_evo_lines(body_fusions)

        for evo_line in new_evo_lines:
            for data in self.get_fusion_tree_data(evo_line, head_fusions, are_head_fusions=True):
                parent_id, item_id, text = data
                self.__tree_head_fusions.insert(parent_id, "end", item_id, text=text)

            for data in self.get_fusion_tree_data(evo_line, body_fusions, are_head_fusions=False):
                parent_id, item_id, text = data
                self.__tree_body_fusions.insert(parent_id, "end", item_id, text=text)

    def get_fusion_tree_data(self, main_line: EvolutionLine, fusion_list: List[EvolutionLine], are_head_fusions: bool,
                             sort_mode: int = __SM_RATE) -> List[Tuple[str, str, str]]:
        # we need to store three levels: main pokemon,
        tree_data: List[List[Tuple[str, str, str, int, float]]] = [[], [], [],]
        elid = main_line.end_stage
        tree_data[0].append(("", f"{elid}", f"{self.__retriever.get_name(main_line.end_stage)}", elid, 1))
        # head fusions use the head from evo_line and the bodies from head_fusions (fusions with main mon as head)
        for other_line in fusion_list:
            fid = elid * util.max_id() + other_line.end_stage

            l1 = main_line if are_head_fusions else other_line
            l2 = other_line if are_head_fusions else main_line
            fusion_line = FusedEvoLine(self.__base_path, self.__retriever, l1, l2, unidirectional=True)
            tree_data[1].append((f"{elid}", f"{fid}", f"{self.__retriever.get_name(other_line.end_stage)} "
                                                      f"[{100 * fusion_line.rate:.0f}%]",
                                 other_line.end_stage, fusion_line.rate))

            for i, fusion in enumerate(fusion_line.existing):
                head_mon, body_mon = fusion
                dex_num = body_mon if are_head_fusions else head_mon    # dex of the other pokemon for sorting
                head_mon = self.__retriever.get_name(head_mon)
                body_mon = self.__retriever.get_name(body_mon)
                tree_data[2].append((f"{fid}", f"{fid}_{i}", f"{head_mon} / {body_mon}", dex_num, 1))

        if sort_mode == GUI.__SM_NAME:
            for td in tree_data: td.sort(key=lambda a: a[2])
        elif sort_mode == GUI.__SM_RATE:
            for td in tree_data: td.sort(key=lambda a: a[4], reverse=True)
        else:   # sort by dex
            for td in tree_data: td.sort(key=lambda a: a[3])
        aaaa = tree_data[0] + tree_data[1] + tree_data[2]

        return [(t[0], t[1], t[2]) for t in aaaa]

    def __reset(self):
        # e_rate.pack()
        self.__e_rate.delete(0, len(self.__e_rate.get()))
        self.__e_rate.insert(0, f"{GUI.__DEFAULT_RATE}")

        items2delete = []
        #for item in self.__tree_head_fusions.grid:
        #    items2delete.append(item)
        for item in items2delete: self.__tree_head_fusions.delete(item)

        self.__tree_head_fusions.delete()
        #self.__e_detail_mon.delete(0, len(self.__e_detail_mon.get()))

    def start(self):
        self.__root.mainloop()
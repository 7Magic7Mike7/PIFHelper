from tkinter import ttk, DoubleVar, StringVar
from typing import Dict, Tuple, Optional

from pkmn_inf_fusion import Pokemon


class Filter:
    def __init__(self):
        self.__vars: Dict[str, Tuple[DoubleVar, StringVar, ttk.Label, ttk.Entry, ttk.Scale]] = {}

    def _parse_val(self, stat: str) -> float:
        _, string_var, _, _, _ = self.__vars[stat]
        return float(string_var.get())

    def _set_text(self, stat: str):
        assert stat in self.__vars, f"Variable={stat} not stored in this filter!"

        double_var, string_var, _, _, _ = self.__vars[stat]
        if string_var is not None and double_var is not None:
            string_var.set(f"{double_var.get():.0f}")

    def _set_scale(self, stat: str):
        assert stat in self.__vars, f"Variable={stat} not stored in this filter!"

        double_var, string_var, _, _, scale = self.__vars[stat]
        if string_var is not None and double_var is not None:
            val = self._parse_val(stat)
            double_var.set(val)  # todo check if val is valid/in range?

    def add_filter(self, master, name: str, from_: float, to_: float, label: Optional[str] = None,
                   col: Optional[int] = None, row: Optional[int] = None) -> Tuple[ttk.Label, ttk.Entry, ttk.Scale]:
        assert name not in self.__vars, f"Name={name} already used!"

        if label is None: label = name

        double_var = DoubleVar(value=0)
        string_var = StringVar(value="0")

        label_ = ttk.Label(master, text=label)

        entry_width = max(len(str(from_)), len(str(to_)))
        entry = ttk.Entry(master, width=entry_width, textvariable=string_var)
        entry.bind("<Key-Return>", lambda event: self._set_scale(name))

        scale = ttk.Scale(master, from_=from_, to=to_, variable=double_var,
                          command=lambda event: self._set_text(name))

        if col is None:
            label_.grid(row=row)
            entry.grid(row=row)
            scale.grid(row=row)
        else:
            label_.grid(column=col, row=row)
            entry.grid(column=col + 1, row=row)
            scale.grid(column=col + 2, row=row)

        self.__vars[name] = double_var, string_var, label_, entry, scale
        return label_, entry, scale

    def fulfills_criteria(self, mon: Pokemon) -> bool:
        if mon.bst < self._parse_val("bst"):
            return False
        if mon.hp < self._parse_val("hp"):
            return False
        if mon.atk < self._parse_val("atk"):
            return False
        if mon.spatk < self._parse_val("spatk"):
            return False
        if mon.def_ < self._parse_val("def"):
            return False
        if mon.spdef < self._parse_val("spdef"):
            return False
        if mon.speed < self._parse_val("spd"):
            return False

        return True

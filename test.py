import os
import unittest
from typing import Dict

import pkmn_inf_fusion as pif
from pkmn_inf_fusion import Pokemon


class MyTestCase(unittest.TestCase):
    @staticmethod
    def load_default_path() -> str:
        path = os.path.join("data", "default_path")
        with open(path, "rt") as file:
            line = file.readline()
            return line

    def test_evo_line(self):
        line = pif.EvolutionLine(1, "2, 3")
        self.assertTrue(1 in line, f"1 not in {line}")
        self.assertTrue(2 in line, f"2 not in {line}")
        self.assertTrue(3 in line, f"3 not in {line}")

    def test_evolution_file(self):
        evo_file = os.path.join("data", "evolutions.txt")
        evo_helper = pif.EvolutionHelper(evo_file)

        for dex_num in range(pif.util.min_id(), pif.util.max_id() + 1):
            if dex_num == 107:
                debug = True

            evo_lines = evo_helper.get_evolution_lines(dex_num)
            self.assertGreater(len(evo_lines), 0,
                               f"No evolution line for {dex_num}")

    def test_dex_num(self):
        base_path = MyTestCase.load_default_path()
        dex_names = os.path.join("data", "dex_names.txt")
        helper = pif.Helper(base_path, dex_names)

        id_ = helper.retriever.get_id("Raichu")

        self.assertEqual(id_, 26)

        heads = helper.get_head_fusions(id_)
        # heads.sort()
        bodies = helper.get_body_fusions(id_)
        # bodies.sort()
        print(f"As head #{len(heads)}:")
        print(", ".join([f"{body}" for body in heads]))
        print()
        print(f"As body #{len(bodies)}:")
        print(", ".join([f"{head}" for head in bodies]))

    def test_eevee_lines(self):
        base_path = MyTestCase.load_default_path()
        dex_names = os.path.join("data", "dex_names.txt")
        helper = pif.Helper(base_path, dex_names)

        evo_file = os.path.join("data", "evolutions.txt")
        evo_helper = pif.EvolutionHelper(evo_file)

        id_ = helper.retriever.get_id("Eevee")
        evo_lines = evo_helper.get_evolution_lines(id_)
        self.assertEqual(len(evo_lines), 8)

        evo_name = helper.retriever.get_name(evo_lines[0].evo1)
        id_ = helper.retriever.get_id(evo_name)
        evo_lines = evo_helper.get_evolution_lines(id_)
        self.assertEqual(len(evo_lines), 1)

    def test_dex2evo_line(self):
        base_path = MyTestCase.load_default_path()
        dex_names = os.path.join("data", "dex_names.txt")
        helper = pif.Helper(base_path, dex_names)

        evo_file = os.path.join("data", "evolutions.txt")
        evo_helper = pif.EvolutionHelper(evo_file)

        dex_nums = [1, 2, 3, 4, 6]
        reduced_evo_lines = evo_helper.dex_nums_to_evo_lines(dex_nums)
        self.assertEqual(len(reduced_evo_lines), 2)

        dex_nums.append(helper.retriever.get_id("Slowking"))
        reduced_evo_lines = evo_helper.dex_nums_to_evo_lines(dex_nums)
        self.assertEqual(len(reduced_evo_lines), 3)

        dex_nums.append(helper.retriever.get_id("Slowpoke"))
        reduced_evo_lines = evo_helper.dex_nums_to_evo_lines(dex_nums)
        self.assertEqual(len(reduced_evo_lines), 4)

    def test_json_parser(self):
        base_path = os.path.join("D:\\", "Games", "Pokemon", "infinitefusion_5.1.0.1-full")
        path = os.path.join("data", "pokedex.json")

        mons = Pokemon.load_from_json(path)
        helper = pif.Helper(base_path, os.path.join("data", "dex_names.txt"))

        mon_dic: Dict[str, Pokemon] = {}
        for mon in mons: mon_dic[mon.name] = mon

        for name in helper.retriever.get_all_names():
            self.assertTrue(name in mon_dic, f"{name} not found!")

        helper.refresh_pif_dex_json("data")

        new_path = os.path.join("data", "pif_dex.json")
        self.assertEqual(len(Pokemon.load_from_json(new_path)), len(helper.retriever.get_all_names()),
                         "Generated json builds different amount of Pokemon than supported!")


if __name__ == '__main__':
    unittest.main()

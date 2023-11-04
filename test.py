import json
import os
import time
import unittest
from typing import Dict

import pkmn_inf_fusion as pif
from pkmn_inf_fusion import Pokemon, util


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
        evo_helper = pif.EvolutionHelper.from_txt(evo_file)

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
        evo_helper = pif.EvolutionHelper.from_txt(evo_file)

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
        evo_helper = pif.EvolutionHelper.from_txt(evo_file)

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

    def test_retrieval_speed(self):
        # while dynamic is significantly (~20x) faster in creation,
        # it's way slower in processing fusions (~13x for heads, ~1800x for body due to changing folders)

        base_path = MyTestCase.load_default_path()

        times = {
            "dynamic": {},
            "static": {}
        }

        def set_time(mode: str, label: str):
            cur_time = time.time()
            if label in times[mode]:
                last_time = times[mode][label]
                times[mode][label] = round(cur_time - last_time, ndigits=7)
            else:
                times[mode][label] = cur_time

        set_time("dynamic", "init")
        dynamic = pif.DynamicFusionRetriever(os.path.join("data", "dex_names.txt"), base_path)
        set_time("dynamic", "init")

        set_time("static", "init")
        static = pif.StaticFusionRetriever("data", "data")
        set_time("static", "init")

        ##################################################################
        set_time("dynamic", "all fusions_head")
        for id_ in range(util.min_id(), util.max_id() + 1):
            dynamic.get_fusions(id_, as_head=True, as_names=True)
        set_time("dynamic", "all fusions_head")

        set_time("static", "all fusions_head")
        for id_ in range(util.min_id(), util.max_id() + 1):
            static.get_fusions(id_, as_head=True, as_names=True)
        set_time("static", "all fusions_head")
        ##################################################################

        ##################################################################
        set_time("dynamic", "all fusions_body")
        for id_ in range(util.min_id(), util.max_id() + 1):
            dynamic.get_fusions(id_, as_head=False, as_names=True)
        set_time("dynamic", "all fusions_body")

        set_time("static", "all fusions_body")
        for id_ in range(util.min_id(), util.max_id() + 1):
            static.get_fusions(id_, as_head=False, as_names=True)
        set_time("static", "all fusions_body")
        ##################################################################

        # no need to test for as_names=False since this is basically instant (O(1)) for static

        print("dynamic: ", times["dynamic"])
        print("static:  ", times["static"])

    def test_natural_fusion_lines(self):
        base_path = MyTestCase.load_default_path()
        dex_names = os.path.join("data", "dex_names.txt")
        helper = pif.Helper(base_path, dex_names)

        with open(os.path.join("data", "evolutions.json"), encoding='utf-8') as file:
            # Load the JSON data
            data = json.load(file)
        new_evo_helper = pif.EvolutionHelper.from_json(data)
        old_evo_helper = pif.EvolutionHelper.from_txt(os.path.join("data", "evolutions.txt"))

        test = [helper.retriever.get_name(id_) for id_ in [81, 82, 263]]

        for id_ in range(util.min_id(), util.max_id()):
            new_result = [evo_line.to_list() for evo_line in new_evo_helper.get_evolution_lines(id_)]
            old_result = [evo_line.to_list() for evo_line in old_evo_helper.get_evolution_lines(id_)]

            self.assertEqual(len(new_result), len(old_result), "Found different results!")
            for i in range(len(new_result)):
                self.assertSequenceEqual(new_result[i], old_result[i], f"Difference at {i}")
            debug = True


if __name__ == '__main__':
    unittest.main()

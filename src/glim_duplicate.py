#!/usr/bin/env python
import json
import os
import re
import unicodedata
import glim_charset_gen
from lua_helper import dump_lua
from glim_layouts import (
    Glyph_mappings,
    Sing_ch,
    Extra_No_Auto,
    Algebras,
    Layouts,
    py_full_double_converter,
    glyph_encoding,
)
import string
from operator import itemgetter


def normalPinyin(pinyin):
    return (
        unicodedata.normalize("NFKD", pinyin).encode("ascii", "ignore").decode("utf-8")
    )


class DupFinder:
    def __init__(self, phrases_file="../dicts/glim_phrase.dict.yaml"):
        _, py_han_dict = glim_charset_gen.charset_gen()
        phrases_raw = open(phrases_file, "r").read().splitlines()
        self.py_han_dict = py_han_dict
        self.phrases_list = list(
            filter(lambda x: not re.match("[a-z-.# ]|^$", x), phrases_raw)
        )
        self.dup_table_folder = "../cache/lua/duplicate"
        self.dup_json_folder = "../cache/json/duplicate"
        if not os.path.exists(self.dup_table_folder):
            os.makedirs(self.dup_table_folder)
        if not os.path.exists(self.dup_json_folder):
            os.makedirs(self.dup_json_folder)

    def full_code_dict_gen(
        self, glyph_dict, algebra, charset_8105="../assets/8105.txt"
    ):
        full_code_dict = {}  # { ..., "也": [["yě"]], ... }
        charset_list = open(charset_8105, "r").read().splitlines()
        for line in charset_list:
            ch = line.split("\t")[1]
            pys = line.split("\t")[2].split(", ")
            if not ch in full_code_dict.keys() and ch in glyph_dict.keys():
                py_list = [
                    py_full_double_converter(x, algebra)
                    for x in list(map(normalPinyin, pys))
                ]
                ch_glyph = glyph_dict[ch]["gl1"] + glyph_dict[ch]["gl2"]
                full_code_list = list(map(lambda x: x + ch_glyph, py_list))
                for code in full_code_list:
                    if not code in full_code_dict.keys():
                        full_code_dict[code] = [ch]
                    else:
                        if not ch in full_code_dict[code]:
                            full_code_dict[code].append(ch)
        return full_code_dict

    def double_han_dict_gen(self, glyph_dict, algebra):
        double_han_dict = {}
        for full_py, pure in self.py_han_dict.items():
            pure = list(filter(lambda han: han not in Extra_No_Auto, pure))
            if full_py in Sing_ch.keys():
                pure = list(filter(lambda han: han != Sing_ch[full_py], pure))
            double_py = py_full_double_converter(full_py, algebra)
            double_han_dict[double_py] = {"pure": pure}
            for ch in string.ascii_lowercase:
                glyph_match = list(
                    filter(
                        lambda han: han in glyph_dict.keys()
                        and glyph_dict[han]["gl1"] == ch
                        and han != pure[0],
                        pure,
                    )
                )
                if len(glyph_match) > 0:
                    double_han_dict[double_py][ch] = glyph_match
                else:
                    double_han_dict[double_py][ch] = None

        return double_han_dict

    def convert_phrases(self, meta, size=None):
        if not size:
            size = len(self.phrases_list)
        mapping = Glyph_mappings[meta["mapping"]]
        algebra = Algebras[meta["algebra"]]
        glyph_dict = glyph_encoding(mapping)
        full_code_dict = self.full_code_dict_gen(glyph_dict, algebra)
        double_han_dict = self.double_han_dict_gen(glyph_dict, algebra)
        phrases = {}
        pinyin_uniq = {}
        for i in range(0, size):
            item = self.phrases_list[i].split("\t")
            phrase = item[0]
            pys = item[1]
            if len(phrase) == 2:
                head = phrase[0]
                tail = phrase[1]
                if (
                    not pys in pinyin_uniq.keys()
                    and head in glyph_dict.keys()
                    and tail in glyph_dict.keys()
                ):
                    pinyin_uniq[pys] = 1
                    double_pys = "".join(
                        [py_full_double_converter(py, algebra) for py in pys.split(" ")]
                    )
                    phrases[phrase] = double_pys
        return glyph_dict, full_code_dict, double_han_dict, phrases

    def try_get_dup_dict(self, layout):
        dup_json_path = self.dup_json_folder + "/" + layout + ".json"
        if os.path.exists(dup_json_path):
            return json.load(open(dup_json_path, "r"))
        else:
            return self.get_duplicate(Layouts[layout])

    def get_duplicate(self, meta, size=None):
        if not size:
            size = len(self.phrases_list)
        _, full_code_dict, double_han_dict, phrases = self.convert_phrases(meta, size)
        duplicate_in_code = {}
        for k, v in phrases.items():
            if v in full_code_dict.keys():
                duplicate_in_code[k] = {
                    "double": v[:2],
                    "l3": v[2:3],
                    "full": v,
                    "hans": full_code_dict[v],
                }
        duplicate = {}
        for phrase, info in duplicate_in_code.items():
            really_duplicate = True
            double, l3, full, hans = itemgetter("double", "l3", "full", "hans")(info)
            if len(hans) == 1:
                han_in_2 = double_han_dict[double]["pure"][0] == hans[0]
                han_in_3 = (
                    double_han_dict[double][l3]
                    and double_han_dict[double][l3][0] == hans[0]
                )
                if hans[0] in Sing_ch.values():
                    really_duplicate = False
                if han_in_2:
                    really_duplicate = False
                elif han_in_3:
                    really_duplicate = False
            if really_duplicate:
                duplicate[full] = {"phrase": phrase, "word": hans}
        return duplicate

    def analysis_dup_without_phrase(self):
        glyph_dict, _, double_han_dict, _ = self.convert_phrases(Layouts["chole"])
        reversed_double_han_dict = {}
        for double, glyph_set in double_han_dict.items():
            for ch in string.ascii_lowercase:
                l3 = double + ch
                hans = glyph_set[ch]
                if hans:
                    len_left = len(hans)
                    code_dup = {}
                    first = l3 + glyph_dict[hans[0]]["gl2"]
                    for han in hans:
                        full_code = l3 + glyph_dict[han]["gl2"]
                        if not full_code in code_dup.keys():
                            code_dup[full_code] = [han]
                        else:
                            code_dup[full_code].append(han)
                    for code, dup_hans in code_dup.items():
                        if code != first and len(dup_hans) == 1:
                            len_left -= 1
                    for code, dup_hans in code_dup.items():
                        if (
                            (code == first and len(dup_hans) > 2)
                            or (code != first and len(dup_hans) > 1)
                            and len_left > 3
                        ):
                            dup_full = list(
                                filter(lambda han: han != hans[0], dup_hans)
                            )
                            reversed_double_han_dict[code] = [dup_full, hans]
        dict_output = self.dup_json_folder + "/" + "dup-without-ph.json"
        with open(dict_output, "w") as dict_out:
            json.dump(reversed_double_han_dict, dict_out)

    def analysis_dup_with_phrase(self, layout="chole"):
        phrase_dup = self.try_get_dup_dict(layout)
        glyph_dict, full_code_dict, double_han_dict, _ = self.convert_phrases(
            Layouts[layout]
        )
        reversed_double_han_dict = {}
        for double, glyph_set in double_han_dict.items():
            for ch in string.ascii_lowercase:
                l3 = double + ch
                hans = glyph_set[ch]
                if hans:
                    reverse_match = list(
                        filter(
                            lambda han: hans.index(han) > 0
                            and l3 + glyph_dict[han]["gl2"] in phrase_dup,
                            hans,
                        )
                    )
                    if len(reverse_match) > 2:
                        match_with_phrase = [
                            [han, phrase_dup[l3 + glyph_dict[han]["gl2"]]["phrase"]]
                            for han in reverse_match
                        ]
                        reversed_double_han_dict[l3] = match_with_phrase
        print(reversed_double_han_dict)
        dict_output = self.dup_json_folder + "/" + layout + "-rev.json"
        with open(dict_output, "w") as dict_out:
            json.dump(reversed_double_han_dict, dict_out)

    def get_dup_all_layout(self):
        dup_all_layouts = {}
        for layout, meta in Layouts.items():
            dup_all_layouts[layout] = self.get_duplicate(meta)
        return dup_all_layouts

    def dump_json(self):
        dup_all = self.get_dup_all_layout()
        for layout, code in dup_all.items():
            dict_output = self.dup_json_folder + "/" + layout + ".json"
            with open(dict_output, "w") as dict_out:
                json.dump(code, dict_out)

    def dump_lua(self):
        dup_all = self.get_dup_all_layout()
        for layout, code in dup_all.items():
            dict_output = self.dup_table_folder + "/" + layout + ".lua"
            with open(dict_output, "w") as dict_out:
                dict_out.write("local dup_table = ")
                dict_out.write(dump_lua(code))
                dict_out.write("\nreturn dup_table")


if __name__ == "__main__":
    finder = DupFinder()
    # finder.analysis_dup_without_phrase()
    # finder.analysis_dup_with_phrase("chole")
    # finder.dump_json()
    finder.dump_lua()

#!/usr/bin/env python
# import json
import os
import re
import unicodedata
import glim_charset_gen
from lua_helper import dump_lua
from glim_layouts import (
    Glyph_mappings,
    Sing_ch,
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


def full_code_dict_gen(glyph_dict, algebra, charset_8105="../assets/8105.txt"):
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


def double_han_dict_gen(py_han_dict, glyph_dict, algebra):
    double_han_dict = {}
    for full_py, pure in py_han_dict.items():
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


def get_duplicate(py_han_dict, layout, meta, phrases_list):
    mapping = Glyph_mappings[meta["mapping"]]
    algebra = Algebras[meta["algebra"]]
    glyph_dict = glyph_encoding(mapping)
    full_code_dict = full_code_dict_gen(glyph_dict, algebra)
    double_han_dict = double_han_dict_gen(py_han_dict, glyph_dict, algebra)
    phrases = {}
    pinyin_uniq = {}
    for i in range(0, len(phrases_list)):
        item = phrases_list[i].split("\t")
        word = item[0]
        py = item[1]
        if len(word) == 2:
            head = word[0]
            tail = word[1]
            if not py in pinyin_uniq.keys():
                pinyin_uniq[py] = 1
                if head in glyph_dict.keys() and tail in glyph_dict.keys():
                    py_head = py_full_double_converter(py.split(" ")[0], algebra)
                    py_tail = py_full_double_converter(py.split(" ")[1], algebra)
                    phrases[word] = py_head + py_tail
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
                double_han_dict[double][l3] and double_han_dict[double][l3][0] == hans[0]
            )
            if hans[0] in Sing_ch:
                really_duplicate = False
            elif han_in_2:
                really_duplicate = False
            elif han_in_3:
                really_duplicate = False
        if really_duplicate:
            duplicate[full] = {"phrase": phrase, "word": hans}

    # print(duplicate["iirl"])
    # print(duplicate_in_code["是让"])
    # # print(double_han_dict)
    # print(double_han_dict["ii"]["pure"], double_han_dict["ii"]["r"])
    # print(phrases["是让"])
    #     first100 = {k: duplicate_in_code[k] for k in list(duplicate_in_code)[:100]}
    #     print(first100)
    # # print(len(list(duplicate)))
    # # dup_table_folder = "../cache/lua/duplicate"
    # # dict_output = dup_table_folder + "/duplicate.lua"
    return duplicate


def get_dup(phrase_dict):
    f = open(phrase_dict, "r").read().splitlines()
    phrases_list = list(filter(lambda x: not re.match("[a-z-.# ]|^$", x), f))
    _, py_han_dict = glim_charset_gen.charset_gen()
    dup_all_layouts = {}
    for layout, meta in Layouts.items():
        dup_all_layouts[layout] = get_duplicate(py_han_dict, layout, meta, phrases_list)
    return dup_all_layouts


if __name__ == "__main__":
    dup_table_folder = "../cache/lua/duplicate"
    phrase_dict = "../dicts/glim_phrase.dict.yaml"
    if not os.path.exists(dup_table_folder):
        os.makedirs(dup_table_folder)
    dup_all = get_dup(phrase_dict)
    for layout, code in dup_all.items():
        dict_output = dup_table_folder + "/" + layout + ".lua"
        with open(dict_output, "w") as dict_out:
            dict_out.write("local dup_table = ")
            dict_out.write(dump_lua(code))
            dict_out.write("\nreturn dup_table")
        
    

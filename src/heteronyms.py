#!/usr/bin/env python
# import json
import os
import re
import unicodedata
from pypinyin import lazy_pinyin, pinyin, Style, load_phrases_dict

han_py_list = []  # [ '的 de', '了 le', ... ]
py_han_dict = {}  # { 'de': ['的', '得', ...], ... }
han_py_dict = {}  # { '的': ['de', 'di'], ... }
lazy_full_dict = {}


def dump_lua(data):
    if type(data) is str:
        return f'"{re.escape(data)}"'
    if type(data) in (int, float):
        return f"{data}"
    if type(data) is bool:
        return data and "true" or "false"
    if type(data) is list:
        l = ", ".join([dump_lua(item) for item in data])
        return "{" + l + "}\n"
    if type(data) is dict:
        kv_pairs = ", ".join(
            [f'["{re.escape(k)}"]={dump_lua(v)}' for k, v in data.items()]
        )
        return "{" + kv_pairs + "}\n"


def fixPinyin(pinyin):
    if pinyin == "n":
        pinyin = "en"
    elif pinyin == "m":
        pinyin = "mu"
    elif pinyin == "ng":
        pinyin = "en"
    else:
        return pinyin
    return pinyin


def normalPinyin(pinyin):
    return (
        unicodedata.normalize("NFKD", pinyin).encode("ascii", "ignore").decode("utf-8")
    )


def is_heteronyms(ch):
    return len(lazy_full_dict[ch]) > 1


def get_heteronyms_ch(pair):
    han = pair[0]
    py = pair[1]
    item = han + " " + py
    i = 0
    han_same = py_han_dict[py][0]
    while is_heteronyms(han_same) and i < len(py_han_dict[py]):
        i += 1
        if len(py_han_dict[py]) > i:
            han_same = py_han_dict[py][i]
    return [han_same, han_py_list.index(han + " " + py)]


def heteronyms(singch_dict):
    full_py_dict = {}  # { ..., "也": [["yě"]], ... }
    charset_list = open(lvl_all_ch_set, "r").read().splitlines()
    for line in charset_list:
        ch = line.split("\t")[1]
        pys = line.split("\t")[2].split(", ")
        if not ch in full_py_dict.keys():
            full_py_dict[ch] = [pys]
    load_phrases_dict(full_py_dict)
    for k, v in full_py_dict.items():
        lazy_full_dict[k] = list(
            map(fixPinyin, pinyin(k, style=Style.NORMAL, heteronym=True)[0])
        )
        if not re.match("[a-z]+", lazy_full_dict[k][0]):
            lazy_full_dict[k] = list(map(normalPinyin, full_py_dict[k][0]))

    chars = list(filter(lambda x: not re.match("[a-z-.# ]|^$", x), open(singch_dict, "r").read().splitlines()))
    dict_raw = list(map(lambda x: x.split("\t"), chars))

    for item in dict_raw:
        han = item[0]
        py = item[1]

        if han in lazy_full_dict.keys() and py in lazy_full_dict[han]:
            han_py_list.append(han + " " + py)
            if not py in py_han_dict.keys():
                py_han_dict[py] = [han]
            else:
                py_han_dict[py].append(han)
            if not han in han_py_dict.keys():
                han_py_dict[han] = list(
                    map(fixPinyin, pinyin(han, style=Style.NORMAL, heteronym=True)[0])
                )
    sorted_8105 = []
    for han_py in han_py_list:
        if not han_py[0] in sorted_8105:
            sorted_8105.append(han_py[0])
    for han in full_py_dict.keys():
        if not han in sorted_8105:
            sorted_8105.append(han)

    heteronyms_dict = {}
    for k, v in lazy_full_dict.items():
        if len(v) > 1:
            ch_py_pair = list(map(lambda x: [k, x], v))
            ch_ch_pair = list(map(get_heteronyms_ch, ch_py_pair))
            heteronyms_dict[k] = ch_ch_pair

    dict_8105 = {}
    for han in sorted_8105:
        dict_8105[han] = {}
        dict_8105[han]["rank"] = sorted_8105.index(han)
        if is_heteronyms(han):
            dict_8105[han]["heteronym"] = {}
            for pair in heteronyms_dict[han]:
                if not pair[0] in dict_8105[han]["heteronym"].keys():
                    dict_8105[han]["heteronym"][pair[0]] = pair[1]
        else:
            dict_8105[han]["heteronym"] = False

    ## 得，嘚 同为 [ de, dei ], 会影响 ensure_different_onechar
    dict_8105["得"]["heteronym"] = False

    with open(dict_output, "w") as dict_out:
        dict_out.write("local charset_table = ")
        dict_out.write(dump_lua(dict_8105))
        dict_out.write("\nreturn charset_table")


if __name__ == "__main__":
    dict_data_dev = "../cache/dict_data"
    singch_dict = "../assets/glim_base.dict.yaml"
    lvl_all_ch_set = "../assets/8105.txt"
    if not os.path.exists(dict_data_dev):
        os.makedirs(dict_data_dev)
    dict_output = dict_data_dev + "/charset_table.lua"
    exit(heteronyms(singch_dict))

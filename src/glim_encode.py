#!/usr/bin/env python
import os
import fnmatch
import re
import argparse
import datetime
import json

glyph_encoding_dict = {}
glyph_mappings = {
    "glyph_table_I": {
        "a": {"map": "a"},
        "b": {"map": "b"},
        "c": {"map": "c"},
        "d": {"map": "d"},
        "e": {"map": "e"},
        "f": {"map": "f"},
        "g": {"map": "g"},
        "h": {"map": "h"},
        "i": {"map": "i"},
        "j": {"map": "j"},
        "k": {"map": "k"},
        "l": {"map": "l"},
        "m": {"map": "m"},
        "n": {"map": "n"},
        "o": {"map": "o"},
        "p": {"map": "p"},
        "q": {"map": "q"},
        "r": {"map": "r"},
        "s": {"map": "s"},
        "t": {"map": "t"},
        "u": {"map": "u"},
        "v": {"map": "v"},
        "w": {"map": "w"},
        "x": {"map": "x"},
        "y": {"map": "y"},
        "z": {"map": "z"},
    },
    "glyph_table_II": {
        "a": {"map": "a"},
        "b": {"map": "b"},
        "c": {"map": "c"},
        "d": {"map": "d"},
        "e": {"map": "e"},
        "f": {"map": "f"},
        "g": {"map": "g"},
        "h": {"map": "h"},
        "i": {"map": "u"},
        "j": {"map": "j"},
        "k": {"map": "k"},
        "l": {"map": "l"},
        "m": {"map": "m"},
        "n": {"map": "n"},
        "o": {"map": "o"},
        "p": {"map": "p"},
        "q": {"map": "q"},
        "r": {"map": "r"},
        "s": {"map": "s"},
        "t": {"map": "t"},
        "u": {"map": "i"},
        "v": {"map": "v"},
        "w": {"map": "w"},
        "x": {"map": "x"},
        "y": {"map": "y"},
        "z": {"map": "z"},
    },
}


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


def glyph_encoding_dev(glyph_dict):
    dict_json = json.load(open(glyph_dict, "r"))
    for i in dict_json:
        glyph_encoding_dict[i["character"]] = (
            glyph_mappings["glyph_table_II"][i["first_py"]]["map"]
            + glyph_mappings["glyph_table_II"][i["last_py"]]["map"]
        )


def glyph_encoding(glyph_dict):
    dict_json = json.load(open(glyph_dict, "r"))
    with open(glyph_lua_table, "a") as table_out:
        for layout_type, mappings in glyph_mappings.items():
            glyph_encoding_lua = {}
            for i in dict_json:
                glyph_encoding_lua[i["character"]] = {
                    "first_py": mappings[i["first_py"]]["map"],
                    "last_py": mappings[i["last_py"]]["map"],
                    "first_gl": i["first_part"],
                    "last_gl": i["last_part"],
                    "level": int(i["level"]),
                }
            table_out.write("local " + layout_type + " = \n")
            table_out.write(dump_lua(glyph_encoding_lua))
            table_out.write("\n")
        return_str = "return { "
        for key in glyph_mappings.keys():
           return_str += key + " = " + key + ", "
        return_str += " }"
        table_out.write(return_str)


def add_glyph_code(item):
    word = [ch for ch in item[0]]
    pinyin = item[1].split(" ")
    enc = lambda x: ":" + glyph_encoding_dict[x] if x in glyph_encoding_dict else ""
    word_pg_encoded = list(map(enc, word))
    item[1] = " ".join([a + b for a, b in zip(pinyin, word_pg_encoded)])
    return "\t".join(item)


def convert_dict(raw_dict):
    dict_input = os.path.join("../cache", raw_dict)
    dict_output = os.path.join(dict_data_dev, raw_dict)
    f = open(dict_input, "r").read().splitlines()
    f_strip = list(filter(lambda x: not re.match("[a-z-.# ]|^$", x), f))
    dict_raw = list(map(lambda x: x.split("\t"), f_strip))
    dict_processed = list(map(add_glyph_code, dict_raw))
    with open(dict_output, "w+") as dict_out:
        dict_out.writelines("%s\n" % line for line in dict_processed)


def main(args):
    if args.dev:
        glyph_encoding_dev(xiaohe_glyph_dict)
        for file in os.listdir("../cache"):
            if fnmatch.fnmatch(file, "*.yaml"):
                convert_dict(file)
    else:
        glyph_encoding(xiaohe_glyph_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Glim 辅助码码表生成工具。")
    parser.add_argument(
        "--dev", "-d", help="生成开发相关词典数据.", action=argparse.BooleanOptionalAction
    )
    args = parser.parse_args()
    dict_data_dev = "../cache/dict_data"
    xiaohe_glyph_dict = "../assets/xiaohe-8105.json"
    glyph_lua_table = dict_data_dev + "/glyph_table.lua"
    if os.path.exists(glyph_lua_table):
        os.remove(glyph_lua_table)
    if args.dev and not os.path.exists(dict_data_dev):
        os.makedirs(dict_data_dev)
    exit(main(args))

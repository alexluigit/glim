#!/usr/bin/env python
import os
import fnmatch
import re
import argparse
import datetime
import json
from string import ascii_lowercase

xiaohe_glyph_dict = "../assets/xiaohe-8105.json"
dict_data_dev = "../cache/dict_data"
glyph_lua_table = dict_data_dev + "/glyph_table.lua"
alphabet_lua_table = dict_data_dev + "/alphabet_table.lua"

glyph_encoding = {}
glyph_encoding_lua = {}
alphabet_to_chars_lua = {}


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


def init_glyph_encoding(glyph_dict, mapping):
    mappings = json.load(open(mapping, "r"))
    dict_json = json.load(open(glyph_dict, "r"))
    for i in dict_json:
        glyph_encoding[i["character"]] = (
            mappings[i["first_py"]]["map"] + mappings[i["last_py"]]["map"]
        )
        glyph_encoding_lua[i["character"]] = {
            "first_py": mappings[i["first_py"]]["map"],
            "last_py": mappings[i["last_py"]]["map"],
            "first_gl": i["first_part"],
            "last_gl": i["last_part"],
            "level": int(i["level"]),
        }

    for c in ascii_lowercase:
        alphabet_to_chars_lua[c] = mappings[c]["chars"]

    print(len(glyph_encoding))


def add_glyph_code(item):
    word = [ch for ch in item[0]]
    pinyin = item[1].split(" ")
    enc = lambda x: ":" + glyph_encoding[x] if x in glyph_encoding else ""
    word_pg_encoded = list(map(enc, word))
    item[1] = " ".join([a + b for a, b in zip(pinyin, word_pg_encoded)])
    return "\t".join(item)


def convert_dict(raw_dict, dev=False):
    dict_name = raw_dict.split(".")[0]
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f'---\nname: {dict_name}\nversion: "{date}"\nsort: by_weight\n...\n'

    dict_input = os.path.join("../cache", raw_dict)
    dict_output = os.path.join(output, raw_dict)
    f = open(dict_input, "r").read().splitlines()
    f_strip = list(filter(lambda x: not re.match("[a-z-.# ]|^$", x), f))
    dict_raw = list(map(lambda x: x.split("\t"), f_strip))
    dict_processed = list(map(add_glyph_code, dict_raw)) if dev else f_strip

    with open(dict_output, "w+") as dict_out:
        if not dev:
            dict_out.write(header)
        dict_out.writelines("%s\n" % line for line in dict_processed)


def main(args):
    init_glyph_encoding(xiaohe_glyph_dict, args.mapping)
    with open(glyph_lua_table, "w") as table_out:
        table_out.write("return ")
        table_out.write(dump_lua(glyph_encoding_lua))

    with open(alphabet_lua_table, "w") as table_out:
        table_out.write("return ")
        table_out.write(dump_lua(alphabet_to_chars_lua))

    global output
    output = dict_data_dev if args.dev else "../dicts"

    for file in os.listdir("../cache"):
        if fnmatch.fnmatch(file, "*.yaml"):
            convert_dict(file, args.dev)
    if os.path.exists("../dicts/emoji.dict.yaml"):
        os.rename("../dicts/emoji.dict.yaml", "../emoji.dict.yaml")

def file_path(string):
    if os.path.exists(string):
        return string
    else:
        raise FileNotFoundError(string)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Glim 辅助码码表生成工具。")
    parser.add_argument(
        "--mapping",
        "-m",
        help="单字母映射文件",
        type=file_path,
        default="../assets/glyph_mappings_II.json",
    )
    parser.add_argument(
        "--dev", "-d", help="生成开发相关词典数据.", action=argparse.BooleanOptionalAction
    )
    args = parser.parse_args()
    if args.dev and not os.path.exists(dict_data_dev):
        os.makedirs(dict_data_dev)
    exit(main(args))

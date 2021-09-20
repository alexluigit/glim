#!/usr/bin/env python
import os
import fnmatch
import re
import argparse
import datetime

xiaohe_glyph_dict = "xiaohe-8135.ini"
ziranma_glyph_dict = "zrm-7500.ini"

glyph_encoding = {}


def init_glyph_encoding(glyph_dict):
    f = open(glyph_dict, "r").read().splitlines()
    for line in f:
        pair = line.split("\t")
        glyph = pair[0]
        glyph_code = pair[1]
        glyph_encoding[glyph] = glyph_code

    print(len(glyph_encoding))


def add_glyph_code(item):
    word = [ch for ch in item[0]]
    pinyin = item[1].split(" ")
    enc = lambda x: ":" + glyph_encoding[x] if x in glyph_encoding else ""
    word_pg_encoded = list(map(enc, word))
    item[1] = " ".join([a + b for a, b in zip(pinyin, word_pg_encoded)])
    return "\t".join(item)


def convert_dict(raw_dict):

    dict_name = raw_dict.split(".")[0]
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f'---\nname: {dict_name}\nversion: "{date}"\nsort: by_weight\n...\n'

    dict_input = os.path.join(".", raw_dict)
    dict_output = os.path.join(output, raw_dict)
    f = open(dict_input, "r").read().splitlines()
    f_strip = filter(lambda x: not re.match("[a-z-.# ]|^$", x), f)
    dict_raw = list(map(lambda x: x.split("\t"), f_strip))
    dict_processed = list(map(add_glyph_code, dict_raw))

    with open(dict_output, "w") as dict_out:
        dict_out.write(header)
        dict_out.writelines("%s\n" % line for line in dict_processed)


def main(args):

    # setting glyph encoding
    if args.encode is None:
        init_glyph_encoding(xiaohe_glyph_dict)
    else:
        init_glyph_encoding(
            xiaohe_glyph_dict if args.encode == "xh" else ziranma_glyph_dict
        )

    global output
    output = ".." if args.dest is None else args.dest

    for file in os.listdir("."):
        if fnmatch.fnmatch(file, "*.yaml"):
            convert_dict(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rime词典 全拼 -> 双拼 转换工具。")
    parser.add_argument(
        "encode",
        help="形码格式，可选 xh （小鹤） 或 zrm （自然码）, 默认小鹤。",
        nargs="?",
    )
    parser.add_argument("dest", help="输出路径，默认上级目录。", nargs="?")
    args = parser.parse_args()
    exit(main(args))

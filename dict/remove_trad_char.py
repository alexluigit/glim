#!/usr/bin/env python
import os
import re
import datetime
import opencc

f = open(os.path.join(".", "clover.base.dict.yaml"), "r").read().splitlines()
dict_entries = list(
    map(lambda x: x.split("\t"), filter(lambda x: not re.match("[a-z-.# ]|^$", x), f))
)
dict_char = list(map(lambda x: x[0], dict_entries))
dict_output = os.path.join(".", "glime_base.dict.yaml")


def convert_dict():
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f'---\nname: glime_base\nversion: "{date}"\nsort: by_weight\n...\n'
    converter = opencc.OpenCC("t2s.json")

    for i in range(len(dict_char)):
        char_orig = dict_char[i]
        char_conv = converter.convert(char_orig)
        if not char_orig == char_conv:
            dict_entries[i] = []

    dict_processed = list(
        map(lambda x: "\t".join(x), (filter(lambda x: x, dict_entries)))
    )
    with open(dict_output, "w") as dict_out:
        dict_out.write(header)
        dict_out.writelines("%s\n" % line for line in dict_processed)


convert_dict()

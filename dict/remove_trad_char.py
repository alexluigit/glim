#!/usr/bin/env python
import os
import re
import datetime

dict_input_simp = os.path.join(".", "clover_base_simp.dict.yaml")
f = open(dict_input_simp, "r").read().splitlines()
f_strip = filter(lambda x: not re.match("[a-z-.# ]|^$", x), f)
dict_raw_simp = list(map(lambda x: x.split("\t"), f_strip))
dict_single_simp = list(map(lambda x: x[0], dict_raw_simp))


def remove_duplicate():
    dict_ss_output = dict_single_simp.copy()
    dict_ss_output.reverse()
    dict_ss_query = dict_single_simp.copy()
    dict_ss_query.reverse()
    dic_len = len(dict_single_simp)

    dict_ss_uniq = []
    for i in dict_single_simp:
        if i not in dict_ss_uniq:
            dict_ss_uniq.append(i)

    for char in dict_ss_uniq:
        forward_index = dict_single_simp.index(char)
        backward_index = dict_ss_query.index(char)
        added = forward_index + backward_index + 1
        if not added == dic_len:
            dict_ss_output.remove(char)

    dict_ss_output.reverse()
    return dict_ss_output


def get_item(x):
    for item in dict_raw_simp:
        if item[0] == x:
            return "\t".join(item)


def convert_dict():
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    header = f'---\nname: glime_base\nversion: "{date}"\nsort: by_weight\n...\n'
    dict_processed_single = remove_duplicate()
    dict_processed = list(map(get_item, dict_processed_single))
    dict_output = os.path.join(".", "out.dict.yaml")
    with open(dict_output, "w") as dict_out:
        dict_out.write(header)
        dict_out.writelines("%s\n" % line for line in dict_processed)


convert_dict()

#!/usr/bin/env python

import json
import re
import argparse
import pypinyin
import opencc

pinyin_dict = pypinyin.pinyin_dict.pinyin_dict  # 从 pypinyin 库里得到所有文字及其若干个拼音
initials_set = set(pypinyin.style._constants._INITIALS)  # 声母表
initials_set.add("ng")
fix_dict = json.load(open("../assets/fix_phrases.json", "r"))

class DictGenerator:
    def __init__(self):
        """
        self.phrase_* 所有词的频率信息字典，格式为
            {
                词: [音,频],
                词: [音,频],
                词: [音,频],
                ...
            }
        """
        self.t2s = opencc.OpenCC("t2s")
        self.phrase_main = {}
        self.phrase_heteronyms = {}
        phrase_fix_dict = {}
        with open("pdb.txt", "r") as pdb:
            f_strip = list(
                filter(
                    lambda x: not re.match(".*#|^$", x), pdb.read().splitlines()
                )
            )
            for line in f_strip:
                phrase = line.split("\t")[0]
                phrase_pinyin = [[el] for el in line.split("\t")[1].split(" ")]
                phrase_fix_dict[phrase] = phrase_pinyin
        pypinyin.load_phrases_dict(phrase_fix_dict)

    def fixPinyin(self, pinyin):
        """
        检查拼音，规范化拼音，失败则返回 None
            因为输入法里不允许出现单声母的拼音，
                否则会出现无法输入正常的词组的情况。
            而汉字中比如 “嗯” 的拼音是 n 和 ng
            通常输入法会让 “嗯” 的拼音为 en
        """
        if pinyin in initials_set:
            if pinyin == "n":
                pinyin = "en"
            elif pinyin == "m":
                pinyin = "mu"
            elif pinyin == "ng":
                pinyin = "en"
            else:
                return None  # 不允许出现单声母的拼音
        return pinyin

    def fixPhrases(self):
        """修复一些词语拼写/发音错误，调整频率"""
        for k, v in fix_dict["adjust"].items():
            if not v:
                del self.phrase_main[k]
            elif type(v) == str:
                self.phrase_main[v] = self.phrase_main[k]
                del self.phrase_main[k]
            elif type(v) == int:
                self.phrase_main[k][1] = v
            else:
                self.phrase_main[k][0] = v

    def supplementPinyin(self, phrase):
        """通过 pypinyin 库获取词组拼音"""
        return list(map(self.fixPinyin, pypinyin.lazy_pinyin(phrase)))

    def mergeDict(self, dict_file, weight=1, min_freq=0, dict_name="dict"):
        """
        将 text [词组\t其它信息\t频率] 里储存的词频合并至 self.phrase_*
        weight: 权值，该词库的频率乘以此权值再合并
        min_freq: 最小频率，小于该频率的词会被过滤掉
        """
        text_raw = open(dict_file, "r", encoding="utf-8").read().splitlines()
        text = list(filter(lambda x: not re.match("[a-z-.# ]|^$", x), text_raw))

        fix_dict = json.load(open("../assets/fix_phrases.json", "r"))
        lit_col_dict = fix_dict["lit_col_reading"]
        lit_col_regex = re.compile('|'.join(lit_col_dict.keys()))

        phrase_count = 0
        for line in text:
            v = tuple(map(lambda e: e.strip(), line.split("\t")))
            # 将最后一列视为频率，如果不是则默认为 1
            if not v[-1].isdigit():
                freq_ori = 1
                freq = 1
            else:
                freq_ori = int(v[-1])
                freq = int(float(v[-1]) * weight)
            # 过滤掉词频过小的词
            if freq_ori < min_freq:
                continue
            # 将第一列视为汉字或词组，如果不是则跳过这一行（break）
            word_or_phrase = None
            for c in v[0]:
                if ord(c) not in pinyin_dict:
                    break
            else:
                word_or_phrase = v[0]
            if word_or_phrase is None or len(word_or_phrase) == 0:
                continue
            # 如果是词组，则合并到 self.phrase_main 里
            if len(word_or_phrase) > 1:
                pinyin = None
                if len(v) > 1:
                    if re.match(r"^[a-z]+ [a-z ]+$", v[1]):
                        correct_py = []
                        for py in v[1].split(" "):
                            correct_py.append(self.fixPinyin(py))
                        pinyin = correct_py
                phrase = self.t2s.convert(word_or_phrase)  # 确保词组为简体
                # 处理多音词 | 文白异读 (literary and colloquial readings)
                # 如: 一行 yi hang/xing (多音词) | 流血 liu xue/xie (文白异读)
                if phrase in self.phrase_main:
                    if pinyin == self.phrase_main[phrase][0]:
                        self.phrase_main[phrase][1] += freq
                    elif phrase in self.phrase_heteronyms:
                        self.phrase_heteronyms[phrase][1] += freq
                    elif pinyin:
                        self.phrase_heteronyms[phrase] = [pinyin, freq]
                else:
                    if re.search(lit_col_regex, phrase):
                        pinyin = pinyin or self.supplementPinyin(phrase)
                        phrase_literary = pinyin.copy()
                        phrase_colloquial = pinyin.copy()
                        for match in re.finditer(lit_col_regex, phrase):
                            word_literary = lit_col_dict[match.group()][0]
                            word_colloquial = lit_col_dict[match.group()][1]
                            phrase_literary[match.start()] = word_literary
                            phrase_colloquial[match.start()] = word_colloquial
                        self.phrase_main[phrase] = [phrase_literary, freq]
                        self.phrase_heteronyms[phrase] = [phrase_colloquial, freq]
                    else:
                        self.phrase_main[phrase] = [pinyin, freq]
                phrase_count += 1
        print("成功合并 %s %s 个词组。" % (dict_name, phrase_count))

    def getPhraseList(self, generate=True):
        """生成词组的 rime 字典 list"""
        if generate:
            for k, v in self.phrase_main.items():
                # 若 pdb.txt 无此 phrase, 则通过 pypinyin 库获取到词组的拼音
                self.phrase_main[k] = [ v[0] or self.supplementPinyin(k), v[1]]
            self.dumpJson()
        else:
            dict_json = json.load(open("glim_dict.json", "r"))
            self.phrase_main = dict_json["main"]
            self.phrase_heteronyms = dict_json["heteronyms"]
        self.fixPhrases()
        phrase_main_list = [(k, v[0], v[1]) for k, v in self.phrase_main.items()]
        phrase_sub_list = [(k, v[0], v[1]) for k, v in self.phrase_heteronyms.items()]
        phrase_add_list = [(k, v[0], v[1]) for k, v in fix_dict["add"].items()]
        phrase_list = phrase_main_list + phrase_sub_list + phrase_add_list
        # 按频率倒序排序
        phrase_list.sort(key=lambda w: w[2], reverse=True)
        return phrase_list

    def dumpJson(self):
        with open("glim_dict.json", "w") as dict_json_out:
            dict_json = {"main": self.phrase_main, "heteronyms": self.phrase_heteronyms}
            json.dump(dict_json, dict_json_out)


def main(args):
    generator = DictGenerator()
    if args.gen:
        generator.mergeDict("main.dict.yaml", args.weight, args.minfreq, "华宇系统词库")
        generator.mergeDict("pinyin_simp.dict.yaml", 1, 0, "袖珍简化字拼音")
        generator.mergeDict("essay.txt", 1, 0, "八股文")
        generator.mergeDict("pdb.txt", 1, 0, "phrase-pinyin-data")
    phrase_list = generator.getPhraseList(args.gen)
    with open("glim_phrase.dict.yaml", "w") as phrase_out:
        header = '---\nname: glim_phrase\nversion: "1.0.0"\nsort: by_weight\n...\n'
        phrase_out.write(header)
        phrase_text = ""
        for ph in phrase_list:
            phrase_text += ph[0] + "\t" + " ".join(ph[1]) + "\t" + str(ph[2]) + "\n"
        phrase_out.write(phrase_text)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Glim raw pinyin dict generator.")
    parser.add_argument("--minfreq", type=int, default=0)
    parser.add_argument("--weight", type=int, default=1)
    parser.add_argument("--gen", default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    main(args)

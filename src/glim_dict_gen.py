#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import jieba
import pypinyin
import opencc
import re
import argparse
import os
import sys

# 从 pypinyin 库里得到所有文字及其若干个拼音
pinyin_dict = pypinyin.pinyin_dict.pinyin_dict
phrase_fix_dict = {}
replace_symbol_to_no_symbol = pypinyin.style._utils.replace_symbol_to_no_symbol
initials_set = set(pypinyin.style._constants._INITIALS)  # 声母表
initials_set.add("ng")

# 修复一些多音字错误
pypinyin.load_phrases_dict(
    {
        "还珠格格": [["huán"], ["zhū"], ["gé"], ["gé"]],
        "睡不着": [["shuì"], ["bù"], ["zháo"]],
        "睡不着觉": [["shuì"], ["bù"], ["zháo"], ["jiào"]],
        "干这一行": [["gàn"], ["zhe"], ["yì"], ["háng"]],
        "十目一行": [["shí"], ["mù"], ["yī"], ["háng"]],
    }
)

with open("../cache/pdb.txt", "r") as pdb:
    f_strip = list(
        filter(lambda x: not re.match("[a-z-.# ]|^$", x), pdb.read().splitlines())
    )
    for line in f_strip:
        phrase = line.split(": ")[0]
        phrase_pinyin = [[el] for el in line.split(": ")[1].split(" ")]
        phrase_fix_dict[phrase] = phrase_pinyin

pypinyin.load_phrases_dict(phrase_fix_dict)


class DictGenerator:
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

    def __init__(self):
        """
        初始化函数，定义了字词频率所需的基本数据结构
        self.word_dict 和 self.phrase_r
        """

        """
            从 jieba 库里的 pinyin_dict 经过 replace_symbol_to_no_symbol 转换得到：
                self.word_pinyin_s 所有字的字音字典，格式为
                    {
                        unicode编码: [音1, 音2, ...],
                        unicode编码: [音1, 音2, ...],
                        unicode编码: [音1, 音2, ...],
                        ...
                    }
        """
        jieba.dt.initialize()
        self.t2s = opencc.OpenCC("t2s.json")

        def symbol2fixPinyin(pinyin):
            pinyin = replace_symbol_to_no_symbol(pinyin)
            fixed_pinyin = self.fixPinyin(pinyin)
            if fixed_pinyin is None or fixed_pinyin in initials_set:
                print(pinyin)
                assert False  # 库的拼音不规范，需要手动规范化
            return fixed_pinyin

        self.word_pinyin_s = {
            i: list(map(symbol2fixPinyin, pinyin_dict[i].split(",")))
            for i in pinyin_dict
        }

        """
            从 jieba 库里的 FREQ 得到所有字音的频率，转换得到：
                self.word_dict 所有字的字音频率字典，格式为
                    {
                        (字,音): 频,
                        (字,音): 频,
                        (字,音): 频,
                        ...
                    }
        """
        self.word_dict = {}
        for i in self.word_pinyin_s:
            word = chr(i)
            freq = jieba.dt.FREQ[word] if word in jieba.dt.FREQ else 1

            # 将多音字的第一个音设为 FREQ 里的频率
            self.word_dict[(word, self.word_pinyin_s[i][0])] = freq

            for pinyin in self.word_pinyin_s[i][1:]:
                # 将其它音的频率设为 1
                if (word, pinyin) not in self.word_dict:
                    self.word_dict[(word, pinyin)] = 1

        """
            self.phrase_r 所有词的频率信息字典，格式为
                {
                    词: [音,频] ,
                    词: [音,频],
                    词: [音,频],
                    ...
                }
        """
        self.phrase_r = {}
        self.phrase_heteronyms = {}
        self.phrase_fix = {
            "落下": [["luo", "xia"],	100000 ],
            "差事": [["cha", "shi"],	10000 ],
            "差事儿": [["cha", "shi" "er"],	10000 ]
        }

    def mergeDict(
        self, text, weight=1, min_freq=0, callbackCount=sys.maxsize, callbackFunc=None
    ):
        """
        将 text 里储存的词频、字频内容合并到数据结构中
        text: 原始文本，会自动过滤掉拼音和其它字符
            原始文本的每一行格式为：
                字或词组\t其它信息\t频率
        weight: 权值，该词库的频率乘以此权值再合并
        min_freq: 最小频率，小于该频率的词会被过滤掉
        返回值: 成功合并的数目元组，格式为 (word_count, parse_count)
        """

        word_count = 0
        parse_count = 0
        skip_count = 0

        text_s = text.split("\n")
        for line in text_s:
            v = tuple(map(lambda e: e.strip(), line.split("\t")))

            # 将最后一列视为频率，如果不是则默认为 1
            if not v[-1].isdigit():
                # freq = weight  # 1 * weight
                freq_ori = 1
                freq = 1
            else:
                # freq = int(v[-1]) * weight
                freq_ori = int(v[-1])
                freq = int(float(v[-1]) * weight)

            # 过滤掉词频过小的词
            if freq_ori < min_freq:
                skip_count += 1
                count = word_count + parse_count + skip_count
                if count % callbackCount == 0:
                    callbackFunc(count, len(text_s))
                continue

            # 将第一列视为汉字或词组，如果不是则跳过这一行（break）
            word = None
            for c in v[0]:
                if ord(c) not in self.word_pinyin_s:
                    break
            else:
                word = v[0]
            if word is None or len(word) == 0:
                continue

            # 当 word 为单字时，将第二列视为拼音，如果出错则设为该字的第一个拼音
            pinyin = None
            if len(word) == 1:
                if len(v) > 1:
                    if v[1].isalpha():
                        pinyin = self.fixPinyin(v[1])
                if pinyin is None:
                    pinyin = self.word_pinyin_s[ord(word)][0]

            # 如果是单字，则合并到 self.word_dict 里
            if len(word) == 1:
                word = self.t2s.convert(word)  # 确保字为简体
                key = (word, pinyin)
                if key in self.word_dict:
                    self.word_dict[key] += freq
                else:
                    sys.stderr.write("新的字音： %s\t%s\n" % key)
                word_count += 1

            # 如果是词组，则合并到 self.phrase_r 里
            else:
                pinyin = None
                if len(v) > 1:
                    if re.match(r"^[a-z ]+$", v[1]):
                        correct_py = []
                        for py in v[1].split(" "):
                            correct_py.append(self.fixPinyin(py))
                        pinyin = correct_py

                word = self.t2s.convert(word)  # 确保词组为简体
                # 处理多音词 如: 一行 yi hang/xing
                if word in self.phrase_r:
                    if pinyin == self.phrase_r[word][0]:
                       self.phrase_r[word][1] += freq
                    elif word in self.phrase_heteronyms:
                       self.phrase_heteronyms[word][1] += freq
                    elif pinyin:
                       self.phrase_heteronyms[word] = [pinyin, freq]
                    # self.phrase_r[word][1] += freq
                else:
                    self.phrase_r[word] = [pinyin, freq]
                parse_count += 1

            if callbackFunc is not None:
                count = word_count + parse_count + skip_count
                if count % callbackCount == 0:
                    callbackFunc(count, len(text_s))

        return (word_count, parse_count)

    def getWordDictText(self):
        """
        生成单字的 rime 字典文本
        """
        # 按频率倒序排序
        word_list = [(key[0], key[1], self.word_dict[key]) for key in self.word_dict]
        word_list.sort(key=lambda w: w[2], reverse=True)

        # 生成文本
        text_dict = ""
        for word_st in word_list:
            text_dict += word_st[0] + "\t" + word_st[1] + "\t" + str(word_st[2]) + "\n"
        return text_dict

    def getParseDictText(self, callbackCount=sys.maxsize, callbackFunc=None):
        """
        生成词组的 rime 字典文本
        由于词典量较大，所以需要显示转换进度
        callbackCount 为每过几个词调用一次 callbackFunc
        callbackFunc 是回调函数，自定义如何处理进度
            格式为 callbackFunc(count, total_count)
                count 为当前已处理的个数
                total_count 为总共数量
        """
        # 按频率倒序排序
        phrase_main_list = [
            (phrase, self.phrase_r[phrase][0], self.phrase_r[phrase][1])
            for phrase in self.phrase_r
        ]
        phrase_heteronyms_list = [
            (phrase, self.phrase_heteronyms[phrase][0], self.phrase_heteronyms[phrase][1])
            for phrase in self.phrase_heteronyms
        ]
        phrase_fix_list = [
            (phrase, self.phrase_fix[phrase][0], self.phrase_fix[phrase][1])
            for phrase in self.phrase_fix
        ]
        phrase_list = phrase_main_list + phrase_heteronyms_list + phrase_fix_list
        phrase_list.sort(key=lambda w: w[2], reverse=True)

        # 生成文本
        count = 0
        text_phrase = ""
        for phrase_st in phrase_list:
            # 若 large_pinyin.txt 无此 phrase, 则通过 pypinyin 库获取到词组的拼音
            phrase_pinyin = phrase_st[1]
            if phrase_pinyin is None:
                phrase_pinyin = map(self.fixPinyin, pypinyin.lazy_pinyin(phrase_st[0]))
            text_phrase += (
                phrase_st[0]
                + "\t"
                + " ".join(phrase_pinyin)
                + "\t"
                + str(phrase_st[2])
                + "\n"
            )
            count += 1
            if callbackFunc is not None:
                if count % callbackCount == 0:
                    callbackFunc(count, len(phrase_list))
        return text_phrase


def main(args):
    generator = DictGenerator()

    class PrintProcess:
        def __init__(self, msg):
            self.msg = msg

        def process(self, count, total):
            print(self.msg % (count, total))

    # 合并华宇系统词库
    text = open("sys.dict.yaml", "r", encoding="utf-8").read()
    r = generator.mergeDict(
        text,
        # args.weight,
        # args.minfreq,
        1,
        0,
        100000,
        PrintProcess("正在合并华宇系统词库 (%s/%s)").process,
    )
    print("成功合并华宇中文词库 %s 个汉字， %s 个词组。" % r)

    # 合并袖珍简化字拼音的词库
    text = (
        open("pinyin_simp.dict.yaml", "r", encoding="utf-8").read().replace("罗嗦", "啰嗦")
    )
    r = generator.mergeDict(
        text, 1, 0, 100000, PrintProcess("正在合并袖珍简化字拼音的词库 (%s/%s)").process
    )
    print("成功合并袖珍简化字拼音 %s 个汉字， %s 个词组。" % r)

    # 合并 THUOCL 词库
    text = open("THUOCL.dict.yaml", "r", encoding="utf-8").read()
    r = generator.mergeDict(text, 0.01, 0, 100000, PrintProcess("正在合并 THUOCL (%s/%s)").process)
    print("成功合并 THUOCL %s 个汉字， %s 个词组。" % r)

    # 合并 rime 自带的八股文
    text = open("essay.txt", "r", encoding="utf-8").read()
    r = generator.mergeDict(text, 1, 0, 100000, PrintProcess("正在合并八股文 (%s/%s)").process)
    print("成功合并八股文 %s 个汉字， %s 个词组。" % r)

    # 合并 phrase-pinyin-data 的词库
    text = open("pdb.txt", "r", encoding="utf-8").read().replace(": ", "\t")
    r = generator.mergeDict(
        text,
        1,
        0,
        100000,
        PrintProcess("正在合并 phrase-pinyin-data 的词库 (%s/%s)").process,
    )
    print("成功合并 phrase-pinyin-data %s 个汉字， %s 个词组。" % r)

    # word_dict_name = "glim_base"
    parse_dict_name = "glim_phrase"

    # word_dict_text = generator.getWordDictText()

    parse_dict_text = generator.getParseDictText(
        10000, PrintProcess("正在取得每个词组的拼音 (%s/%s)").process
    )

    with open(parse_dict_name + ".dict.yaml", "w") as phrase_out:
        phrase_out.write("---\nname: glim_phrase\nversion: \"1.0.0\"\nsort: by_weight\n...\n")
        phrase_out.write(parse_dict_text)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Glim raw pinyin dict generator.")
    parser.add_argument(
        "--minfreq",
        "-m",
        help="Specify the minimum frequency, "
        + "phrases that are less than this frequency will be filtered out",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--weight",
        "-w",
        help="Specify the weight for vanilla rime dict, will multiple this value with word freq",
        type=int,
        default=0.005,
    )
    args = parser.parse_args()
    main(args)

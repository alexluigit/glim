#!/usr/bin/env python
import argparse
import struct
import os


class FormatError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class scel:
    def __init__(self):
        self.title = ""
        self.category = ""
        self.description = ""
        self.samples = []
        self.py_map = {}
        self.word_list = []
        self.del_words = []

    def loads(self, bin_data):
        """
        bin_data 是包含 scel 格式的 bytes 类型二进制数据
        返回值： 返回读取到的数据字典
        """

        def read_str(offset, length=-1):
            if length >= 0:
                str_raw = bin_data[offset : offset + length]
            else:
                str_raw = bin_data[offset : bin_data.find(b"\0\0", offset)]
            if len(str_raw) % 2 == 1:
                str_raw += b"\0"
            return str_raw.decode("utf-16-le")

        def read_uint16(offset):
            return struct.unpack("H", bin_data[offset : offset + 2])[0]

        def read_uint32(offset):
            return struct.unpack("I", bin_data[offset : offset + 4])[0]

        # 检验头部
        #   0x0 ~ 0x3
        magic = read_uint32(0)
        if magic != 0x1540:
            raise FormatError("头部校验错误，可能不是搜狗词库文件！")

        # scel格式类型，标志着汉字的偏移量
        #   0x4
        scel_type = bin_data[4]
        if scel_type == 0x44:
            hz_offset = 0x2628
        elif scel_type == 0x45:
            hz_offset = 0x26C4
        else:
            raise FormatError("未知的搜狗词库格式，可能为新版格式！")

        #   0x5 ~ 0x11F 目前未知

        # 读取到词组个数
        record_count = read_uint32(0x120)
        total_words = read_uint32(0x124)

        # 两个未知的值
        int_unknow1 = read_uint32(0x128)
        int_unknow2 = read_uint32(0x12C)

        # 读取到标题、目录、描述、样例
        #   0x130 ~ 0x1540
        self.title = read_str(0x130)
        self.category = read_str(0x338)
        self.description = read_str(0x540)
        str_samples = read_str(0xD40)
        # self.samples = list(map(lambda s:s.split('\u3000'), str_samples.split('\r ')))
        # self.samples[-1][1] = self.samples[-1][1].rstrip(' ')
        self.samples = str_samples

        # 读取到拼音列表
        #   0x1540 ~ 0x1540 + ?
        py_count = read_uint32(0x1540)
        offset = 0x1544
        for j in range(py_count):
            py_idx = read_uint16(offset)
            offset += 2
            py_len = read_uint16(offset)
            offset += 2
            py_str = read_str(offset, py_len)
            offset += py_len

            self.py_map[py_idx] = py_str

        # 读取词语列表
        #   hz_offset ~ ?
        offset = hz_offset
        for j in range(record_count):
            word_count = read_uint16(offset)
            offset += 2
            py_idx_count = int(read_uint16(offset) / 2)
            offset += 2

            py_set = []
            for i in range(py_idx_count):
                py_idx = read_uint16(offset)
                offset += 2
                py_set.append(py_idx)

            for i in range(word_count):
                word_len = read_uint16(offset)
                offset += 2
                word_str = read_str(offset, word_len)
                offset += word_len

                info_len = read_uint16(offset)
                offset += 2
                seq = read_uint16(offset)
                flag_unknow = read_uint16(offset + 2)
                info_unknow = []
                for i in range(3):
                    info_unknow.append(read_uint16(offset + 4 + i * 2))
                if info_unknow != [0, 0, 0]:
                    print("发现新的扩展信息，请将该词库上报以便调试。", info_unknow)
                offset += info_len

                self.word_list.append([word_str, py_set, seq])

        # 读取的词语按顺序排序
        self.word_list.sort(key=lambda e: e[2])

        # 读取被删除的词语
        if bin_data[offset : offset + 12] == "DELTBL".encode("utf-16-le"):
            offset += 12
            del_count = read_uint16(offset)
            offset += 2
            for i in range(del_count):
                word_len = read_uint16(offset) * 2
                offset += 2
                word_str = read_str(offset, word_len)
                offset += word_len
                self.del_words.append(word_str)

    def load(self, file_path):
        data = open(file_path, "rb").read()
        return self.loads(data)


# def getInternetPopularNewWords():
#     """
#     从搜狗输入法细胞词库官网下载网络流行新词【官方推荐】
#     网址是 https://pinyin.sogou.com/dict/detail/index/4
#     下载地址为 https://pinyin.sogou.com/d/dict/download_cell.php?id=4&name=%E7%BD%91%E7%BB%9C%E6%B5%81%E8%A1%8C%E6%96%B0%E8%AF%8D%E3%80%90%E5%AE%98%E6%96%B9%E6%8E%A8%E8%8D%90%E3%80%91&f=detail
#     返回： scel文件的二进制 bytes
#     """
#     import requests

#     url = "https://pinyin.sogou.com/d/dict/download_cell.php"
#     params = {
#         "id": 4,
#         "name": "网络流行新词【官方推荐】",
#         "f": "detail",
#     }
#     r = requests.get(url, params=params)
#     return r.content


# def main(args):
#     s = scel()

#     # 读取 scel
#     if args.file is None:
#         s.loads(getInternetPopularNewWords())
#     else:
#         s.load(args.file)

#     # 生成 text
#     text = ""
#     for w in s.word_list:
#         text += (
#             w[0]
#             + "\t"
#             + " ".join(map(lambda key: s.py_map[key], w[1]))
#             + "\t"
#             + str(1)
#             + "\n"
#         )

#     # 输出
#     if args.dest is None:
#         fp = sys.stdout
#     else:
#         fp = open(args.dest + ".dict.yaml", "w")
#         date = datetime.datetime.now().strftime("%Y-%m-%d")
#         header = f'---\nname: {args.dest}\nversion: "{date}"\nsort: by_weight\n...\n'
#         fp.write(header)
#     fp.write(text)


def single_file(args):
    input_path = args.file
    output_path = args.dest
    # 转换scel为txt
    GTable = scel2txt(input_path)
    # 保存结果
    with open(output_path, "w", encoding="utf8") as f:
        f.writelines([py + " " + word + "\n" for count, py, word in GTable])


def batch_file(input_dir, output_dir):
    # 创建保存路径
    try:
        os.mkdir(output_dir)
    except Exception as e:
        print(e)
    # 遍历文件夹下的文件
    for parent, dirnames, filenames in os.walk(input_dir):
        new_parent = output_dir + parent.replace(input_dir, "")
        try:
            os.mkdir(new_parent)
        except Exception as e:
            print(e)
        # 批量处理文件
        for filename in filenames:
            if os.path.exists(
                os.path.join(new_parent, filename.replace(".scel", ".txt"))
            ):
                print(filename + ">>>>>>文件已存在")
            else:
                try:
                    s = scel()
                    s.load(os.path.join(parent, filename))
                    text = ""
                    for w in s.word_list:
                        text += (
                            w[0]
                            + "\t"
                            + " ".join(map(lambda key: s.py_map[key], w[1]))
                            + "\t"
                            + str(1)
                            + "\n"
                        )

                    # GTable = scel2txt(os.path.join(parent, filename))
                    with open(
                        os.path.join(
                            new_parent, filename.replace(".scel", ".dict.yaml")
                        ),
                        "w",
                        encoding="utf8",
                    ) as f:
                        f.write(text)
                        # f.writelines(
                        #     [py + " " + word + "\n" for count, py, word in GTable]
                        # )  # 此处可选择输出的是词频、拼音或是文字
                        print(filename + ">>>>>> .dict.yaml 转换成功")
                except Exception as e:
                    print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="搜狗细胞词库（.scel）转换工具，" + '输出格式为 "词语\\t拼音\\t优先级"'
    )
    parser.add_argument("dest", help="输出的 rime 词典名，将生成「词典名.dict.yaml」文件", nargs="?")
    parser.add_argument(
        "file",
        help="搜狗细胞词库文件，格式为 .scel " + "如果不指定则会自动从官网获取“网络流行新词【官方推荐】.scel”",
        nargs="?",
    )
    args = parser.parse_args()
    exit(single_file(args))

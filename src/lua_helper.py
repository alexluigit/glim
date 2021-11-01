import re

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


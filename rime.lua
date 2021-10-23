TAB_CARET = 0
CHARSET_TABLE = require("charset_table")
local config = Schema("glim").config
local onechar = config:get_bool("translator/onechar")
local fixed = config:get_bool("translator/fixed_single_ch")
local diff = config:get_bool("translator/ensure_different_onechar")
local preprocess_charset = require("alphabet_table").preprocess_charset_table
preprocess_charset(CHARSET_TABLE, (onechar and fixed and diff))
editor_processor = require("editor")
date_translator = require("date")
time_translator = require("time")
abbrev_segmentor = require("abbrev")
glyph_filter = require("glyph")
charset_filter = require("charset")
onechar_filter = require("onechar")

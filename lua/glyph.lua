--[[
glyph_filter: 候选项重排序, 匹配形码
--]]

local REVERSE_LOOKUP = 1
local AUTO_GLYPH_WORD = 2
local AUTO_GLYPH_PHRASE = 3
local input_helper = require("helpers.input")
local cand_helper = require("helpers.candidate")

local __filter_char = function (cand, env, ch, gl_input, glyph_lvl, matched, rest)
  local ch1 = env.glyph_table[ch]["ch1"]
  local ch2 = env.glyph_table[ch]["ch2"]
  local gl1 = env.glyph_table[ch]["gl1"]
  local gl2 = env.glyph_table[ch]["gl2"]
  local auto = env.glyph_table[ch]["auto"]
  local glyph_filter_str = ch1 .. ch2
  local pop_len = (glyph_lvl > REVERSE_LOOKUP and gl_input:len() or gl_input:len() + 1)
  if string.match(glyph_filter_str, '^' .. gl_input) then
    cand.comment = cand_helper.get_hint(env.gl_hint_level, ch1 .. ch2, gl1 .. gl2)
    cand.type = "glyph_" .. tostring(pop_len)
    if glyph_lvl == REVERSE_LOOKUP or auto then
      table.insert(matched, cand)
    end
  else
    table.insert(rest, cand)
  end
end

local __filter_phrase = function
    (cand, env, tail_ch, head_ch, gl_input, glyph_lvl, ph_top, matched, rest)
  local t_ch1 = env.glyph_table[tail_ch]["ch1"]
  local t_gl1 = env.glyph_table[tail_ch]["gl1"]
  local t_auto = env.glyph_table[head_ch]["auto"]
  local h_ch1 = env.glyph_table[head_ch]["ch1"]
  local h_gl1 = env.glyph_table[head_ch]["gl1"]
  local h_auto = env.glyph_table[head_ch]["auto"]
  local glyph_filter_str = h_ch1 .. t_ch1
  local glyph_gl_str = h_gl1 .. t_gl1
  local text = cand.text
  if ph_top == nil and utf8.len(text) == glyph_lvl then ph_top = cand end
  if glyph_lvl == REVERSE_LOOKUP and string.match(glyph_filter_str, '^' .. gl_input) then
    cand.comment = cand_helper.get_hint(env.gl_hint_level, glyph_filter_str, glyph_gl_str)
    cand.type = "glyph_" .. tostring(gl_input:len() + 1)
    yield(cand)
  elseif utf8.len(text) < glyph_lvl
    and string.match(glyph_filter_str, '^' .. gl_input)
    and t_auto and h_auto then
    cand.comment = cand_helper.get_hint(env.gl_hint_level, glyph_filter_str, glyph_gl_str)
    cand.type = "glyph_" .. tostring(gl_input:len())
    table.insert(matched, cand)
  elseif cand.text ~= (ph_top and ph_top.text) then
    table.insert(rest, cand)
  end
  return ph_top
end

local __display_matches = function (env, ph_top, gl_input, matched, rest, glyph_lvl)
  if glyph_lvl == REVERSE_LOOKUP then
    for i, cand in ipairs(matched) do yield(cand) end
    return
  end
  local ctx = env.engine.context
  local gl_len = gl_input:len()
  local caret = gl_len + 2 * (glyph_lvl - 1)
  local recorded = false
  local history = input_helper.get_history(ctx, caret - 1)
  local valid_match = {}
  local ph_text = ph_top and ph_top.text
  local top_qual = 0
  local TOP, BOTTOM = 1, 2
  local dup_table = env.dup_table
  for i, cand in ipairs(matched) do
    if input_helper.validate(history, cand.text) then
      top_qual = math.max(top_qual, cand.quality)
      table.insert(valid_match, cand)
    end
  end
  local place_phrase = cand_helper.place_phrase(
    ph_top, valid_match, env.gl_fixed, top_qual, ctx.input, dup_table)
  if place_phrase == TOP then
    yield(ph_top)
    recorded = input_helper.set_history(ctx, caret, ph_text)
  end
  if (#valid_match > 0) and (not recorded) then
    recorded = input_helper.set_history(ctx, caret, valid_match[1].text)
  end
  if glyph_lvl == AUTO_GLYPH_WORD and gl_len == 1 then
    for i, cand in ipairs(valid_match) do
      code = ctx.input:sub(-3) .. env.glyph_table[cand.text]["ch2"]
      if i > 1 and (not dup_table[code]) then
        table.remove(valid_match, i)
        table.insert(rest, cand)
      end
    end
  end
  for i, cand in ipairs(valid_match) do yield(cand) end
  if place_phrase == BOTTOM then yield(ph_top) end
  for i, cand in ipairs(rest) do yield(cand) end
end

local _filter_cands = function (cands, env, gl_input, glyph_lvl)
  local ph_top = nil
  local matched = {}
  local rest = {}
  local words_text = {}
  for cand in cands:iter() do
    cand_helper.append_valid_word(cand, words_text)
    local tail_ch, head_ch, valid_words = cand_helper.get_words(cand)
    if not valid_words then table.insert(rest, cand); goto skip_to_next end
    if head_ch then
      ph_top = __filter_phrase(
        cand, env, tail_ch, head_ch, gl_input, glyph_lvl, ph_top, matched, rest)
    elseif glyph_lvl <= 2 then
      __filter_char(cand, env, tail_ch, gl_input, glyph_lvl, matched, rest)
    else
      table.insert(rest, cand)
    end
    ::skip_to_next::
  end
  cand_helper.sort_by_heteronym(matched, words_text, glyph_lvl)
  __display_matches(env, ph_top, gl_input, matched, rest, glyph_lvl)
end

local _match_input = function (caret, input, auto_lvl, lvl)
  local seg_len = caret - TAB_CARET
  if auto_lvl > lvl - 1 and input:match('^[a-z ;]+$')
    and seg_len > 2 * lvl and seg_len <= 2 * (1 + lvl) then
    return true
  end
end

local filter = function (cands, env)
  local ctx = env.engine.context
  local input = ctx.input
  local caret = ctx.caret_pos
  local auto_lvl = env.gl_auto_level
  local gl_input = input:sub(caret - (caret % 2 == 1 and 0 or 1), caret)
  if string.match(input, ':%a?') then
    gl_input = string.gsub(input, ".*:", "")
    _filter_cands(cands, env, gl_input, REVERSE_LOOKUP)
  elseif _match_input(caret, input, auto_lvl, 1) then
    _filter_cands(cands, env, gl_input, AUTO_GLYPH_WORD)
  elseif _match_input(caret, input, auto_lvl, 2) then
    _filter_cands(cands, env, gl_input, AUTO_GLYPH_PHRASE)
  else
    for cand in cands:iter() do yield(cand) end
  end
end

local init = function (env)
  local config = env.engine.schema.config
  local layout = config:get_string("speller/layout")
  env.gl_hint_level = config:get_int("translator/glyph_hint_level")
  env.gl_fixed = config:get_bool("translator/fixed_single_ch")
  if layout == "full" then
    env.gl_auto_level = 0
  else
    env.gl_auto_level = config:get_int("translator/glyph_auto_level")
    env.dup_table = require("../tables.duplicate/" .. layout)
  end
  env.glyph_table = require("tables.glyph_table")(layout)
end

return { init = init, func = filter }

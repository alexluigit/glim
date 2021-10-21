--[[
glyph_filter: 候选项重排序, 匹配形码
--]]

local __cand_hint = function (hint_lvl, py, gl)
  if hint_lvl == 1 then
    return ":" .. py
  elseif hint_lvl == 2 then
    return ":" .. py .. " " .. gl
  end
end

local __filter_char = function (cand, env, ch, glyph_all, keep_phrase, matched)
  local py1 = env.glyph_table[ch]["first_py"]
  local py2 = env.glyph_table[ch]["last_py"]
  local gl1 = env.glyph_table[ch]["first_gl"]
  local gl2 = env.glyph_table[ch]["last_gl"]
  local lvl = env.glyph_table[ch]["level"]
  local glyph_filter_str = py1 .. py2
  local pop_len = (keep_phrase > 1 and glyph_all:len() or glyph_all:len() + 1)
  if string.match(glyph_filter_str, '^' .. glyph_all) then
    cand.comment = __cand_hint(env.gl_hint_level, py1 .. py2, gl1 .. gl2)
    cand.type = "glyph_" .. tostring(pop_len)
    if keep_phrase == 1 or lvl < 3 then
      table.insert(matched, cand)
    end
  end
end

local __filter_phrase = function
    (cand, env, tail_ch, head_ch, glyph_all, keep_phrase, ph_top, matched, rest)
  local t_py1 = env.glyph_table[tail_ch]["first_py"]
  local t_py2 = env.glyph_table[tail_ch]["last_py"]
  local t_gl1 = env.glyph_table[tail_ch]["first_gl"]
  local t_gl2 = env.glyph_table[tail_ch]["last_gl"]
  local t_lvl = env.glyph_table[head_ch]["level"]
  local h_py1 = env.glyph_table[head_ch]["first_py"]
  local h_py2 = env.glyph_table[head_ch]["last_py"]
  local h_gl1 = env.glyph_table[head_ch]["first_gl"]
  local h_gl2 = env.glyph_table[head_ch]["last_gl"]
  local h_lvl = env.glyph_table[head_ch]["level"]
  local glyph_filter_str = h_py1 .. t_py1 .. t_py2 .. h_py2
  local glyph_gl_str = h_gl1 .. t_gl1 .. t_gl2 .. h_gl2
  local text = cand.text
  if ph_top == nil and utf8.len(text) == keep_phrase then ph_top = cand end
  if keep_phrase == 1 and string.match(glyph_filter_str, '^' .. glyph_all) then
    cand.comment = __cand_hint(env.gl_hint_level, glyph_filter_str, glyph_gl_str)
    cand.type = "glyph_" .. tostring(glyph_all:len() + 1)
    yield(cand)
  elseif utf8.len(text) < keep_phrase
    and string.match(glyph_filter_str, '^' .. glyph_all)
    and t_lvl < 3 and h_lvl < 3 then
    cand.comment = __cand_hint(env.gl_hint_level, h_py1 .. t_py1, h_gl1 .. t_gl1)
    cand.type = "glyph_" .. tostring(glyph_all:len())
    table.insert(matched, cand)
  elseif cand.text ~= (ph_top and ph_top.text) then
    table.insert(rest, cand)
  end
  return ph_top
end

local __get_words = function (cand, env)
  local text = cand.text
  local ch_idxs = {}
  for i in utf8.codes(text) do table.insert(ch_idxs, i) end
  local tail_ch = utf8.char(utf8.codepoint(text, ch_idxs[#ch_idxs]))
  local head_ch = nil
  if #ch_idxs > 1 then head_ch = utf8.char(utf8.codepoint(text, ch_idxs[#ch_idxs - 1])) end
  local valid_tail_word = env.glyph_table[tail_ch]
  local valid_head_word = (not head_ch) or env.glyph_table[head_ch]
  return tail_ch, head_ch, (valid_tail_word and valid_head_word)
end

local __sort_matches = function (env, ph_top, glyph_all, matched, rest, keep_phrase)
  if ph_top then
    if glyph_all:len() == 1 then
      for i, cand in ipairs(matched) do yield(cand) end
      yield(ph_top)
    else
      local ontop = ph_top.quality >= env.gl_min_freq
      -- print("freqe: ", string.format("%.5f", env.gl_min_freq))
      -- print("first: ", string.format("%.5f", ph_top.quality), ph_top.text)
      if ontop then
        yield(ph_top)
        for i, cand in ipairs(matched) do yield(cand) end
      else
        for i, cand in ipairs(matched) do yield(cand) end
        yield(ph_top)
      end
    end
  else
    for i, cand in ipairs(matched) do yield(cand) end
  end
  if keep_phrase ~= 1 then
    for i, cand in ipairs(rest) do yield(cand) end
  end
end

local _filter_cands = function (cands, env, glyph_all, keep_phrase)
  local ph_top = nil
  local matched = {}
  local rest = {}
  for cand in cands:iter() do
    local tail_ch, head_ch, valid_words = __get_words(cand, env)
    if not valid_words then table.insert(rest, cand); goto skip_to_next end
    if head_ch then
      ph_top = __filter_phrase(
        cand, env, tail_ch, head_ch, glyph_all, keep_phrase, ph_top, matched, rest)
    elseif keep_phrase <= 2 then
      __filter_char(cand, env, tail_ch, glyph_all, keep_phrase, matched)
    else
      table.insert(rest, cand)
    end
    ::skip_to_next::
  end
  __sort_matches(env, ph_top, glyph_all, matched, rest, keep_phrase)
end

local _match_input = function (caret, input, auto_lvl, lvl)
  if auto_lvl > lvl - 1 and string.match(input, '^[a-z ;]+$')
    and caret - TAB_CARET > 2 * lvl
    and caret - TAB_CARET <= 2 * (1 + lvl) then
    return true
  end
end

local filter = function (cands, env)
  local ctx = env.engine.context
  local input = ctx.input
  local caret = ctx.caret_pos
  local auto_lvl = env.gl_auto_level
  local glyph_all = input:sub(caret - (caret % 2 == 1 and 0 or 1), caret)
  if string.match(input, ':%a?') then
    glyph_all = string.gsub(input, ".*:", "")
    _filter_cands(cands, env, glyph_all, 1)
  elseif _match_input(caret, input, auto_lvl, 1) then
    _filter_cands(cands, env, glyph_all, 2)
  elseif _match_input(caret, input, auto_lvl, 2) then
    _filter_cands(cands, env, glyph_all, 3)
  else
    for cand in cands:iter() do yield(cand) end
  end
end

local init = function (env)
  local glyph = require("glyph_table")
  local config = env.engine.schema.config
  local layout = config:get_string("speller/layout")
  local layout_types = {
    ["full"]=1,
    ["flypy"]=1,
    ["ms"]=1,
    ["natural"]=1,
    ["double_plus"]=2,
    ["chole"]=2
  }
  local freq_lvl = { 0, 1, 3, 5, 10, 50, 100, 1000, 5000, 10000 }
  local min_freq = freq_lvl[ config:get_int("translator/glyph_min_freq") + 1 ] or 0
  env.gl_hint_level = config:get_int("translator/glyph_hint_level")
  env.gl_auto_level = config:get_int("translator/glyph_auto_level")
  env.gl_min_freq = min_freq * 0.51 / 10000
  if layout == "full" then env.gl_auto_level = 0 end
  env.glyph_table = (layout_types[layout] == 2 and glyph.table_II or glyph.table_I)
end

return { init = init, func = filter }

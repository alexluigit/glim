--[[
oneword_filter: 单字固定顺序
--]]

local input_helper = require("helpers.input")
local cand_helper = require("helpers.candidate")

local function filter(cands, env)
  local ctx = env.engine.context
  local input = ctx.input
  local input_len = input:len()
  local caret = ctx.caret_pos
  local tab_caret = tonumber(ctx:get_property("tab_caret"))
  local seg_len = caret - tab_caret
  local fixed_26 = env.fixed_26
  if input:match("%l+") and seg_len == 1 then
    local tail = input:sub(caret, caret)
    local words = env.alpha_table[tail]
    ctx:set_property("input_C1", words[1])
    for i, word in ipairs(words) do
      cand = Candidate("one", caret, caret + 1, word, "")
      yield(cand)
    end
  elseif env.fixed_ch and input:match("%l+") and seg_len == 2 then
    local words_text, filtered, rest = cand_helper.filter_charset(cands)
    cand_helper.sort_by_heteronym(filtered, words_text)
    local rec = false
    for i, cand in ipairs(filtered) do
      local text = cand.text
      local head_ch_word = env.alpha_table[input:sub(caret - 1, caret - 1)][1]
      if not rec then
        ctx:set_property("input_C1", head_ch_word)
        rec = input_helper.set_history(ctx, seg_len, text)
      end
      -- do not enable fixed_26 feature when composing sentence with TAB key
      if fixed_26 and input_len <= 2 then
        if text ~= head_ch_word then yield(cand) end
      else
        yield(cand)
      end
    end
    for i, cand in ipairs(rest) do yield(cand) end
  else
    for cand in cands:iter() do yield(cand) end
  end
end

local init = function(env)
  local fixed_ch = env.engine.schema.config:get_bool("glim/fixed_single_ch")
  local layout = env.engine.schema.config:get_string("speller/layout")
  env.fixed_26 = env.engine.schema.config:get_bool("glim/fixed_26")
  env.fixed_ch = fixed_ch
  env.alpha_table = require("tables.alphabet_table")(layout)
end

return {init = init, func = filter}

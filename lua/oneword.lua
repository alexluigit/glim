--[[
oneword_filter: 单字固定顺序
--]]

local input_helper = require("helpers.input")
local cand_helper = require("helpers.candidate")

local function filter(cands, env)
  local charset_table = env.charset_table
  local ctx = env.engine.context
  local input = ctx.input
  local caret = ctx.caret_pos
  local seg_len = caret - TAB_CARET
  if input:match("%l+") and seg_len == 1 then
    local tail = input:sub(caret, caret)
    local words = env.alpha_table[tail]
    ctx:set_property("input_C1", words[1])
    for i, word in ipairs(words) do
      cand = Candidate("one", 0, 1, word, "")
      yield(cand)
    end
  elseif env.fixed and input:match("%l+") and seg_len == 2 then
    local matched, rest = cand_helper.sort_by_heteronym(cands, charset_table)
    local rec = false
    local history = input_helper.get_history(ctx, 1)
    for i, cand in ipairs(matched) do
      local text = cand.text
      local valid = input_helper.validate(history, text) or input:len() > 2
      if not rec then rec = input_helper.set_history(ctx, seg_len, text) end
      if valid then yield(cand) end
    end
    for i, cand in ipairs(rest) do yield(cand) end
  else
    for cand in cands:iter() do yield(cand) end
  end
end

local init = function(env)
  local alpha_table = require("alphabet_table")
  local charset_table = require("charset_table")
  local fixed = env.engine.schema.config:get_bool("translator/fixed_single_ch")
  local layout = env.engine.schema.config:get_string("speller/layout")
  local layout_types = {
    ["full"]=1,
    ["flypy"]=1,
    ["ms"]=1,
    ["natural"]=1,
    ["double_plus"]=2,
    ["chole"]=2
  }
  env.fixed = fixed
  env.alpha_table = (layout_types[layout] == 2 and alpha_table.table_II or alpha_table.table_I)
  env.charset_table = charset_table
end

return {init = init, func = filter}

--[[
onechar_filter: 常用单字固定顺序
--]]

local function filter(cands, env)
  local ctx = env.engine.context
  local input = ctx.input
  local caret = ctx.caret_pos
  local selected = {}
  local rest = {}
  if env.onechar and input:match("^[A-Za-z]$") then
    local words = env.alpha_table[input]
    if words then
      for i, word in ipairs(words) do
        cand = Candidate("one", 0, 1, word, "")
        cand.quality = 10000000
        yield(cand)
      end
    end
  elseif env.fixed and input:match("%a+")
    and caret - TAB_CARET == 2 then
    local selected_text = {}
    for cand in cands:iter() do
      if CHARSET_TABLE[cand.text] then
        table.insert(selected, cand)
        selected_text[cand.text] = 1
      else
        table.insert(rest, cand)
      end
    end
    for i, cand in ipairs(selected) do
      local cand_prop = CHARSET_TABLE[cand.text]
      if not cand_prop["heteronym"] then
        cand.quality = cand_prop["rank"]
      else
        for k, v in pairs(cand_prop["heteronym"]) do
          if selected_text[k] then cand.quality = v end
        end
      end
    end
    table.sort(selected, function(a, b) return a.quality < b.quality end)
    -- for i, cand in ipairs(selected) do print(cand.text, cand.quality) end
    for i, cand in ipairs(selected) do yield(cand) end
    for i, cand in ipairs(rest) do yield(cand) end
  else
    for cand in cands:iter() do yield(cand) end
  end
end

local init = function(env)
  local alpha_table = require("alphabet_table")
  local onechar = env.engine.schema.config:get_bool("translator/onechar")
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
  env.onechar = onechar
  env.fixed = fixed
  env.alpha_table = (layout_types[layout] == 2 and alpha_table.table_II or alpha_table.table_I)
end

return {init = init, func = filter}

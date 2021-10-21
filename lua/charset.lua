--[[
charset_filter: 滤除 8105 外汉字
--]]

local function is_ext_ch(charset, text)
  if utf8.len(text) > 1 then
    return false
  else
    if charset[text] then
      return false
    else
      return true
    end
  end
end

local function charset_filter(cands, env)
  local ctx = env.engine.context
  local rest = {}
  if ctx.input:match("^[;/].*") or ctx.input:match("[^A-Za-z]$") then
    for cand in cands:iter() do yield(cand) end
    return
  end
  for cand in cands:iter() do
    if not is_ext_ch(env.charset_table, cand.text) then
      yield(cand)
    else
      table.insert(rest, cand)
    end
  end
  if ctx:get_option("full_charset") then
    for _, cand in ipairs(rest) do yield(cand) end
  end
end

local function init(env)
  local charset_table = require("charset_table")
  env.charset_table = charset_table
end

return { init = init, func = charset_filter }

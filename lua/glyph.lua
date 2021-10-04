--[[
glyph_filter: 候选项重排序, 匹配形码
--]]

local glyph_table = require("glyph_table")

local filter = function (cands, env)
  local context = env.engine.context
  local input = context:get_script_text()
  if string.match(input, ':%a?') then
    local glyph_all = string.gsub(input, ".*:", "")
    for cand in cands:iter() do
      local text = cand.text
      local utflen = utf8.len(text)
      local tail_ch = utf8.char(utf8.codepoint(text, 1 + (utflen - 1) * 3))
      local head_ch = nil
      local head_idx = 1 + (utflen - 2) * 3
      if head_idx > 0 then head_ch = utf8.char(utf8.codepoint(text, head_idx)) end
      if glyph_table[tail_ch] then
        local tail_ch_g1 = glyph_table[tail_ch]["first"]
        local tail_ch_g2 = glyph_table[tail_ch]["second"]
        if not head_ch then
          local glyph_filter_str = tail_ch_g1 .. tail_ch_g2
          if string.match(glyph_filter_str, '^' .. glyph_all) then
            cand.comment = ":" .. glyph_filter_str
            yield(cand)
          end
        else
          if glyph_table[head_ch] then
            local head_ch_g1 = glyph_table[head_ch]["first"]
            local head_ch_g2 = glyph_table[head_ch]["second"]
            local glyph_filter_str = head_ch_g1 .. tail_ch_g1 .. head_ch_g2 .. tail_ch_g2
            if string.match(glyph_filter_str, '^' .. glyph_all) then
              cand.comment = ":" .. glyph_filter_str
              yield(cand)
            end
          end
        end
      end
    end
  else
    for cand in cands:iter() do
      yield(cand)
    end
  end
end

return filter

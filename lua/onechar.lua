--[[
number_translator: 将单字母翻译为首页固定顺序候选
--]]

local alphabet_to_words = require("alphabet_table")

local function translator(input, seg, env)
  if string.len(input) == 1 then
    local words = alphabet_to_words[input]
    if words then
      for i, word in ipairs(words) do
        cand = Candidate("one", 0, 1, word, "")
        cand.quality = 10000000
        yield(cand)
      end
    end
  end
end


return translator

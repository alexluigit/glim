--[[
number_translator: 将单字母翻译为唯二候选
--]]

local alphabet_to_words = {
  ["a"] = {"啊", "阿"},
  ["b"] = {"不", "把"},
  ["c"] = {"从", "才"},
  ["d"] = {"的", "到"},
  ["e"] = {"嗯", "饿"},
  ["f"] = {"发", "分"},
  ["g"] = {"个", "给"},
  ["h"] = {"和", "好"},
  ["i"] = {"是", "说"},
  ["j"] = {"就", "将"},
  ["k"] = {"看", "开"},
  ["l"] = {"了", "来"},
  ["m"] = {"吗", "没"},
  ["n"] = {"你", "那"},
  ["o"] = {"哦", "喔"},
  ["p"] = {"怕", "跑"},
  ["q"] = {"去", "请"},
  ["r"] = {"人", "让"},
  ["s"] = {"算", "三"},
  ["t"] = {"他", "她"},
  ["u"] = {"吃", "出"},
  ["v"] = {"这", "中"},
  ["w"] = {"我", "问"},
  ["x"] = {"想", "向"},
  ["y"] = {"也", "要"},
  ["z"] = {"在", "再"}
}

local function translator(input, seg, env)
  if string.len(input) == 1 then
    local words = alphabet_to_words[input]
    if words then
      for i, word in ipairs(words) do
        yield(Candidate("one", 0, 1, word, ""))
      end
    end
  end
end


return translator

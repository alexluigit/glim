local alphabet_table_I = {
    ["a"] = {"啊", "阿", "吖"},
    ["b"] = {"不", "把", "吧"},
    ["c"] = {"才", "从", "次"},
    ["d"] = {"的", "到", "都"},
    ["e"] = {"二", "嗯", "而"},
    ["f"] = {"飞", "分", "放"},
    ["g"] = {"个", "给", "跟"},
    ["h"] = {"和", "好", "还"},
    ["i"] = {"出", "吃", "成"},
    ["j"] = {"就", "将", "讲"},
    ["k"] = {"看", "开", "卡"},
    ["l"] = {"了", "来", "啦"},
    ["m"] = {"没", "吗", "么"},
    ["n"] = {"你", "那", "呢"},
    ["o"] = {"哦", "喔", "噢"},
    ["p"] = {"跑", "平", "拍"},
    ["q"] = {"去", "请", "钱"},
    ["r"] = {"人", "让", "日"},
    ["s"] = {"三", "算", "所"},
    ["t"] = {"他", "她", "它"},
    ["u"] = {"是", "说", "上"},
    ["v"] = {"这", "中", "着"},
    ["w"] = {"我", "问", "哇"},
    ["x"] = {"小", "向", "下"},
    ["y"] = {"一", "也", "要"},
    ["z"] = {"在", "再", "做"}
}

local alphabet_table_II = {
    ["a"] = {"啊", "阿", "吖"},
    ["b"] = {"不", "把", "吧"},
    ["c"] = {"才", "从", "次"},
    ["d"] = {"的", "到", "都"},
    ["e"] = {"二", "嗯", "而"},
    ["f"] = {"飞", "分", "放"},
    ["g"] = {"个", "给", "跟"},
    ["h"] = {"和", "好", "还"},
    ["i"] = {"是", "说", "上"},
    ["j"] = {"就", "将", "讲"},
    ["k"] = {"看", "开", "卡"},
    ["l"] = {"了", "来", "啦"},
    ["m"] = {"没", "吗", "么"},
    ["n"] = {"你", "那", "呢"},
    ["o"] = {"哦", "喔", "噢"},
    ["p"] = {"跑", "平", "拍"},
    ["q"] = {"去", "请", "钱"},
    ["r"] = {"人", "让", "日"},
    ["s"] = {"三", "算", "所"},
    ["t"] = {"他", "她", "它"},
    ["u"] = {"出", "吃", "成"},
    ["v"] = {"这", "中", "着"},
    ["w"] = {"我", "问", "哇"},
    ["x"] = {"小", "向", "下"},
    ["y"] = {"一", "也", "要"},
    ["z"] = {"在", "再", "做"}
}

local swap_list = {
  {"啊","阿"},
  {"不","部"},
  {"才","菜"},
  {"的","得"},
  -- {"二","而"},
  -- {"飞","非"},
  {"个","各"},
  {"和","喝"},
  {"出","处"},
  {"就","久"},
  {"看","砍"},
  {"了","乐"},
  {"没","每"},
  {"你","泥"},
  {"哦","喔"},
  {"跑","泡"},
  {"去","区"},
  {"人","任"},
  {"三","散"},
  {"他","她"},
  {"是","事"},
  {"这","着"},
  -- {"我","窝"},
  {"小","笑"},
  {"一","以"},
  {"在","再"}
}

local function preprocess_charset_table(charset_table, should_swap)
  local swap_helper = function (charset_table, ch, rank)
    local temp = charset_table[ch]["rank"]
    charset_table[ch]["rank"] = rank
    if charset_table[ch]["heteronym"] then
      for k, v in pairs(charset_table[ch]["heteronym"]) do
        if v == temp then charset_table[ch]["heteronym"][k] = rank end
      end
    end
  end
  if should_swap then
    for i, pair in ipairs(swap_list) do
      local ch1 = pair[1]
      local ch2 = pair[2]
      local rank1 = charset_table[ch1]["rank"]
      local rank2 = charset_table[ch2]["rank"]
      swap_helper(charset_table, ch1, rank2)
      swap_helper(charset_table, ch2, rank1)
    end
  end
end

return {
  table_I = alphabet_table_I,
  table_II = alphabet_table_II,
  preprocess_charset_table = preprocess_charset_table
}

local function segmentor(_, env)
  local context = env.engine.context
  local save_input = context.input
  local abv_suffix = env.engine.schema.config:get_string("glim/abbrev_suffix")
  local abv_first = string.sub(abv_suffix, 1, 1)
  local abv_len = string.len(abv_suffix)
  if string.sub(save_input, 0 - abv_len) == abv_suffix then
    context:clear()
    for i = 1, string.len(save_input) - abv_len do
      context:push_input(string.sub(save_input, i, i))
      context:push_input("'")
    end
  elseif string.sub(save_input, -1) == abv_first and string.match(save_input, "'") then
    context:clear()
    local raw_input = string.gsub(string.gsub(save_input, "'", ''), abv_first, '')
    context:push_input(raw_input)
  end
end

return segmentor

local function segmentor(input, env)
  local context = env.engine.context
  local save_input = context:get_script_text()
  local suffix = env.engine.schema.config:get_string("punctuator/abbrev_suffix")
  if string.sub(save_input, 0 - string.len(suffix)) == suffix then
    context:clear()
    for i = 1, string.len(save_input) - string.len(suffix) do
      context:push_input(string.sub(save_input, i, i))
      context:push_input("'")
    end
  end
end

return segmentor

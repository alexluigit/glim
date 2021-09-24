local function filter(input, env)
  for cand in input:iter() do yield(cand) end
end

local function segmentor(input, env)
  local context = env.engine.context
  local save_input = context:get_script_text()
  if (string.sub(save_input, -2) == "::") then
    context:clear()
    for i = 1, string.len(save_input) -2 do
      context:push_input(string.sub(save_input, i, i))
      context:push_input("'")
    end
  end
end

return { filter = filter, segmentor = segmentor }


local Input = {}
local INPUT_START = 1
local INPUT_END = 5

function Input.get_history (ctx, history_len)
  local history = {}
  for i = INPUT_START, history_len do
    local property_name = "input_C" .. tostring(i)
    history[i] = ctx:get_property(property_name)
  end
  return history
end

function Input.set_history (ctx, hist_end, text)
  local property = "input_C" .. tostring(hist_end)
  local hist = Input.get_history(ctx, hist_end)
  if Input.validate(hist, text) then
    ctx:set_property(property, text)
    return true
  end
  return false
end

function Input.validate (input_history, text)
  for i = INPUT_START, #input_history do
    if input_history[i] == text then return false end
  end
  return true
end

function Input.log (ctx)
  local history = ""
  for i = INPUT_START, INPUT_END do
    local property_name = "input_C" .. tostring(i)
    history = history .. " " .. i .. " " .. ctx:get_property(property_name, "")
  end
  return history
end

function Input.clear (ctx, from)
  if from > INPUT_END + 1 then return end
  for i = from - 1, INPUT_END do
    local property_name = "input_C" .. tostring(i)
    ctx:set_property(property_name, "")
  end
end

function Input.reset (ctx)
  for i = INPUT_START, INPUT_END do
    local property_name = "input_C" .. tostring(i)
    ctx:set_property(property_name, "")
  end
end

return Input

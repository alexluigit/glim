local input_helper = require("helpers.input")
local key_helper = require("helpers.key_event")

local function _clean_up (ctx, clear)
  if clear then ctx:clear() end
  ctx:set_property("tab_caret", 0)
  input_helper.reset(ctx)
end

local function _commit_and_santinize (env, cand, idx)
  local ctx = env.engine.context
  if idx then ctx:select(idx) else ctx:confirm_current_selection() end
  local tab_caret = tonumber(ctx:get_property("tab_caret"))
  ctx:set_property("tab_caret", tab_caret + 2 * utf8.len(cand.text))
  if string.match(cand.type, 'glyph') then
    local g_len = tonumber(cand.type:sub(-1))
    ctx:pop_input(g_len)
  end
  ctx:refresh_non_confirmed_composition()
  ctx.caret_pos = ctx.input:len()
  if not ctx:has_menu() then
    ctx:commit()
    _clean_up(ctx)
  end
end

local function editor(key_event, env)
  local kAccepted = 1
  local kNoop = 2
  local engine = env.engine
  local ctx = engine.context
  local key_repr = key_event:repr() -- key representation
  local key_press = key_helper:init{ kEvent = key_event }
  local tab_caret = tonumber(ctx:get_property("tab_caret"))
  local should_forward_key = (not ctx:has_menu())
    or key_event:release() or key_event:ctrl() or key_event:alt()
  if should_forward_key then return kNoop end
  local input = ctx.input
  if key_press:is_space() then
    local cand = ctx:get_selected_candidate()
    _commit_and_santinize(env, cand)
  elseif key_press:is_backspace() then
    input_helper.clear(ctx, ctx.caret_pos - tab_caret)
    ctx:pop_input(1)
    if not ctx:has_menu() then
      ctx:set_property("tab_caret", 0)
    end
  elseif key_press:is_return() then
    env.engine:commit_text(input)
    _clean_up(ctx, true)
  elseif key_press:is_escape() then
    _clean_up(ctx, true)
  elseif key_press:is_digit() then
    local segment = ctx.composition:back()
    local curr_index = segment.selected_index
    local page_start_index = curr_index - curr_index % env.page_size
    local computed_index = page_start_index + tonumber(key_repr) - 1
    local cand = segment:get_candidate_at(computed_index)
    _commit_and_santinize(env, cand, computed_index)
  elseif key_press:is_lower() then
    -- to solve https://github.com/rime/librime/issues/500, so far so good
    ctx:push_input(key_repr)
  elseif env.navi_index and key_press:is_upper() then
    local index = env.navi_index[key_repr]
    if KeySequence then
      local ks = KeySequence()
      local ks_str = "{Home}"
      for i = 1, index do ks_str = ks_str .. "{Shift+Right}" end
      ks:parse(ks_str)
      for _, ke in ipairs(ks:toKeyEvent()) do engine:process_key(ke) end
    else
      ctx.caret_pos = tab_caret + index * 2
    end
  else
    return kNoop
  end
  return kAccepted
end

local init = function (env)
  local config = env.engine.schema.config
  env.engine.context:set_property("tab_caret", 0)
  env.navi_index = key_helper.to_navi_index(config:get_string("glim/navigate_with"))
  local layout = config:get_string("speller/layout")
  if layout == "full" and not KeySequence then env.navi_index = false end
  env.engine.context.commit_notifier:connect(_clean_up)
  env.page_size = config:get_int("menu/page_size")
end

return { init = init, func = editor }

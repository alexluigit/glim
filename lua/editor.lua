local input_helper = require("helpers.input")
local key_helper = require("helpers.key_event")

local function _commit_and_santinize (env, cand, idx)
  local ctx = env.engine.context
  if idx then ctx:select(idx) else ctx:confirm_current_selection() end
  TAB_CARET = TAB_CARET + 2 * utf8.len(cand.text)
  if string.match(cand.type, 'glyph') then
    local g_len = tonumber(cand.type:sub(-1))
    ctx:pop_input(g_len)
  end
  ctx:refresh_non_confirmed_composition()
  ctx.caret_pos = ctx.input:len()
  if not ctx:has_menu() then
    -- BUG? If context is 'composing' here, user dict do not pick up new word.
    ctx:commit()
    TAB_CARET = 0
    input_helper.reset(ctx)
  end
end

local function editor(key_event, env)
  local kAccepted = 1
  local kNoop = 2
  local ctx = env.engine.context
  local key_press = key_helper:init{ kCode = key_event.keycode }
  -- local tab_caret = ctx:get_property("TAB_CARET")
  local should_forward_key = (not ctx:has_menu())
    or key_event:release() or key_event:ctrl() or key_event:alt()
  if should_forward_key then return kNoop end
  local key_repr = key_event:repr() -- key representation
  local input = ctx.input
  if key_press:is_space() then
    local cand = ctx:get_selected_candidate()
    _commit_and_santinize(env, cand)
  elseif key_press:is_backspace() then
    input_helper.clear(ctx, ctx.caret_pos - TAB_CARET)
    ctx:pop_input(1)
    if not ctx:has_menu() then TAB_CARET = 0 end
  elseif key_press:is_return() then
    env.engine:commit_text(input)
    ctx:clear()
    input_helper.reset(ctx)
    TAB_CARET = 0
  elseif key_press:is_escape() then
    ctx:clear()
    TAB_CARET = 0
    input_helper.reset(ctx)
  elseif key_press:is_digit() then
    local segment = ctx.composition:back()
    local curr_index = segment.selected_index
    local page_start_index = curr_index - curr_index % env.page_size
    local computed_index = page_start_index + tonumber(key_repr) - 1
    local cand = segment:get_candidate_at(computed_index)
    _commit_and_santinize(env, cand, computed_index)
  elseif env.navi_index and key_press:is_upper() then
    ctx.caret_pos = TAB_CARET + env.navi_index[key_repr]
  else
    return kNoop
  end
  return kAccepted
end

local init = function (env)
  local config = env.engine.schema.config
  local layout = config:get_string("speller/layout")
  env.navi_index = key_helper.to_navi_index(config:get_string("glim/navigate_with"))
  if layout == "full" then env.navi_index = false end
  env.page_size = config:get_int("menu/page_size")
end

return { init = init, func = editor }

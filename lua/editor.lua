local input_helper = require("helpers.input")

local function _commit_and_santinize (input, ctx, cand, idx)
  -- todo if input include apostrophe
  if idx then ctx:select(idx) else ctx:confirm_current_selection() end
  TAB_CARET = TAB_CARET + 2 * utf8.len(cand.text)
  if string.match(cand.type, 'glyph') then
    local g_len = tonumber(cand.type:sub(-1))
    ctx:pop_input(g_len)
  end
  ctx:refresh_non_confirmed_composition()
  ctx.caret_pos = input:len()
  if not ctx:has_menu() then
    ctx:commit(ctx.get_commit_text(ctx))
    TAB_CARET = 0
    input_helper.reset(ctx)
  end
end

local function editor(key, env)
  local kAccepted = 1
  local kNoop = 2
  local key_repr = key:repr() -- key representation
  local ctx = env.engine.context
  local input = ctx.input
  -- local tab_caret = ctx:get_property("TAB_CARET")
  if ctx:has_menu() and string.len(input) > 0 then
    if key_repr == 'space' then
      local cand = ctx:get_selected_candidate()
      _commit_and_santinize(input, ctx, cand)
    elseif key_repr == 'BackSpace' then
      input_helper.clear(ctx, ctx.caret_pos - TAB_CARET)
      ctx:pop_input(1)
      if not ctx:has_menu() then TAB_CARET = 0 end
      -- todo: reopen commit
    elseif key_repr == 'Return' then
      env.engine:commit_text(input)
      ctx:clear()
      input_helper.reset(ctx)
      TAB_CARET = 0
    elseif key_repr == 'Escape' then
      ctx:clear()
      TAB_CARET = 0
      input_helper.reset(ctx)
    elseif string.match(key_repr, "^%d$") then
      local segment = ctx.composition:back()
      local curr_index = segment.selected_index
      local page_start_index = curr_index - curr_index % env.page_size
      local computed_index = page_start_index + tonumber(key_repr) - 1
      local cand = segment:get_candidate_at(computed_index)
      _commit_and_santinize(input, ctx, cand, computed_index)
    else
      return kNoop
    end
    return kAccepted
  else
    return kNoop
  end
end

local init = function (env)
  env.page_size = env.engine.schema.config:get_int("menu/page_size")
  -- env.notifier = env.engine.context.update_notifier:connect(function (ctx) end)
end

return { init = init, func = editor }

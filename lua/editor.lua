-- todo: tab key add ':' automaticallly

local function _sanitize_input (input, ctx, saved_caret)
  if string.match(input, ':%a?') then
    local g_len = saved_caret - string.find(input, ":") + 1
    ctx:pop_input(g_len)
  end
  ctx.caret_pos = ctx.caret_pos + 2
  if not ctx:has_menu() then
    ctx:commit(ctx.get_commit_text(ctx))
  end
end

local function editor(key, env)
  local kAccepted = 1
  local kNoop = 2
  local key_repr = key:repr() -- key representation
  local ctx = env.engine.context
  local input = ctx.input
  local saved_caret = ctx.caret_pos
  if string.len(input) > 0 then
    if key_repr == 'space' then
      ctx:confirm_current_selection()
      _sanitize_input(input, ctx, saved_caret)
    elseif key_repr == 'BackSpace' then
      ctx:pop_input(1)
    elseif key_repr == 'Return' then
      env.engine:commit_text(input)
      ctx:clear()
    elseif key_repr == 'Escape' then
      ctx:clear()
    elseif string.match(key_repr, "^%d$") then
      ctx:select(key_repr - 1)
      _sanitize_input(input, ctx, saved_caret)
    else
      return kNoop
    end
    return kAccepted
  else
    return kNoop
  end
end

return editor

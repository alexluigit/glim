Key = { kCode = 0x00 }

function Key:init (o)
  o = o or {}
  setmetatable(o, self)
  self.__index = self
  return o
end

function Key.to_navi_index(str)
  if str == "" then return false end
  local t = {}
  for i = 1, #str do
    local c = str:sub(i,i):upper()
    t["Shift+" .. c] = i + 1
  end
  return t
end

function Key:is_space ()
  return self.kCode == 0x20
end

function Key:is_backspace ()
  return self.kCode == 0xff08
end

function Key:is_return ()
  return self.kCode == 0xff0d
end

function Key:is_escape ()
  return self.kCode == 0xff1b
end

function Key:is_digit ()
  return self.kCode > 0x30 and self.kCode <= 0x39
end

function Key:is_upper ()
  return self.kCode > 0x40 and self.kCode <= 0x5a
end

function Key:is_lower ()
  return self.kCode > 0x60 and self.kCode <= 0x7a
end

return Key

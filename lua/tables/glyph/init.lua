local glyph_tables = {
  ["I"] = require(... .. ".I"),
  ["II"] = require(... .. ".II")
}

local layout_types = {
    ["full"] = "I",
    ["flypy"] = "I",
    ["natural"] = "I",
    ["ms"] = "I",
    ["pyjj"] = "II",
    ["chole"] = "II"
}

return function(layout)
    return glyph_tables[layout_types[layout]]
end

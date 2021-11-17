local duplicate_tables = {
  ["flypy"] = require(... .. ".flypy"),
  ["ms"] = require(... .. ".ms"),
  ["natural"] = require(... .. ".natural"),
  ["pyjj"] = require(... .. ".pyjj"),
  ["chole"] = require(... .. ".chole"),
}

return function(layout)
  return duplicate_tables[layout]
end

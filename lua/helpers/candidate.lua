local Candidate = {}
local AUTO_GLYPH_WORD = 2

function Candidate.get_words (cand, glyph_table)
  local text = cand.text
  local ch_idxs = {}
  for i in utf8.codes(text) do table.insert(ch_idxs, i) end
  local tail_ch = utf8.char(utf8.codepoint(text, ch_idxs[#ch_idxs]))
  local head_ch = nil
  if #ch_idxs > 1 then head_ch = utf8.char(utf8.codepoint(text, ch_idxs[#ch_idxs - 1])) end
  local valid_tail_word = glyph_table[tail_ch]
  local valid_head_word = (not head_ch) or glyph_table[head_ch]
  return tail_ch, head_ch, (valid_tail_word and valid_head_word)
end

function Candidate.get_hint (hint_lvl, py, gl)
  if hint_lvl == 1 then
    return "↬ " .. py
  elseif hint_lvl == 2 then
    return "↬ " .. py .. " " .. gl
  end
end

function Candidate.place_phrase (phrase, glyph_match, rule, top_quality, input_len)
  local top = 1
  local bottom = 2
  if not phrase then
    return 0
  elseif #glyph_match == 0 then
    return top
  elseif input_len % 2 == 1 then
    return bottom
  elseif rule == "phrase" then
    return top
  elseif rule == "glyph" then
    return bottom
  else
    return phrase.quality > top_quality and top or bottom
  end
end

function Candidate.sort_by_rank (ch_table, matched, glyph_lvl)
  if glyph_lvl > AUTO_GLYPH_WORD then return end
  local by_rank = function(a, b)
    return ch_table[a.text]["rank"] < ch_table[b.text]["rank"]
  end
  table.sort(matched, by_rank)
end

function Candidate.sort_by_heteronym (cands, charset_table)
  local matched = {}
  local rest = {}
  local matched_text = {}
  for cand in cands:iter() do
    if charset_table[cand.text] then
      table.insert(matched, cand)
      matched_text[cand.text] = 1
    else
      table.insert(rest, cand)
    end
  end
  for i, cand in ipairs(matched) do
    local cand_prop = charset_table[cand.text]
    if not cand_prop["heteronym"] then
      cand.quality = cand_prop["rank"]
    else
      for k, v in pairs(cand_prop["heteronym"]) do
        if matched_text[k] then cand.quality = v end
      end
    end
  end
  table.sort(matched, function(a, b) return a.quality < b.quality end)
  return matched, rest
end

return Candidate

local Candidate = {}
local AUTO_GLYPH_WORD = 2
local charset_table = require("../tables.charset_table")

function Candidate.append_valid_word (cand, words_text)
  if charset_table[cand.text] then
    words_text[cand.text] = 1
  end
end

function Candidate.filter_charset (cands)
  local filtered = {}
  local rest = {}
  local words_text = {}
  for cand in cands:iter() do
    if charset_table[cand.text] then
      table.insert(filtered, cand)
      words_text[cand.text] = 1
    else
      table.insert(rest, cand)
    end
  end
  return words_text, filtered, rest
end

function Candidate.get_words (cand)
  local text = cand.text
  local ch_idxs = {}
  for i in utf8.codes(text) do table.insert(ch_idxs, i) end
  local tail_ch = utf8.char(utf8.codepoint(text, ch_idxs[#ch_idxs]))
  local head_ch = nil
  if #ch_idxs > 1 then head_ch = utf8.char(utf8.codepoint(text, ch_idxs[#ch_idxs - 1])) end
  local valid_tail_word = charset_table[tail_ch]
  local valid_head_word = (not head_ch) or charset_table[head_ch]
  return tail_ch, head_ch, (valid_tail_word and valid_head_word)
end

function Candidate.get_hint (hint_lvl, py, gl)
  if hint_lvl == 1 then
    return "↬ " .. py
  elseif hint_lvl == 2 then
    return "↬ " .. py .. " " .. gl
  end
end

function Candidate.place_phrase
  (phrase, glyph_match, fixed, top_quality, input, dup_table)
  local top = 1
  local bottom = 2
  if not phrase then
    return 0
  elseif #glyph_match == 0 then
    return top
  elseif input:len() % 2 == 1 then
    return bottom
  elseif fixed then
    return dup_table[input:sub(-4)] and top or bottom
  else
    return phrase.quality >= top_quality and top or bottom
  end
end

function Candidate.sort_by_heteronym (tbl, words_text, glyph_lvl)
  if (glyph_lvl or 0) > AUTO_GLYPH_WORD then return end
  local get_rank = function (cand)
    local cand_prop = charset_table[cand.text]
    local rank = 10000
    if not cand_prop["heteronym"] then
      rank = cand_prop["rank"]
    else
      for k, v in pairs(cand_prop["heteronym"]) do
        if words_text[k] then rank = v end
      end
    end
    return rank
  end
  table.sort(tbl, function(a, b) return get_rank(a) < get_rank(b) end)
end

return Candidate

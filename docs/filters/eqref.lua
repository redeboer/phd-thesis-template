--[[
This script performs post-processing for Quarto to replace `\ref` with `\eqref`
for equations. See https://github.com/quarto-dev/quarto-cli/issues/2439 for more
information.
--]]

PANDOC = require("pandoc")

local function replace_eqref(el)
  if el.format == "latex" then
    el.text = el.text:gsub("\\ref{eq%-", "\\eqref{eq-")
    return el
  end
end

function RawBlock(el)
  return replace_eqref(el)
end

function RawInline(el)
  return replace_eqref(el)
end

local NBSP = "\194\160" -- nbsp; U+00A0
local function is_equation(el) return el and el.t == "Str" and el.text == "Equation" end
local function is_gap(el) return el and (el.t == "Space" or (el.t == "Str" and el.text == NBSP)) end
local function is_span(el) return el and el.t == "Span" end
local function is_equation_link(el) return el and el.t == "Link" and el.target:match("#eq%-") end

local function parenthesize_link(el)
  if not is_equation_link(el) then
    return nil
  end

  local content = el.content
  if is_equation(content[1]) and is_gap(content[2]) then
    if content[3] and content[3].t == "Str" and content[3].text:match("^%(") then
      return el
    end
    local new_content = PANDOC.List({content[1], content[2], PANDOC.Str("(")})
    for i = 3, #content do
      new_content:insert(content[i])
    end
    new_content:insert(PANDOC.Str(")"))
    el.content = new_content
    return el
  end

  if content[1] and content[1].t == "Str" then
    local prefix = "Equation" .. NBSP
    local number = content[1].text:match("^" .. prefix .. "(.+)$")
    if number then
      if number:match("^%(.+%)$") then
        return el
      end
      content[1] = PANDOC.Str("Equation" .. NBSP .. "(" .. number .. ")")
      return el
    end
  end
end

function Inlines(inlines)
  local out = PANDOC.List()
  local i = 1
  while i <= #inlines - 2 do
    local label     = inlines[i]
    local separator = inlines[i + 1]
    local ref_span  = inlines[i + 2]
    if is_equation(label) and is_gap(separator) and is_span(ref_span) then
      out:insert(label)
      out:insert(separator)
      out:insert(PANDOC.Str("("))
      out:insert(ref_span)
      out:insert(PANDOC.Str(")"))
      i = i + 3
    else
      out:insert(parenthesize_link(label) or label)
      i = i + 1
    end
  end
  while i <= #inlines do
    out:insert(parenthesize_link(inlines[i]) or inlines[i])
    i = i + 1
  end
  return out
end

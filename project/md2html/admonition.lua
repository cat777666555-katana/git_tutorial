local map = {
  ["[!NOTE]"] = { class = "note", title = "Note", icon = "💡" },
  ["[!TIP]"] = { class = "tip", title = "Tip", icon = "✨" },
  ["[!IMPORTANT]"] = { class = "important", title = "Important", icon = "❗" },
  ["[!WARNING]"] = { class = "warning", title = "Warning", icon = "⚠️" },
  ["[!CAUTION]"] = { class = "caution", title = "Caution", icon = "🚧" }
}

function BlockQuote(el)
  if #el.content == 0 then return nil end

  local first = el.content[1]
  if first.t ~= "Para" then return nil end

  local inlines = first.content
  if #inlines == 0 then return nil end

  local key = inlines[1].text
  local info = map[key]
  if not info then return nil end

  -- Remove [!XXX]
  table.remove(inlines, 1)
  if #inlines > 0 and inlines[1].t == "Space" then
    table.remove(inlines, 1)
  end

  -- Title paragraph（Para に class を付けるには Div で包む）
  local title_para = pandoc.Para({
    pandoc.Str(info.icon .. " " .. info.title)
  })
  local title_div = pandoc.Div({ title_para }, pandoc.Attr("", {"admonition-title"}))

  -- Combine blocks
  local blocks = { title_div }
  for i = 1, #el.content do
    table.insert(blocks, el.content[i])
  end

  -- Outer admonition box
  local attr = pandoc.Attr("", {"admonition", info.class})
  return pandoc.Div(blocks, attr)
end

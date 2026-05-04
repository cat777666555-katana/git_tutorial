local pipe = pandoc.pipe

function CodeBlock(block)
  if block.classes[1] == "plantuml" then
    local jar = os.getenv("PLANTUML_JAR")
    if not jar then
      io.stderr:write("環境変数 PLANTUML_JAR が設定されていません\n")
      return block
    end

    local img = pipe("java", {"-jar", jar, "-tpng", "-pipe"}, block.text)
    local fname = "plantuml-" .. pandoc.sha1(block.text) .. ".png"
    local f = io.open(fname, "wb")
    f:write(img)
    f:close()
    return pandoc.Para({ pandoc.Image({}, fname) })
  end
end

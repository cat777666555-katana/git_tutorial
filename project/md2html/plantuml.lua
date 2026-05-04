local pipe = pandoc.pipe

function CodeBlock(block)
  if block.classes[1] == "plantuml" then
    local jar = os.getenv("PLANTUML_JAR")
    if not jar then
      io.stderr:write("The environment variable PLANTUML_JAR is not set.\n")
      return block
    end

    local img = pipe("java", {"-jar", jar, "-tpng", "-pipe"}, block.text)
    local fname = "plantuml-" .. pandoc.sha1(block.text) .. ".png"
    local f = io.open(fname, "wb")
    f:write(img)
    f:close()
    return pandoc.Para({ pandoc.Image({}, fname) })
  end

  return block
end

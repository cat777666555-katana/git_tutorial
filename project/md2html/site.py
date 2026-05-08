import os
import sys
import json
import shutil
import subprocess
from pathlib import Path


# ----------------------------------------
# 0. 引数チェック
# ----------------------------------------
if len(sys.argv) < 2:
    print("ERROR: docs のパスが指定されていません。", file=sys.stderr)
    sys.exit(1)

docs_root = Path(sys.argv[1]).resolve()
if not docs_root.exists():
    print("ERROR: 指定された docs パスが存在しません。", file=sys.stderr)
    sys.exit(1)

out_dir = Path("./site")
template = Path("./template.html")
css_file = Path("./style.css")
search_js = Path("./search.js")

# ----------------------------------------
# 1. 出力フォルダを作り直す
# ----------------------------------------
if out_dir.exists():
    shutil.rmtree(out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

# ----------------------------------------
# 2. docs 以下の md を再帰的に取得
# ----------------------------------------
files = list(docs_root.rglob("*.md"))
nav_files = [f for f in files if f.name != "index.md"]

# ----------------------------------------
# 3. ツリーナビ用データ構造生成
# ----------------------------------------
tree = {}

for file in nav_files:
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")  # Windows/Unix 両対応
    parts = relative.split(os.sep)

    current = tree
    for p in parts[:-1]:
        if p not in current:
            current[p] = {}
        current = current[p]

    current[parts[-1]] = str(file)


# ----------------------------------------
# 4. ツリーナビ HTML 生成（フラット名リンク）
# ----------------------------------------
def build_nav_html(tree, indent=""):
    html = "<ul>\n"

    if indent == "":
        html += '<li><a href="index.html">Top</a></li>\n'

    for key in sorted(tree.keys()):
        value = tree[key]

        if isinstance(value, dict):
            html += f"<li>{key}\n" + build_nav_html(value, indent + "  ") + "</li>\n"
        else:
            rel = value[len(str(docs_root)) :].lstrip("\\/")
            flat = rel.replace("\\", "_").replace("/", "_").replace(".md", ".html")
            html += f'<li><a href="{flat}">{key}</a></li>\n'

    html += "</ul>\n"
    return html


nav_html = build_nav_html(tree)
(out_dir / "nav.html").write_text(nav_html, encoding="utf-8")


# ----------------------------------------
# 5. search.json 生成
# ----------------------------------------
search_index = []

for file in files:
    content = file.read_text(encoding="utf-8")
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")
    flat = relative.replace("\\", "_").replace("/", "_").replace(".md", ".html")

    search_index.append({
        "title": relative,
        "url": flat,
        "body": content
    })

(out_dir / "search.json").write_text(
    json.dumps(search_index, ensure_ascii=False, indent=2),
    encoding="utf-8"
)


# ----------------------------------------
# 6. Pandoc による HTML 生成
# ----------------------------------------
for file in files:
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")
    flat = relative.replace("\\", "_").replace("/", "_").replace(".md", ".html")
    out_path = out_dir / flat

    cmd = [
        "pandoc",
        "--standalone",
        f"--template={template}",
        f"--include-before-body={out_dir / 'nav.html'}",
        "--css=style.css",
        "--syntax-highlighting=pygments",
        "--lua-filter=admonition.lua",
        "--lua-filter=plantuml.lua",
        "-o", str(out_path),
        str(file)
    ]

    subprocess.run(cmd, check=True)
    print(f"生成: {out_path}")


# ----------------------------------------
# 7. 静的ファイルコピー
# ----------------------------------------
shutil.copy(css_file, out_dir)
shutil.copy(search_js, out_dir)

print("\n=== サイト生成完了 ===")
print(f"出力: {out_dir}\n")

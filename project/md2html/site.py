import os
import sys
import json
import shutil
import subprocess
import re
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
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")
    parts = relative.split(os.sep)

    current = tree
    for p in parts[:-1]:
        if p not in current:
            current[p] = {}
        current = current[p]

    current[parts[-1]] = str(file)


# ----------------------------------------
# 4. ツリーナビ HTML 生成
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
# 5. @import 展開（MPE 互換）
# ----------------------------------------
IMPORT_RE = re.compile(r'@import\s+"([^"]+)"')

def expand_imports(md_path: Path, docs_root: Path, visited=None):
    """
    MPE の @import を再帰展開する。
    .puml は ```plantuml に自動ラップする。
    """
    if visited is None:
        visited = set()

    md_path = md_path.resolve()

    # 無限ループ防止
    if md_path in visited:
        return f"\n<!-- WARNING: circular import detected: {md_path} -->\n"
    visited.add(md_path)

    text = md_path.read_text(encoding="utf-8")

    def replace(match):
        rel = match.group(1)
        target = (md_path.parent / rel).resolve()

        if not target.exists():
            return f"\n<!-- ERROR: not found: {rel} -->\n"

        # .puml → plantuml コードブロック
        if target.suffix.lower() == ".puml":
            code = target.read_text(encoding="utf-8")
            return f"\n```plantuml\n{code}\n```\n"

        # .md → 再帰展開
        if target.suffix.lower() == ".md":
            return expand_imports(target, docs_root, visited)

        # その他 → そのまま挿入
        return target.read_text(encoding="utf-8")

    expanded = IMPORT_RE.sub(replace, text)
    return expanded


# ----------------------------------------
# 6. search.json 生成
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
# 7. HTML 生成（@import 展開 → Pandoc）
# ----------------------------------------
tmp_dir = out_dir / "_tmp"
tmp_dir.mkdir(exist_ok=True)

for file in files:
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")
    flat = relative.replace("\\", "_").replace("/", "_").replace(".md", ".html")
    out_path = out_dir / flat

    # --- @import 展開済み Markdown を生成 ---
    expanded_md = expand_imports(file, docs_root)

    tmp_md = tmp_dir / (flat + ".md")
    tmp_md.write_text(expanded_md, encoding="utf-8")

    # --- Pandoc 実行 ---
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
        str(tmp_md)
    ]

    subprocess.run(cmd, check=True)
    print(f"生成: {out_path}")


# ----------------------------------------
# 8. 静的ファイルコピー
# ----------------------------------------
shutil.copy(css_file, out_dir)
shutil.copy(search_js, out_dir)

print("\n=== サイト生成完了 ===")
print(f"出力: {out_dir}\n")

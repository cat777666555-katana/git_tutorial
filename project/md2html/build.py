import os
import sys
import json
import shutil
import subprocess
import re
import hashlib
from pathlib import Path


# ----------------------------------------
# 0. 引数チェック（docs と out_dir の 2 つ）
# ----------------------------------------
if len(sys.argv) < 3:
    print("使い方: python build.py <docsフォルダ> <出力先フォルダ>", file=sys.stderr)
    sys.exit(1)

docs_root = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()

print(f"[INFO] docs フォルダ: {docs_root}")
print(f"[INFO] 出力先フォルダ: {out_dir}")

if not docs_root.exists():
    print(f"[ERROR] docs フォルダが存在しません: {docs_root}", file=sys.stderr)
    sys.exit(1)


# ----------------------------------------
# 1. 出力フォルダを作成（存在すれば削除 → 再作成）
# ----------------------------------------
if out_dir.exists():
    print(f"[INFO] 既存の出力フォルダを削除します: {out_dir}")
    shutil.rmtree(out_dir)

print(f"[INFO] 出力フォルダを作成します: {out_dir}")
out_dir.mkdir(parents=True, exist_ok=True)


# ----------------------------------------
# 2. その他の設定ファイル
# ----------------------------------------
template = Path("./template.html")
css_file = Path("./style.css")
search_js = Path("./search.js")

if not template.exists():
    print("[ERROR] template.html が見つかりません", file=sys.stderr)
    sys.exit(1)

if not css_file.exists():
    print("[ERROR] style.css が見つかりません", file=sys.stderr)
    sys.exit(1)

if not search_js.exists():
    print("[ERROR] search.js が見つかりません", file=sys.stderr)
    sys.exit(1)


# ----------------------------------------
# 3. PlantUML.jar の確認
# ----------------------------------------
PLANTUML_JAR = os.environ.get("PLANTUML_JAR")
if not PLANTUML_JAR:
    print("ERROR: 環境変数 PLANTUML_JAR が設定されていません。", file=sys.stderr)
    sys.exit(1)

PLANTUML_JAR = Path(PLANTUML_JAR).resolve()

if not PLANTUML_JAR.exists():
    print(f"ERROR: PlantUML.jar が見つかりません: {PLANTUML_JAR}", file=sys.stderr)
    sys.exit(1)

print(f"[INFO] PlantUML.jar: {PLANTUML_JAR}")


# ----------------------------------------
# 4. docs 以下の md を再帰的に取得
# ----------------------------------------
files = list(docs_root.rglob("*.md"))
nav_files = [f for f in files if f.name != "index.md"]

print(f"[INFO] Markdown ファイル数: {len(files)}")


# ----------------------------------------
# 5. ツリーナビ構造生成
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
# 6. ツリーナビ HTML 生成
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
# 7. PlantUML SVG 生成（md 名入り）
# ----------------------------------------
def generate_plantuml_svg(code: str, out_dir: Path, md_name: str) -> str:
    sha = hashlib.sha1(code.encode("utf-8")).hexdigest()
    base = Path(md_name).stem.replace(" ", "_")
    svg_name = f"plantuml-{base}-{sha}.svg"
    svg_path = out_dir / svg_name

    if svg_path.exists():
        print(f"[INFO] SVG キャッシュ利用: {svg_name}")
        return svg_name

    print(f"[INFO] PlantUML 生成: {svg_name}")

    tmp_puml = out_dir / f"{sha}.puml"
    tmp_puml.write_text(code, encoding="utf-8")

    subprocess.run(
        [
            "java",
            "-jar",
            str(PLANTUML_JAR),
            "-tsvg",
            "-o",
            str(out_dir.resolve()),
            str(tmp_puml),
        ],
        check=True,
    )

    svg_files = list(out_dir.glob("*.svg"))
    if not svg_files:
        raise RuntimeError("PlantUML が SVG を生成しませんでした")

    generated_svg = max(svg_files, key=lambda p: p.stat().st_mtime)
    generated_svg.rename(svg_path)

    tmp_puml.unlink()

    return svg_name


# ----------------------------------------
# 8. plantuml ブロック変換
# ----------------------------------------
PLANTUML_BLOCK_RE = re.compile(
    r"```plantuml\s+([\s\S]*?)```",
    re.MULTILINE,
)

def replace_plantuml_blocks(md_text: str, out_dir: Path, md_name: str) -> str:
    def repl(match):
        code = match.group(1).strip()
        svg_name = generate_plantuml_svg(code, out_dir, md_name)
        return f'\n<img src="{svg_name}" alt="plantuml-diagram" />\n'

    return PLANTUML_BLOCK_RE.sub(repl, md_text)


# ----------------------------------------
# 9. Admonition 変換
# ----------------------------------------
ADMONITION_RE = re.compile(
    r"^> \[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*\n((?:> .*\n?)*)",
    re.MULTILINE
)

def convert_admonitions(md_text: str) -> str:
    def repl(match):
        kind = match.group(1).lower()
        body_block = match.group(2)

        # "> " を削除
        lines = [line[2:].rstrip() for line in body_block.splitlines()]
        inner_html = "\n".join(f"<p>{line}</p>" for line in lines if line.strip())

        title = kind.capitalize()

        return (
            f'<div class="admonition {kind}">\n'
            f'  <p class="admonition-title">{title}</p>\n'
            f'{inner_html}\n'
            f'</div>\n'
        )

    return ADMONITION_RE.sub(repl, md_text)




# ----------------------------------------
# 10. @import 展開（md 名伝播）
# ----------------------------------------
IMPORT_RE = re.compile(r'@import\s+"([^"]+)"')

def expand_imports(md_path: Path, docs_root: Path, visited=None):
    if visited is None:
        visited = set()

    md_path = md_path.resolve()
    md_name = md_path.name

    if md_path in visited:
        return f"\n<!-- WARNING: circular import detected: {md_path} -->\n"
    visited.add(md_path)

    text = md_path.read_text(encoding="utf-8")

    def wrap_codeblock(ext: str, code: str):
        return f"\n```{ext}\n{code}\n```\n"

    def process_single_import(target: Path):
        if not target.exists():
            return f"\n<!-- ERROR: not found: {target} -->\n"

        suffix = target.suffix.lower()

        if suffix == ".puml":
            code = target.read_text(encoding="utf-8")
            svg = generate_plantuml_svg(code, out_dir, md_name)
            return f'\n<img src="{svg}" alt="{target.name}" />\n'

        if suffix == ".md":
            return expand_imports(target, docs_root, visited)

        if suffix == ".mermaid":
            code = target.read_text(encoding="utf-8")
            return wrap_codeblock("mermaid", code)

        if suffix == ".json":
            code = target.read_text(encoding="utf-8")
            return wrap_codeblock("json", code)

        if suffix in [".yaml", ".yml"]:
            code = target.read_text(encoding="utf-8")
            return wrap_codeblock("yaml", code)

        return target.read_text(encoding="utf-8")

    def replace(match):
        rel = match.group(1)
        pattern = (md_path.parent / rel).resolve()

        if any(ch in rel for ch in "*?["):
            matched = list(md_path.parent.glob(rel))
            if not matched:
                return f"\n<!-- WARNING: glob not matched: {rel} -->\n"
            return "\n".join(process_single_import(t) for t in matched)

        return process_single_import(pattern)

    expanded = IMPORT_RE.sub(replace, text)

    expanded = replace_plantuml_blocks(expanded, out_dir, md_name)
    expanded = convert_admonitions(expanded)

    return expanded


# ----------------------------------------
# 11. search.json 生成
# ----------------------------------------
search_index = []

for file in files:
    content = file.read_text(encoding="utf-8")
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")
    flat = relative.replace("\\", "_").replace("/", "_").replace(".md", ".html")

    search_index.append(
        {
            "title": relative,
            "url": flat,
            "body": content,
        }
    )

(out_dir / "search.json").write_text(
    json.dumps(search_index, ensure_ascii=False, indent=2),
    encoding="utf-8",
)


# ----------------------------------------
# 12. HTML 生成
# ----------------------------------------
tmp_dir = out_dir / "_tmp"
tmp_dir.mkdir(exist_ok=True)

for file in files:
    relative = str(file)[len(str(docs_root)) :].lstrip("\\/")
    flat = relative.replace("\\", "_").replace("/", "_").replace(".md", ".html")
    out_path = out_dir / flat

    print(f"[INFO] HTML 生成: {out_path}")

    expanded_md = expand_imports(file, docs_root)

    tmp_md = tmp_dir / (flat + ".md")
    tmp_md.write_text(expanded_md, encoding="utf-8")

    cmd = [
        "pandoc",
        "--standalone",
        f"--template={template}",
        f"--include-before-body={out_dir / 'nav.html'}",
        "--css=style.css",
        "--syntax-highlighting=pygments",
        "-o",
        str(out_path),
        str(tmp_md),
    ]

    subprocess.run(cmd, check=True)


# ----------------------------------------
# 13. 静的ファイルコピー
# ----------------------------------------
shutil.copy(css_file, out_dir)
shutil.copy(search_js, out_dir)

print("\n=== サイト生成完了 ===")
print(f"出力: {out_dir}\n")

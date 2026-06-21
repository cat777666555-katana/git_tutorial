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

for f in [template, css_file, search_js]:
    if not f.exists():
        print(f"[ERROR] {f.name} が見つかりません", file=sys.stderr)
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
# 4. Mermaid CLI の確認
# ----------------------------------------
def check_mmdc():
    try:
        subprocess.run(["mmdc.cmd", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

if not check_mmdc():
    print("[ERROR] Mermaid CLI (mmdc.cmd) が見つかりません。", file=sys.stderr)
    print("npm install -g @mermaid-js/mermaid-cli")
    sys.exit(1)


# ----------------------------------------
# 5. docs 以下の md を再帰的に取得
# ----------------------------------------
files = list(docs_root.rglob("*.md"))
nav_files = [f for f in files if f.name != "index.md"]

print(f"[INFO] Markdown ファイル数: {len(files)}")


# ----------------------------------------
# 6. ツリーナビ構造生成
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
# 7. ツリーナビ HTML 生成
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
# 8. PlantUML SVG 生成（md 名入り）
# ----------------------------------------
def generate_plantuml_svg(code: str, out_dir: Path, md_name: str) -> str:
    sha = hashlib.sha1(code.encode("utf-8")).hexdigest()
    base = Path(md_name).stem.replace(" ", "_")
    svg_name = f"plantuml-{base}-{sha}.svg"
    svg_path = out_dir / svg_name

    # キャッシュ
    if svg_path.exists():
        print(f"[INFO] SVG キャッシュ利用: {svg_name}")
        return svg_name

    print(f"[INFO] PlantUML 生成: {svg_name}")

    tmp_puml = out_dir / f"{sha}.puml"
    tmp_puml.write_text(code, encoding="utf-8")

    try:
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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print("[WARN] PlantUML 生成失敗。コードをそのまま表示します。")
        print("[WARN] PlantUML stderr:", e.stderr.decode("utf-8", errors="ignore"))

        # エラー時はコードブロックとして返す
        fallback = f"plantuml-error-{sha}.txt"
        fallback_path = out_dir / fallback
        fallback_path.write_text(code, encoding="utf-8")
        tmp_puml.unlink()
        return fallback  # HTML 側では <img> ではなくテキスト扱いにする

    # 正常時
    svg_files = list(out_dir.glob("*.svg"))
    if not svg_files:
        print("[WARN] PlantUML が SVG を生成しませんでした。")
        fallback = f"plantuml-error-{sha}.txt"
        fallback_path = out_dir / fallback
        fallback_path.write_text(code, encoding="utf-8")
        tmp_puml.unlink()
        return fallback

    generated_svg = max(svg_files, key=lambda p: p.stat().st_mtime)
    generated_svg.rename(svg_path)
    tmp_puml.unlink()

    return svg_name


# ----------------------------------------
# 9. Mermaid SVG 生成（md 名入り）
# ----------------------------------------
def generate_mermaid_svg(code: str, out_dir: Path, md_name: str) -> str:
    sha = hashlib.sha1(code.encode("utf-8")).hexdigest()
    base = Path(md_name).stem.replace(" ", "_")

    svg_name = f"mermaid-{base}-{sha}.svg"
    svg_path = out_dir / svg_name

    if svg_path.exists():
        print(f"[INFO] Mermaid SVG キャッシュ利用: {svg_name}")
        return svg_name

    print(f"[INFO] Mermaid 生成: {svg_name}")

    tmp_mmd = out_dir / f"{sha}.mmd"
    tmp_mmd.write_text(code, encoding="utf-8")

    subprocess.run(
        [
            "mmdc.cmd",
            "-i", str(tmp_mmd),
            "-o", str(svg_path),
            "-b", "transparent",
            "--scale", "2.0"
        ],
        check=True,
    )

    tmp_mmd.unlink()

    return svg_name


# ----------------------------------------
# 10. plantuml / mermaid ブロック変換
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


# 誤爆しないように、```mermaid の直後と ``` の直前に改行を要求
MERMAID_BLOCK_RE = re.compile(
    r"```mermaid\n([\s\S]*?)\n```",
    re.MULTILINE,
)

# Mermaid の diagram type 一覧
MERMAID_TYPES = (
    "graph", "flowchart", "sequenceDiagram", "classDiagram",
    "stateDiagram", "erDiagram", "journey", "gantt",
    "pie", "mindmap", "timeline"
)

def is_valid_mermaid(code: str) -> bool:
    """Mermaid の diagram type で始まっているか確認"""
    stripped = code.strip()
    if not stripped:
        return False
    first = stripped.splitlines()[0].strip()
    return first.startswith(MERMAID_TYPES)


def replace_mermaid_blocks(md_text: str, out_dir: Path, md_name: str) -> str:

    def repl(match):
        code = match.group(1).strip()

        # Mermaid ではない → そのままコードブロックとして残す
        if not is_valid_mermaid(code):
            print("[WARN] Mermaid ではないためスキップ:", code[:40])
            return f"```mermaid\n{code}\n```"

        # Mermaid SVG 生成
        try:
            svg_name = generate_mermaid_svg(code, out_dir, md_name)
            return f'\n<img src="{svg_name}" alt="mermaid-diagram" />\n'

        except Exception as e:
            print("[WARN] Mermaid 生成失敗:", e)

            # エラー時はコードを保存して fallback
            sha = hashlib.sha1(code.encode("utf-8")).hexdigest()
            fallback = f"mermaid-error-{sha}.txt"
            fallback_path = out_dir / fallback
            fallback_path.write_text(code, encoding="utf-8")

            return f"\n<!-- Mermaid error: {fallback} -->\n"

    return MERMAID_BLOCK_RE.sub(repl, md_text)


# ----------------------------------------
# 11. Admonition 変換（あなたのまま）
# ----------------------------------------
ADMONITION_RE = re.compile(
    r"^> \[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*\n((?:> .*\n?)*)",
    re.MULTILINE
)

def convert_admonitions(md_text: str) -> str:
    def repl(match):
        kind = match.group(1).lower()
        body_block = match.group(2)

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
# 12. @import 展開（安全版）
# ----------------------------------------
IMPORT_RE = re.compile(r'@import\s+"([^"]+)"')

def expand_imports(md_path: Path, docs_root: Path, visited=None):
    if visited is None:
        visited = set()

    md_path = md_path.resolve()
    md_name = md_path.name

    # 循環参照防止
    if md_path in visited:
        return f'\n<!-- WARNING: circular import detected: {md_path} -->\n'
    visited.add(md_path)

    text = md_path.read_text(encoding="utf-8")

    def wrap_codeblock(ext: str, code: str):
        return f"\n```{ext}\n{code}\n```\n"

    # -------------------------
    # import 1件を処理する関数
    # -------------------------
    def process_single_import(target: Path, rel: str):
        # フォルダは読み込めない → @import をそのまま残す
        if target.is_dir():
            return f'@import "{rel}"'

        # ファイルが存在しない → @import をそのまま残す
        if not target.exists():
            return f'@import "{rel}"'

        suffix = target.suffix.lower()

        # --- PlantUML ---
        if suffix == ".puml":
            code = target.read_text(encoding="utf-8")
            svg = generate_plantuml_svg(code, out_dir, md_name)
            return f'\n<img src="{svg}" alt="{target.name}" />\n'

        # --- Mermaid ---
        if suffix == ".mermaid":
            code = target.read_text(encoding="utf-8")
            svg = generate_mermaid_svg(code, out_dir, md_name)
            return f'\n<img src="{svg}" alt="{target.name}" />\n'

        # --- Markdown（再帰展開） ---
        if suffix == ".md":
            return expand_imports(target, docs_root, visited)

        # --- JSON ---
        if suffix == ".json":
            return wrap_codeblock("json", target.read_text(encoding="utf-8"))

        # --- YAML ---
        if suffix in [".yaml", ".yml"]:
            return wrap_codeblock("yaml", target.read_text(encoding="utf-8"))

        # --- その他のファイル ---
        return target.read_text(encoding="utf-8")

    # -------------------------
    # @import "xxx" を置換する
    # -------------------------
    def replace(match):
        rel = match.group(1)
        pattern = (md_path.parent / rel).resolve()

        # --- glob パターン ---
        if any(ch in rel for ch in "*?["):
            matched = list(md_path.parent.glob(rel))

            # フォルダを除外
            matched = [t for t in matched if t.is_file()]

            if not matched:
                return f'@import "{rel}"'

            return "\n".join(process_single_import(t, rel) for t in matched)

        # --- 単一ファイル ---
        return process_single_import(pattern, rel)

    # @import 展開
    expanded = IMPORT_RE.sub(replace, text)

    # plantuml / mermaid ブロック変換
    expanded = replace_plantuml_blocks(expanded, out_dir, md_name)
    expanded = replace_mermaid_blocks(expanded, out_dir, md_name)

    # admonition 変換
    expanded = convert_admonitions(expanded)

    return expanded


# ----------------------------------------
# 13. search.json 生成
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
# 14. HTML 生成
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
# 15. 静的ファイルコピー
# ----------------------------------------
shutil.copy(css_file, out_dir)
shutil.copy(search_js, out_dir)

print("\n=== サイト生成完了 ===")
print(f"出力: {out_dir}\n")

param(
    [string]$DocsPath
)

if (-not $DocsPath) {
    Write-Host "ERROR: docs のパスが指定されていません。" -ForegroundColor Red
    exit 1
}

$DocsRoot = (Resolve-Path $DocsPath).Path
$OutDir = ".\site"
$Template = ".\template.html"
$CssFile = ".\style.css"
$SearchJs = ".\search.js"

# 出力フォルダを作り直す
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Path $OutDir | Out-Null

# docs 以下の md を再帰的に取得
$files = Get-ChildItem -Path $DocsRoot -Filter *.md -Recurse

# -------------------------
# ① ツリーナビ用データ構造生成
# -------------------------
$tree = @{}
foreach ($file in $files) {

    $relative = $file.FullName.Substring($DocsRoot.Length).TrimStart("\","/")
    $parts = $relative -split '\\'

    $current = $tree
    for ($i = 0; $i -lt $parts.Length - 1; $i++) {
        $p = $parts[$i]
        if (-not $current.ContainsKey($p)) {
            $current[$p] = @{}
        }
        $current = $current[$p]
    }

    $current[$parts[-1]] = $file.FullName
}

# -------------------------
# ② ツリーナビ HTML 生成関数（フラット名リンク）
# -------------------------
function Build-NavHtml($tree, $indent) {
    $nl = [Environment]::NewLine
    $html = "<ul>$nl"

    if ($indent -eq "") {
        $html += "<li><a href=""top.html"">Top</a></li>$nl"
    }

    foreach ($key in ($tree.Keys | Sort-Object)) {
        $value = $tree[$key]

        if ($value -is [hashtable]) {
            $html += "<li>$key$nl" + (Build-NavHtml $value ($indent + "  ")) + "</li>$nl"
        }
        else {
            $rel = $value.Substring($DocsRoot.Length).TrimStart("\","/")
            $flatName = ($rel -replace '\\','_') -replace '\.md$', '.html'
            $html += "<li><a href=""$flatName"">$key</a></li>$nl"
        }
    }

    $html += "</ul>$nl"
    return $html
}


$navHtml = Build-NavHtml $tree ""
Set-Content -Path "$OutDir\nav.html" -Value $navHtml -Encoding UTF8

# -------------------------
# ③ 全文検索用 JSON 生成（URL もフラット名）
# -------------------------
$searchIndex = @()

foreach ($file in $files) {
    $content  = Get-Content $file.FullName -Raw
    $relative = $file.FullName.Substring($DocsRoot.Length).TrimStart("\","/")

    # フラット名
    $flatName = ($relative -replace '\\','_') -replace '\.md$', '.html'

    $searchIndex += [PSCustomObject]@{
        title = $relative
        url   = $flatName
        body  = $content
    }
}

$searchJson = ConvertTo-Json $searchIndex -Depth 5
Set-Content -Path "$OutDir\search.json" -Value $searchJson -Encoding UTF8

# -------------------------
# ④ HTML 生成（フラット構造）
# -------------------------
foreach ($file in $files) {

    $relative = $file.FullName.Substring($DocsRoot.Length).TrimStart("\","/")
    $flatName = ($relative -replace '\\','_') -replace '\.md$', '.html'
    $outPath = Join-Path $OutDir $flatName

    pandoc `
        --standalone `
        --template=$Template `
        --include-before-body="$OutDir\nav.html" `
        --css="style.css" `
        --lua-filter="plantuml.lua" `
        -o $outPath `
        $file.FullName


    Write-Host "生成: $outPath"
}

Copy-Item $CssFile $OutDir
Copy-Item $SearchJs $OutDir

Write-Host ""
Write-Host "=== サイト生成完了 ==="
Write-Host "出力: $OutDir"
Write-Host ""

# -------------------------
# ⑤ Top ページ生成（リンクもフラット名）
# -------------------------
$links = @()
foreach ($file in $files) {
    $relative = $file.FullName.Substring($DocsRoot.Length).TrimStart("\","/")
    $flatName = ($relative -replace '\\','_') -replace '\.md$', '.html'
    $links += "<li><a href=""$flatName"">$relative</a></li>"
}

$navContent = Get-Content "$OutDir\nav.html" -Raw

$topHtml = @"
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Top</title>
  <link rel="stylesheet" href="style.css">
  <script src="search.js"></script>
</head>
<body>

<div id="sidebar">
  <input type="text" id="searchBox" placeholder="検索...">

  <div id="nav">
$navContent
  </div>
</div>

<div id="content">
  <h1>Top</h1>
  <ul>
    $($links -join "`r`n")
  </ul>
</div>

<script>
highlightCurrentPage();
setupSearch();
</script>

</body>
</html>
"@

Set-Content -Path "$OutDir\top.html" -Value $topHtml -Encoding UTF8

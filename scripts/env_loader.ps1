<#
.SYNOPSIS
  UTF-8 の .env ファイルを読み込み、環境変数として設定する
.DESCRIPTION
  - KEY=VALUE 形式のみ対応
  - 空行はスキップ
  - コメント行（#や;）は無し前提
.PARAMETER Path
  読み込む .env ファイルのパス
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

if (-not (Test-Path $Path)) {
    Write-Error "[ERROR] ファイルが存在しません: $Path"
    exit 1
}

# UTF-8 で読み込み
Get-Content -Path $Path -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -ne "") {
        $parts = $line -split '=', 2
        if ($parts.Count -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            # 環境変数に設定（現在のプロセスのみ有効）
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

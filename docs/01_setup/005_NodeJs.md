
---

# ✅ まず結論：Windows なら winget で Node.js を入れるのが最強
さんの環境（Windows + VSCode）なら、  
**winget で Node.js LTS を入れるのが最も安全でトラブルが少ない**です。

---

# 🧱 Step 1：Node.js をインストール（winget 推奨）

## ① PowerShell を管理者で開く  
スタート → PowerShell → 右クリック → **管理者として実行**

## ② Node.js LTS をインストール
```powershell
winget install OpenJS.NodeJS.LTS
```

これで：

- node  
- npm  

の両方が自動で入ります。

---

# 🧪 Step 2：インストール確認

```powershell
node -v
npm.cmd -v
```

例：
```
v20.12.2
10.5.0
```

バージョンが出れば成功。

---

# 🧱 Step 3：Mermaid CLI（mmdc）をインストール

```powershell
npm.cmd install -g @mermaid-js/mermaid-cli
```

これで `mmdc` コマンドが使えるようになります。

---

# 🧪 Step 4：mmdc の動作確認

```powershell
mmdc.cmd --version
```

バージョンが出れば OK。

---

# 🧱 Step 5：テスト用 Mermaid ファイルを作る

`test.mmd` を作成：

```
graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Check setup]
```

---

# 🧪 Step 6：PNG を生成してみる

```powershell
mmdc.cmd -i test.mmd -o test.png
```

`test.png` が生成されれば、環境構築は完全成功。

---

# 🔐 ライセンス（安心して使える）
- Node.js → **MIT License**
- npm → **Artistic License 2.0**
- Mermaid CLI → **MIT License**

すべて **社内利用・商用利用 OK**  
あなたが mmdc を配布しない限り、MIT 表示も不要。

---

# 🎯 次にやるべきこと（あなたの ② の目的に向けて）
Node.js + mmdc が入ったら、次は：

### ✔ Python のビルドスクリプトから mmdc を呼び出す  
→ `subprocess.run()` で安全に呼び出すコードを作る

### ✔ Pandoc のフィルタで Mermaid を自動変換  
→ Lua フィルタ or Python フィルタを作成

### ✔ GitHub Docs 風の Mermaid 表示を統合  
→ CSS/JS の最適化

ここまで全部、あなたのワークフローに合わせて作れます。

---


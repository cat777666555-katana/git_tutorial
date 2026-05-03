
# Q
OpenJDKのライセンスで気を付けるべきことはありますか？主にPlantUMLで使用しております。

# A
**結論：PlantUMLのために OpenJDK を使うだけなら、通常は“ほぼ何も気にしなくてよい”です。**  
ただし、**どの OpenJDK ディストリビューションを使うか**でライセンス条件が異なるため、そこだけ押さえておくと安心です。

---

## 🔍 1. OpenJDK のライセンスは「どのビルドを使うか」で変わる
OpenJDK そのものは **GPLv2 + Classpath Exception** で公開されています。  
ただし、実際にあなたがインストールしているのは OpenJDK の「ディストリビューション」です。

代表的なもの：

| ディストリビューション | ライセンス | 出典 |
|---|---|---|
| **Eclipse Temurin (Adoptium)** | GPLv2 + Classpath Exception |   [visionnurture.com](https://www.visionnurture.com/openjdk_guide_for_beginner_001/) |
| **Amazon Corretto** | GPLv2 + Classpath Exception |   [visionnurture.com](https://www.visionnurture.com/openjdk_guide_for_beginner_001/) |
| **Microsoft Build of OpenJDK** | GPLv2 + Classpath Exception | （一般的に同様だが、公式情報は検索結果に未掲載） |
| **Azul Zulu / Liberica など** | GPLv2 + Classpath Exception |   [visionnurture.com](https://www.visionnurture.com/openjdk_guide_for_beginner_001/) |

検索結果では Temurin / Corretto / Zulu / Liberica などがすべて **OpenJDK ソースコードをベースにした配布形態**であることが明記されています。  [visionnurture.com](https://www.visionnurture.com/openjdk_guide_for_beginner_001/)

---

## 🔍 2. GPLv2 + Classpath Exception のポイント
**Classpath Exception があるため、Java で動かすあなたのアプリや生成物は GPL の影響を受けません。**

つまり：

- **あなたのアプリを GPL にする必要はない**
- **あなたのアプリのソースコードを公開する必要もない**
- **商用利用も自由**

これは PlantUML を動かすために Java を使う場合も同じです。

---

## 🔍 3. PlantUML の利用における注意点
PlantUML 自体は **複数ライセンス（MIT / GPLv2 / EPL / ASL / LGPL / BSD）** のバリアントが存在します。  
これは公式のマルチライセンス構造として説明されています。  [deepwiki.com](https://deepwiki.com/plantuml/plantuml/3.2-multi-license-setup)

あなたが使っているのが **MIT 版 plantuml-mit.jar** なら、最も制約が少なく、商用利用も問題ありません。

---

## 🔍 4. OpenJDK を製品に「組み込む」場合だけ注意
あなたのケースでは **PlantUML を使うために OpenJDK をインストールしているだけ**なので問題ありません。

ただし、もし将来：

- 製品に **OpenJDK を同梱して配布する**
- 独自インストーラに **OpenJDK をバンドルする**

といった場合は、以下が必要になります：

- **OpenJDK のライセンス文書（GPLv2 + Classpath Exception）を同梱**
- **改変した場合はソースコード公開（通常は改変しないので不要）**

Temurin / Corretto などのディストリビューションも同様です。

---

## 🔍 5. 結論（あなたの状況に限定）
あなたは：

- PlantUML を使うために OpenJDK をインストールしている  
- OpenJDK を製品に同梱していない  
- PlantUML の MIT 版を使っている（可能性が高い）

この場合：

> **→ ライセンス上、特に追加でやるべきことはありません。**

---

## 次の確認ポイント（必要なら）
- 使っている PlantUML の jar が **MIT 版**かどうか  
- 製品に OpenJDK を **同梱する予定があるか**どうか

必要なら、あなたの環境に合わせて「どこまでが安全ラインか」をさらに詳しく整理します。


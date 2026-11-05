# 公開説明の補完と同期保全（2026-11-05）

100件を維持し、空欄24件を公式情報で補完。061・066はPR #8と同じ内部比較文のみを削除。その他のフィールドは変更していません。

シート末尾にAA「公開用説明」、AB「公開説明確認日」、AC「公開説明根拠URL」を追加。A:Zの値・数式は保持。空欄は同一IDの既存説明を継承し、候補に説明がないイベントがあれば同期を停止します。備考・Instagram制作履歴は公開しません。

同期処理はPR #8のID照合、欠落停止、公開フィールド許可リスト、内部情報検出、バックアップ、原子的置換、Actions直列化を継承。Muse・Metricool等の検出と説明空欄の拒否を追加。既存PR #8自体は変更せず、現在の100件に適用しています。

公式情報の留意点：

- 096：当初8社発表後、リカーたぬきちが11/4出展中止。入場券は全3部完売・追加販売なし。
- 099：企画は11/7開始、店頭試飲の初回は11/14〜15。
- 087：受講券は完売。
- 079：10/23は当選発表予定日。応募期間10/19〜21は終了済み。既存日付は保持し、説明に明記。
- 083：公式告知で確認できた日程・共同開催者のみを記載。昼の部の個別内容・料金は再確認できず、推測しない。
- 有料蒸溜所ツアーの料金未確認分は推測せず公式予約ページへ案内。

## 一次情報

- WEJ-2026-079 SMWS 33.141・125.81 希少カスク2銘柄 抽選販売：https://smwsjapan.com/product/list?fpfl=0&pno=1
- WEJ-2026-098 WHISKY MEW『攻殻機動隊』シークレットスペイサイド1994・グレングラント2009 抽選：https://whiskymew.jp/items/2026/gits/lottery-gits.html
- WEJ-2026-084 Glenfiddich The Celestial Pairing vol.2：https://www.tablecheck.com/shops/ritzcarlton-tokyo-thelobbylounge-bar/reserve?menu_items=6a9fcec47bc8f4f518a4e53b
- WEJ-2026-080 SMWS CODE33＆125 オンライン・テイスティング会：https://smwsjapan.com/2026%EF%BC%8E10%E6%9C%88%2B%E3%82%AA%E3%83%B3%E3%83%A9%E3%82%A4%E3%83%B3%E3%83%BB%E3%83%86%E3%82%A4%E3%82%B9%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0%E4%BC%9A%EF%BC%9ACODE33%2B%EF%BC%86%2B125%E7%89%B9%E9%9B%86%EF%BC%81/product/202610_onlinetasting_oct/
- WEJ-2026-083 SMWS THE GATHERING JAPAN 2026 愛知・名古屋 昼の部：https://blog.smwsjapan.com/event/10943/
- WEJ-2026-103 シーバスリーガル×新橋『今宵は、新橋で。』飲食店タイアップ・くじ企画：https://prtimes.jp/main/html/rd/p/000000410.000004201.html
- WEJ-2026-096 ウイスキーフェスティバル東京2026 会場ブース限定商品8社・希少ボトル：https://prtimes.jp/main/html/rd/p/000000373.000119996.html
- WEJ-2026-097 神戸蒸溜所 KOBE WHISKY 1st edition・200本限定シングルカスク発売：https://prtimes.jp/main/html/rd/p/000000010.000146820.html
- WEJ-2026-087 ウイスキーフェスティバル東京 嘉之助マスタークラス 10年目のKANOSUKE：https://whiskyfestival.jp/tokyo2026/seminar4/
- WEJ-2026-099 リカーマウンテン SINGLE MALT JOURNEY 2026 3ブランド週末試飲会：https://prtimes.jp/main/html/rd/p/000000258.000030735.html
- WEJ-2026-095 WHISKY MEW『ウルトラマン』スプリングバンク2000・キャンベルタウン2016 限定抽選：https://whiskymew.jp/items/2026/ultraman/lottery-ultraman.html
- WEJ-2026-102 デュワーズ12年ハイボール缶発売記念イベント Magic Hour Park：https://prtimes.jp/main/html/rd/p/000000143.000001172.html
- WEJ-2026-088 日光街道 小山蒸溜所「哲／TETSU」2026限定2銘柄（各1000本）：https://nishiborisyuzo.com/tetsu-2026-25312.html
- WEJ-2026-081 SMWS JAPAN 11月東京テイスティング会 第1部：https://smwsjapan.com/product/list?fpfl=0&pno=1
- WEJ-2026-082 SMWS 東京テイスティング会 第2部：https://smwsjapan.com/product/list?fpfl=0&pno=1
- WEJ-2026-100 福島ウイスキーテイスティングセミナー＆トークイベント（輿水精一氏×土屋守）：https://prtimes.jp/main/html/rd/p/000000378.000119996.html
- WEJ-2026-091 厚岸ウイスキー メーカーズディナー2026｜グラーレ マルヤマ：https://www.gllare.jp/697/
- WEJ-2026-090 土屋守と行く 富士御殿場蒸溜所＆富嶽蒸溜所 日帰りツアー：https://prtimes.jp/main/html/rd/p/000000368.000119996.html
- WEJ-2026-094 山崎蒸溜所 2027年1月 山崎ウイスキー館無料見学予約開始：https://www.suntory.co.jp/factory/yamazaki/news/detail/post_4.html
- WEJ-2026-086 山崎蒸溜所 2027年1月有料ツアー抽選受付：https://www.suntory.co.jp/factory/yamazaki/news/detail/post_4.html
- WEJ-2026-085 白州蒸溜所 2027年1月有料ツアー抽選受付：https://www.suntory.co.jp/factory/hakushu/news/detail/post_6.html
- WEJ-2026-093 白州蒸溜所 2027年1月 無料入場・見学予約開始：https://www.suntory.co.jp/factory/hakushu/news/detail/post_6.html
- WEJ-2026-101 オーケー ウイスキーセミナー2027（山崎蒸溜所講師）アプリ抽選：https://ok-corporation.jp/news/entry-3347.html
- WEJ-2026-089 ウイスキー＆スピリッツフェスティバル2027 in 横浜：https://prtimes.jp/main/html/rd/p/000000372.000119996.html

追加確認先：
- https://whiskyfestival.jp/?eventmenu=info
- https://whiskymew.jp/items/2026/gits/item-gits.html
- SMWS公式商品ページ：033141_lot、125081_lot、EV_202611_tasting_thabase_1、EV_202611_tasting_thabase_2（公式サイト検索から確認）。

## 検証

13テスト成功。100件の全IDと説明以外の全フィールドを保全。空欄24→0。103行の実シート公開入力列による100件同期を2回検証、実CSVのdry-runも100件・差分なし。既存1件／18件消失・同件数置換・重複・非掲載化・新規説明なし・内部情報混入・不正日付／URL・書込失敗で停止を検証。fixtureは公開同期用列だけを保存し内部備考・IG履歴を含めない。

# 公開説明の補完（2026-11-05）

対象: mainの100件中、publicDescriptionが空欄の24件。公式発表で確認できた内容のみ補完。開催情報・料金・URLなど既存フィールドは変更しない。

AA「公開用説明」、AB「公開説明確認日」、AC「公開説明根拠URL」で管理。公開対象はAAだけ。既存26列と備考・Instagram履歴を保全し、備考を説明の代替に使わない。

PR #8の同期安全対策を同じ実装から導入。旧97件JSONでmainを置換せず、現在100件を維持。061・066の内部管理表現だけを除去。新しい公開説明を生成後に空欄が残れば同期停止。既存説明はIDで保持する。

## 根拠と確認範囲

- WEJ-2026-079 SMWS 33.141・125.81 希少カスク2銘柄 抽選販売
  - https://smwsjapan.com/%E3%80%90%E6%8A%BD%E9%81%B8%E7%94%B3%E8%BE%BC%E3%80%9133%EF%BC%8E141%E3%80%80%EF%BC%8A%E6%8A%BD%E9%81%B8%E7%94%B3%E8%BE%BC%E5%B0%82%E7%94%A8/product/033141_lot/
  - https://smwsjapan.com/%E3%80%90%E6%8A%BD%E9%81%B8%E7%94%B3%E8%BE%BC%E3%80%91125%EF%BC%8E81%E3%80%80%EF%BC%8A%E6%8A%BD%E9%81%B8%E7%94%B3%E8%BE%BC%E5%B0%82%E7%94%A8/product/125081_lot/
- WEJ-2026-098 WHISKY MEW『攻殻機動隊』シークレットスペイサイド1994・グレングラント2009 抽選
  - https://whiskymew.jp/items/2026/gits/lottery-gits.html
- WEJ-2026-084 Glenfiddich The Celestial Pairing vol.2
  - https://www.tablecheck.com/ja/shops/ritzcarlton-tokyo-thelobbylounge-bar/reserve?menu_items=6a9fcec47bc8f4f518a4e53b
- WEJ-2026-080 SMWS CODE33＆125 オンライン・テイスティング会
  - https://smwsjapan.com/2026%EF%BC%8E10%E6%9C%88%2B%E3%82%AA%E3%83%B3%E3%83%A9%E3%82%A4%E3%83%B3%E3%83%BB%E3%83%86%E3%82%A4%E3%82%B9%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0%E4%BC%9A%EF%BC%9ACODE33%2B%EF%BC%86%2B125%E7%89%B9%E9%9B%86%EF%BC%81/product/202610_onlinetasting_oct/
- WEJ-2026-083 SMWS THE GATHERING JAPAN 2026 愛知・名古屋 昼の部
  - https://blog.smwsjapan.com/event/10943/
- WEJ-2026-103 シーバスリーガル×新橋『今宵は、新橋で。』飲食店タイアップ・くじ企画
  - https://www.chivas.com/ja-jp/stories/shimbashi-area-jack/
- WEJ-2026-096 ウイスキーフェスティバル東京2026 会場ブース限定商品8社・希少ボトル
  - https://prtimes.jp/main/html/rd/p/000000373.000119996.html
  - https://whiskyfestival.jp/?eventmenu=info
- WEJ-2026-097 神戸蒸溜所 KOBE WHISKY 1st edition・200本限定シングルカスク発売
  - https://prtimes.jp/main/html/rd/p/000000010.000146820.html
- WEJ-2026-087 ウイスキーフェスティバル東京 嘉之助マスタークラス 10年目のKANOSUKE
  - https://whiskyfestival.jp/tokyo2026/seminar4/
- WEJ-2026-099 リカーマウンテン SINGLE MALT JOURNEY 2026 3ブランド週末試飲会
  - https://prtimes.jp/main/html/rd/p/000000258.000030735.html
- WEJ-2026-095 WHISKY MEW『ウルトラマン』スプリングバンク2000・キャンベルタウン2016 限定抽選
  - https://whiskymew.jp/items/2026/ultraman/lottery-ultraman.html
- WEJ-2026-102 デュワーズ12年ハイボール缶発売記念イベント Magic Hour Park
  - https://prtimes.jp/main/html/rd/p/000000143.000001172.html
- WEJ-2026-088 日光街道 小山蒸溜所「哲／TETSU」2026限定2銘柄（各1000本）
  - https://nishiborisyuzo.com/tetsu-2026-25312.html
- WEJ-2026-081 SMWS JAPAN 11月東京テイスティング会 第1部
  - https://smwsjapan.com/%5B%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%5D%2B2026%E5%B9%B411%E6%9C%8821%E6%97%A5%28%E5%9C%9F%29%2B13%EF%BC%9A00%EF%BD%9E14%EF%BC%9A30%2B%2B%2B%E6%9D%B1%E4%BA%AC%E4%BC%9A%E5%A0%B4%2B%E3%83%86%E3%82%A4%E3%82%B9%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0%E4%BC%9A%2B%40THE%2BBASE/product/EV_202611_tasting_thabase_1/
- WEJ-2026-082 SMWS 東京テイスティング会 第2部
  - https://smwsjapan.com/%5B%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88%5D%2B2026%E5%B9%B411%E6%9C%8821%E6%97%A5%28%E5%9C%9F%29%2B%2B14%EF%BC%9A40%EF%BD%9E16%EF%BC%9A10%2B%2B%2B%E6%9D%B1%E4%BA%AC%E4%BC%9A%E5%A0%B4%2B%E3%83%86%E3%82%A4%E3%82%B9%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0%E4%BC%9A%2B%40THE%2BBASE/product/EV_202611_tasting_thabase_2/
- WEJ-2026-100 福島ウイスキーテイスティングセミナー＆トークイベント（輿水精一氏×土屋守）
  - https://prtimes.jp/main/html/rd/p/000000378.000119996.html
- WEJ-2026-091 厚岸ウイスキー メーカーズディナー2026｜グラーレ マルヤマ
  - https://www.gllare.jp/697/
- WEJ-2026-090 土屋守と行く 富士御殿場蒸溜所＆富嶽蒸溜所 日帰りツアー
  - https://prtimes.jp/main/html/rd/p/000000368.000119996.html
- WEJ-2026-094 山崎蒸溜所 2027年1月 山崎ウイスキー館無料見学予約開始
  - https://www.suntory.co.jp/factory/yamazaki/news/detail/post_4.html
- WEJ-2026-086 山崎蒸溜所 2027年1月有料ツアー抽選受付
  - https://www.suntory.co.jp/factory/yamazaki/news/detail/post_4.html
- WEJ-2026-085 白州蒸溜所 2027年1月有料ツアー抽選受付
  - https://www.suntory.co.jp/factory/hakushu/news/detail/post_6.html
- WEJ-2026-093 白州蒸溜所 2027年1月 無料入場・見学予約開始
  - https://www.suntory.co.jp/factory/hakushu/news/detail/post_6.html
- WEJ-2026-101 オーケー ウイスキーセミナー2027（山崎蒸溜所講師）アプリ抽選
  - https://ok-corporation.jp/news/entry-3347.html
- WEJ-2026-089 ウイスキー＆スピリッツフェスティバル2027 in 横浜
  - https://prtimes.jp/main/html/rd/p/000000372.000119996.html

## 留保

- 083は公式ブログの開催日・共同企画・テーマ・ゲスト登録を確認。昼の部の料金・詳細会場・提供内容は再確認できず、説明には追加しない。既存料金欄は保全。
- 081・082・079の公式商品詳細は検索インデックス経由で確認。082は完売表示。申込可否や在庫を保証しない。
- 東京フェスは当初8社のリリースに加え、11月4日のリカーたぬきち出展取消と全3部入場券完売を反映。既存のタイトル・料金欄は変更せず、説明で変更を明示。
- 山崎・白州は更新型ページのため、対象月と申込期間を区別して記載。有料ツアーの料金は推測しない。
- 061・066はPR #8の修正文を採用。今回公式内容を新規に追加していない。

## 検証

41テスト成功。現100件・24空欄の移行、全IDと説明以外のフィールド保持、2回同期、未入力新規イベント停止、内部メモ混入停止を確認。fixtureのCSVは公開入力列だけで、備考やIG履歴を含まない。

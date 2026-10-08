# WEJ Webサイト初期版

## 公開方法
1. GitHubでリポジトリ `wej-website` を作成。
2. `index.html` と `events.json` をルートにアップロード。
3. Cloudflare PagesでGitHubリポジトリを接続し、静的サイトとしてデプロイ。ビルドコマンドは不要、出力ディレクトリは `.` 。
4. 発行されたURLを確認後、Instagramのプロフィールに登録。

## 運営
- `events.json` を更新してGitHubへコミットすると、Cloudflare Pagesで再デプロイできます。
- この初期版は2026年10月8日時点のWEJ DBから選んだ8件のみを収録。自動同期は未実装です。
- Google Sheetsからの自動同期には別途GitHub ActionsとGoogle Sheets API認証が必要です。
- 公開前に公式情報で販売状況・日程・リンクを再確認してください。

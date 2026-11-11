# Canva PNG export and staging (WEJ)

The Canva connector can inspect/edit designs but currently does not provide a full-resolution export action in this integration. Do not use expiring Canva thumbnail URLs for Instagram publication.

## One-time manual export per design
1. Open the linked Canva design and select **Share → Download → PNG → All 4 pages**.
2. Keep the page order. Each image must be 1080×1350 px.
3. Upload the PNGs to this feature branch under `posting/media/<post-id>/01.png` through `04.png`. Do **not** upload to the default branch until the images and event facts are reviewed.
4. Run `python scripts/build_post_media_manifest.py` to check file presence, PNG headers and dimensions. It writes `posting/media-manifest.json`.
5. Only after official event status and image content are checked may a post be submitted for explicit approval. No approval or Instagram publishing is implemented yet.

Post IDs: `nagahama-fes-2026`, `shuiiku-seminar-2026`, `nagahama-special-2026`, `utsunomiya-marche-2026`, `niseko-seminar-2026`.

**Safety:** The current approval queue is a staging ledger. It cannot publish. Canva editing links and thumbnails are not stable image-hosting URLs. Never put Meta credentials in this public repository.

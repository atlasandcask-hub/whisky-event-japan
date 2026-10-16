# WEJ Instagram approval queue (staging only)

This is a manual approval ledger. It does not post to Instagram and does not change the public WEJ website.

## Safety contract
- Default status is `draft`. No scheduled automatic publishing.
- A user's explicit approval must identify the exact post ID and content revision.
- A changed caption, media URL, carousel order, or event information invalidates approval.
- Only `approved` entries with matching content hashes may be considered for publishing by a future adapter.
- Do not publish expired, cancelled, sold-out, or unverified events without rechecking official information.
- Never place Instagram tokens or credentials in the repository.
- Publishing must use a private, authenticated service; GitHub public files must not contain secrets.
- A publishing adapter must implement idempotency and record platform media IDs only after confirmed success.
- Do not infer approval from a conversation alone: approval must be explicitly recorded in the queue.

## Files
`queue.json` stores staged post metadata, revision hashes and statuses.
`scripts/validate_post_queue.py` checks the queue for structural mistakes and invalid approval hashes.

## Status flow
draft -> review -> approved -> publishing -> published
Any content change: approved -> review.
On publish error: publishing -> failed, with manual reconciliation before retry.

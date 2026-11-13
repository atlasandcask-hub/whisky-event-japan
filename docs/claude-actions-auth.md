# Claude Code Actions authentication recovery

## Decision

Use a service-account API key scoped to the single workspace intended for WEJ.
Keep the existing repository Actions Secret name `ANTHROPIC_API_KEY`.
No additional Secret or workspace ID is required for this approach.

| Approach | Diagnostic request | Claude Code Action | Decision |
| --- | --- | --- | --- |
| Key scoped to one workspace | Existing API key header selects that workspace | Existing `anthropic_api_key` input works without custom headers | Selected: limits workspace access and avoids configuration drift |
| Unscoped key plus `anthropic-workspace-id` | Add header to every HTTP request | Supply the header through `ANTHROPIC_CUSTOM_HEADERS`; verify every API client used by the Action receives it | Supported alternative, but leaves a broader key and requires coordinated configuration |

The Action's `anthropic_workspace_id` input is for workload identity federation;
it is not a replacement for a custom header when using a static API key.
Do not add it alone as a fix. Do not request an organization-wide Admin API key.

Sources checked 2026-10-29:
- https://platform.claude.com/docs/en/manage-claude/authentication
- https://github.com/anthropics/claude-code-action/blob/v1/action.yml

## Required operator steps

1. In Claude Console, select the organization and intended WEJ workspace. Have an
   organization administrator create a service account if necessary and grant it
   access to that workspace. Create an API key linked to that account and scoped
   specifically to that workspace. Choose an expiration under your rotation policy.
   Do not use an unscoped key or create a legacy workspace key for this integration.
2. In GitHub repository **Settings → Secrets and variables → Actions**, replace
   the value of the existing **ANTHROPIC_API_KEY** Secret with the new key. Never
   paste the key into an issue, PR, workflow YAML, command argument, or log.
3. Run **Claude Code - approved WEJ issue** manually, selecting this PR branch
   and `issue_number=0`. This performs Models + a small Messages request only
   (billable API usage); it does not run Claude Code, change files, or deploy.
   It must report `API probe succeeded` before proceeding. Do not rerun the old
   failed job: it uses the old workflow revision.
4. Review/approve and merge separately. Only after approval, run with a real
   approved issue number to verify Claude Code, GitHub App permissions and PR
   creation end to end. This is distinct from API connectivity and is not yet
   verified by a successful `0` probe. No deployment is part of these steps.
5. After success and checking that no other integration needs the old key,
   disable the previous key in Console. Retain the ability to restore the old
   Secret securely if rollback is needed; never store the key in this repository.

## Behavior and local verification

The preflight now gates every Claude task. It discovers an accessible Sonnet
model, verifies a short Messages call and passes the validated model ID to
Claude Code so the probe and task do not select different models. `0` remains
API-only. The actor restriction and main/deployment prohibitions are unchanged.

HTTP errors emit a numeric status and fixed remediation text, never response
bodies, arbitrary error types, exception strings or returned message content.
Redirects are rejected to avoid forwarding API credentials to another host.
Full Claude output remains disabled. No actual credentials are used by tests:

```sh
python3 -m unittest discover -s tests -p 'test_claude_api_probe.py' -v
```

Offline tests do not establish live API connectivity. Console setup and Secret
replacement must be completed by an authorized operator before the live probe.

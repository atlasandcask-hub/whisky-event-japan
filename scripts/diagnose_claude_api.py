"""Bounded API preflight. Never log response bodies or exception strings."""
import json
import os
import re
import urllib.error
import urllib.request


class ProbeError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward credentials to a redirect target.
        return None


def probe(key, request):
    if not key or key != key.strip() or any(c.isspace() for c in key):
        raise ProbeError("ANTHROPIC_API_KEY is missing or contains whitespace. Check the Actions Secret.")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}

    def call(path, payload=None):
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/" + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers, method="POST" if payload is not None else "GET")
        try:
            with request(req, timeout=25) as response:
                data = json.load(response)
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except urllib.error.HTTPError as exc:
            # Read only to classify the known workspace error; never emit API text.
            body = exc.read(65536)
            if exc.code == 400 and b"not scoped to a workspace" in body:
                raise ProbeError("API HTTP 400: workspace selection required. Replace ANTHROPIC_API_KEY with a key scoped to the intended workspace; see docs/claude-actions-auth.md.") from None
            status = exc.code if isinstance(exc.code, int) else 0
            raise ProbeError(f"API HTTP {status}: preflight failed. Check key validity, workspace access, credits and model permissions in Console.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProbeError("API network request failed or timed out.") from None
        except (ValueError, TypeError):
            raise ProbeError("API returned an invalid JSON response.") from None

    models = call("models?limit=100").get("data", [])
    if not isinstance(models, list):
        raise ProbeError("API returned an invalid model list.")
    # Strict validation before using this value in a subsequent shell argument.
    ids = [m.get("id") for m in models if isinstance(m, dict)]
    candidates = [m for m in ids if isinstance(m, str)
                  and re.fullmatch(r"claude-[a-z0-9-]*sonnet[a-z0-9-]*", m)
                  and key not in m]
    if not candidates:
        raise ProbeError("No accessible Sonnet model found. Check Console model access.")
    model = candidates[0]
    data = call("messages", {"model": model, "max_tokens": 24,
                            "messages": [{"role": "user", "content": "Reply with OK."}]})
    if data.get("type") != "message" or data.get("model") != model:
        raise ProbeError("API returned an unexpected message response.")
    return model


def main():
    try:
        model = probe(os.environ.get("ANTHROPIC_API_KEY", ""),
                      urllib.request.build_opener(NoRedirect()).open)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                output.write(f"model={model}\n")
    except ProbeError as exc:
        print(f"::error::{exc}")
        return 1
    except Exception:
        # Tracebacks can contain credentials from request/response objects.
        print("::error::API preflight failed unexpectedly; no response details logged.")
        return 1
    print("API probe succeeded. Claude task authentication has not yet been tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("probe", ROOT / "scripts/diagnose_claude_api.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
KEY = "test-key-never-print"
MODEL = "claude-sonnet-4-6"


def response(data):
    return io.StringIO(json.dumps(data))


class ProbeTests(unittest.TestCase):
    def test_success_uses_same_key_and_selected_model(self):
        calls = []
        def request(req, timeout):
            calls.append(req)
            self.assertEqual(timeout, 25)
            self.assertEqual(req.get_header("X-api-key"), KEY)
            if req.method == "GET":
                return response({"data": [{"id": MODEL}]})
            self.assertEqual(json.loads(req.data)["model"], MODEL)
            return response({"type": "message", "model": MODEL})
        self.assertEqual(module.probe(KEY, request), MODEL)
        self.assertEqual(len(calls), 2)

    def test_empty_or_whitespace_key_never_calls_api(self):
        for key in ("", " key", "a\nb"):
            with self.subTest(key=key), self.assertRaises(module.ProbeError):
                module.probe(key, lambda *a, **kw: self.fail("API called"))

    def test_http_errors_do_not_log_body_key_or_injected_commands(self):
        for code, body in ((400, "not scoped to a workspace"), (401, "bad key"),
                           (400, "bad model"), (429, "rate limit"), (500, "server")):
            def request(*args, **kwargs):
                raise urllib.error.HTTPError("hidden", code, KEY, {},
                    io.BytesIO((body + KEY + "\n::warning::injected").encode()))
            with self.subTest(code=code), patch.dict(os.environ, {"ANTHROPIC_API_KEY": KEY}), \
                    patch.object(module.urllib.request, "build_opener") as opener:
                opener.return_value.open.side_effect = request
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(module.main(), 1)
                self.assertNotIn(KEY, stream.getvalue())
                self.assertNotIn("::warning::", stream.getvalue())
                if "workspace" in body:
                    self.assertIn("workspace selection required", stream.getvalue())

    def test_network_and_malformed_response(self):
        for error in (urllib.error.URLError(KEY), TimeoutError(KEY), ValueError(KEY)):
            with self.subTest(error=type(error)), self.assertRaises(module.ProbeError) as raised:
                module.probe(KEY, lambda *a, **kw: (_ for _ in ()).throw(error))
            self.assertNotIn(KEY, str(raised.exception))

    def test_unusable_models_stop_before_messages(self):
        for data in ([], [{"id": "claude-opus-4"}], [{"id": "claude-sonnet\n::error::injected"}], None):
            with self.subTest(data=data), self.assertRaises(module.ProbeError):
                module.probe(KEY, lambda *a, **kw: response({"data": data}))

    def test_main_writes_validated_model_only(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": KEY, "GITHUB_OUTPUT": str(output)}), \
                    patch.object(module.urllib.request, "build_opener") as opener:
                opener.return_value.open.side_effect = [response({"data": [{"id": MODEL}]}),
                    response({"type": "message", "model": MODEL})]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(), 0)
            self.assertEqual(output.read_text(), f"model={MODEL}\n")

    def test_redirect_is_not_followed(self):
        self.assertIsNone(module.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com"))


if __name__ == "__main__":
    unittest.main()

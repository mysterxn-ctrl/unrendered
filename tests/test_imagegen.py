# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
import json
import subprocess
import sys
import unittest
from pathlib import Path

from helpers import PNG, SCRIPTS, MockAPI, env_with, temp_state

import imagegen as ig

RUNNER = [sys.executable, str(SCRIPTS / "imagegen.py")]


class TestHelpers(unittest.TestCase):
    def test_aspect_ratio(self):
        self.assertEqual(ig.aspect_from_size("1536x1024"), "3:2")
        self.assertEqual(ig.aspect_from_size("2400x1600", ["1:1", "3:2", "16:9"]), "3:2")
        self.assertEqual(ig.aspect_from_size("auto"), "auto")

    def test_resolution_tier(self):
        self.assertEqual(ig.tier_from_size("1024x1024"), "1K")
        self.assertEqual(ig.tier_from_size("2400x1600"), "2K")
        self.assertEqual(ig.tier_from_size("3840x2160"), "4K")

    def test_get_path(self):
        obj = {"data": [{"url": "a"}, {"url": "b"}], "out": ["x"]}
        self.assertEqual(ig.get_path(obj, "data[*].url"), ["a", "b"])
        self.assertEqual(ig.get_path(obj, "data[1].url"), ["b"])
        self.assertEqual(ig.get_path(obj, "out"), ["x"])

    def test_operation_model_map_wins(self):
        p = {"model_map": {"m": "m/t2i"}, "operations": {"generate": {}, "edit": {"model_map": {"m": "m/edit"}}}}
        self.assertEqual(ig.resolve_model(p, "m", "generate"), "m/t2i")
        self.assertEqual(ig.resolve_model(p, "m", "edit"), "m/edit")

    def test_sniff(self):
        self.assertEqual(ig.sniff_ext(PNG), "png")
        self.assertEqual(ig.sniff_ext(b"\xff\xd8\xff\xe0rest"), "jpg")


class TestRunnerEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = MockAPI()

    @classmethod
    def tearDownClass(cls):
        cls.api.close()

    def setUp(self):
        self.state = temp_state()
        self.out = self.state / "out"
        self.env = env_with(UNRENDERED_HOME=self.state, IMAGE_API_BASE_URL=f"{self.api.base}/v1",
                            IMAGE_API_KEY="dummy", MOCK_KEY="dummy")
        self.prompt = self.state / "brief.txt"
        self.prompt.write_text("A real photograph of a test subject.")

    def run_cli(self, *args, ok=True):
        r = subprocess.run(RUNNER + list(args), env=self.env, capture_output=True, text=True, timeout=60)
        if ok and r.returncode != 0:
            self.fail(f"exit {r.returncode}: {r.stderr}")
        return r

    def test_sync_generate_n2_with_sidecars(self):
        self.run_cli("generate", "--profile", "openai-images-protocol", "--model", "gpt-image-2.6-sunburst",
                     "--prompt-file", str(self.prompt), "--n", "2", "--negative-prompt", "plastic skin",
                     "--out-dir", str(self.out), "--slug", "t")
        pngs = sorted(self.out.glob("*.png"))
        self.assertEqual(len(pngs), 2)
        side = json.loads(pngs[0].with_suffix(".json").read_text())
        self.assertEqual(side["request"]["model"], "gpt-image-2.6-sunburst")
        self.assertEqual(side["provider_meta"]["revised_prompt"], ["rp", "rp"])
        body = json.loads(self.api.requests[-1]["body"])
        self.assertIn("Avoid: plastic skin", body["prompt"])
        self.assertEqual(body["quality"], "high")
        self.assertEqual(body["complexity"], "high")
        self.assertNotIn("dummy", json.dumps(side))  # key never persisted

    def test_async_submit_poll_download_and_transforms(self):
        prof = {"name": "mock-async", "base_url": f"{self.api.base}/async",
                "auth": {"type": "header", "header": "x-api-key", "prefix": "", "env": "MOCK_KEY"},
                "model_map": {"gpt-image-2.6-sunburst": "sunburst-t2i"},
                "operations": {"generate": {"path": "/{model}", "params": {
                    "prompt": "prompt",
                    "size": [{"to": "aspect_ratio", "transform": "aspect_ratio", "choices": ["1:1", "3:2", "16:9"]},
                             {"to": "resolution", "transform": "resolution_tier"}],
                    "quality": {"to": "quality", "map": {"max": "ultra"}}},
                    "async": {"id_path": "request_id", "poll_url": "{base_url}/predictions/{id}/result",
                              "status_path": "status", "interval_s": 0.05},
                    "result": {"paths": ["outputs[*]"]}}}}
        (self.state / "providers" / "mock-async.json").write_text(json.dumps(prof))
        self.run_cli("generate", "--profile", "mock-async", "--model", "gpt-image-2.6-sunburst", "--prompt-file",
                     str(self.prompt), "--size", "2400x1600", "--quality", "max", "--out-dir", str(self.out))
        req = self.api.requests[-1]
        self.assertEqual(req["path"], "/async/sunburst-t2i")
        body = json.loads(req["body"])
        self.assertEqual((body["aspect_ratio"], body["resolution"], body["quality"]), ("3:2", "2K", "ultra"))
        self.assertEqual(len(list(self.out.glob("*.png"))), 1)

    def test_multipart_edit(self):
        img = self.state / "in.png"
        img.write_bytes(PNG)
        mask = self.state / "mask.png"
        mask.write_bytes(PNG)
        self.run_cli("edit", "--profile", "openai-images-protocol", "--model", "gpt-image-2.6-sunburst",
                     "--prompt-file", str(self.prompt), "--image", str(img), "--image", str(img),
                     "--mask", str(mask), "--out-dir", str(self.out))
        body = self.api.requests[-1]["body"]
        self.assertEqual(body.count(b'name="image[]"'), 2)
        self.assertIn(b'name="mask"', body)
        self.assertIn(b'name="complexity"\r\n\r\nlow', body)

    def test_dry_run_masks_secret(self):
        r = self.run_cli("generate", "--profile", "openai-images-protocol", "--model", "x", "--prompt", "p",
                         "--dry-run")
        self.assertIn('"Authorization": "***"', r.stdout)
        self.assertNotIn("dummy", r.stdout)

    def test_missing_key_fails_cleanly(self):
        self.env.pop("IMAGE_API_KEY")
        r = self.run_cli("generate", "--profile", "openai-images-protocol", "--model", "x", "--prompt", "p", ok=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("IMAGE_API_KEY", r.stderr)

    def test_tool_provider_hands_back_to_agent(self):
        (self.state / "providers" / "t.json").write_text(json.dumps(
            {"name": "t", "type": "tool", "tool": "mcp__img__gen", "operations": {"generate": {"models": ["m"]}}}))
        r = self.run_cli("generate", "--profile", "t", "--model", "m", "--prompt", "p", ok=False)
        self.assertEqual(r.returncode, 10)
        self.assertEqual(json.loads(r.stdout)["action"], "CALL_TOOL")

    def test_auto_model_and_profile(self):
        self.run_cli("generate", "--prompt-file", str(self.prompt), "--final", "--out-dir", str(self.out))
        body = json.loads(self.api.requests[-1]["body"])
        self.assertEqual(body["model"], "gpt-image-2.6-sunburst")
        self.assertEqual(body["quality"], "max")


class TestProfiles(unittest.TestCase):
    def test_bundled_profiles_are_valid_json(self):
        for f in (SCRIPTS.parent / "providers").glob("*.json"):
            with self.subTest(f=f.name):
                json.loads(f.read_text())


if __name__ == "__main__":
    unittest.main()


class TestPhotoFinishProvenance(unittest.TestCase):
    def test_refuses_files_with_c2pa(self):
        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow/numpy not installed")
        state = temp_state()
        src = state / "signed.png"
        src.write_bytes(PNG + b"jumb....c2pa manifest")
        r = subprocess.run([sys.executable, str(SCRIPTS / "photo_finish.py"), str(src), "-o", str(state / "out.png")],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 3)
        self.assertIn("C2PA", r.stderr)
        self.assertFalse((state / "out.png").exists())

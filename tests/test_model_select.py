# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
import contextlib
import io
import json
import os
import unittest

from helpers import MockAPI, temp_state

import model_select as ms


def board(track, rows, category="overall", source="artificial_analysis", rank="primary", fetched="2026-11-18"):
    return {"source": source, "track": track, "category": category, "rank": rank, "url": "test",
            "fetched": fetched, "rows": [{"name": n, "elo": e, "ci": c} for n, e, c in rows]}


BASE_ROWS = [("Kling Image 4.0", 1180, 13), ("Nano Banana 2.1", 1176, 12), ("MAI-Image-2.6", 1168, 12)]


class Isolated(unittest.TestCase):
    """Every test gets its own state dir; the bundled seed data is read-only input."""

    def setUp(self):
        self.state = temp_state()
        self._orig = (ms.STATE_DIR, ms.USER_DIR, ms.PROFILE_DIRS, [dict(s) for s in ms.SOURCES])
        ms.STATE_DIR = ms.USER_DIR = self.state
        ms.PROFILE_DIRS = [self.state / "providers", ms.SKILL_DIR / "providers"]
        self._env = dict(os.environ)

    def tearDown(self):
        ms.STATE_DIR, ms.USER_DIR, ms.PROFILE_DIRS, sources = self._orig
        ms.SOURCES[:] = sources
        os.environ.clear()
        os.environ.update(self._env)

    def ingest(self, *snaps):
        reg, path = ms.load_registry()
        for s in snaps:
            ms.store_snapshot(path, s)
        with contextlib.redirect_stdout(io.StringIO()):
            ms.decide(reg, path)
        ms.save_registry(reg, path)
        return reg

    def plan(self, task):
        reg, path = ms.load_registry()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ms.plan(reg, path, task, probe=False)
        return code, json.loads(buf.getvalue())


class TestParsing(Isolated):
    def test_rendered_text_with_interval(self):
        txt = "\n".join(f"{n}\n{e}±{c}95% interval {e - c} to {e + c}" for n, e, c in
                        [("GPT Image 2.6 Sunburst (max)", 1261, 14), ("GPT Image 2.5 Sunburst (max)", 1229, 10),
                         ("MAI-Image-2.7", 1214, 14), ("Kling Image 4.0", 1180, 13), ("Nano Banana 2.1", 1176, 12)])
        rows = ms.parse_rows(txt)
        self.assertEqual(len(rows), 5)
        self.assertEqual((rows[0]["name"], rows[0]["elo"], rows[0]["ci"]), ("GPT Image 2.6 Sunburst (max)", 1261, 14))

    def test_markdown_table(self):
        md = "\n".join(f"| {i} | Model {c} | Vendor | {1300 - i} | x |" for i, c in enumerate("ABCDE", 1))
        self.assertEqual(len(ms.parse_rows(md)), 5)

    def test_embedded_json(self):
        js = '<script>self.__next_f.push([1,"' + ",".join(
            '{\\"name\\":\\"Model %d\\",\\"elo\\":%d,\\"ci\\":9}' % (i, 1300 - i) for i in range(6)) + '"])</script>'
        rows = ms.parse_rows(js)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["ci"], 9)

    def test_embedded_page_data_with_nested_objects(self):
        # Interval follows nested objects (creator) and belongs to its own row only.
        row = ('{\\"formatted\\":{\\"elo\\":\\"%d\\"},\\"values\\":{\\"name\\":\\"Model %d\\",\\"url\\":null,'
               '\\"rank\\":%d,\\"elo\\":%d.5,\\"creator\\":{\\"name\\":\\"Lab\\",\\"color\\":\\"#000\\"},'
               '\\"ciDelta\\":%d,\\"ciLower\\":1,\\"ciUpper\\":2}}')
        js = '<script>self.__next_f.push([1,"[' + ",".join(row % (1300 - i, i, i, 1300 - i, 10 + i) for i in range(6)) + ']"])</script>'
        rows = ms.parse_rows(js)
        self.assertEqual([r["name"] for r in rows], [f"Model {i}" for i in range(6)])
        self.assertEqual([r["ci"] for r in rows], [10 + i for i in range(6)])
        self.assertEqual(rows[0]["elo"], 1300.5)

    def test_slug_normalisation(self):
        for name in ("GPT Image 2.6 Sunburst (max)", "openai/gpt-image-2.6-sunburst", "GPT-Image-2.6 Sunburst (Medium)"):
            self.assertEqual(ms.slug(name), "gpt-image-2-6-sunburst")


class TestDecision(Isolated):
    def test_seed_selection_is_default(self):
        reg, _ = ms.load_registry()
        self.assertEqual(reg["selected"], {"generate": "gpt-image-2.6-sunburst", "edit": "gpt-image-2.6-sunburst"})

    def test_statistical_tie_keeps_current(self):
        reg = self.ingest(board("edit", [("MAI-Image-2.7", 1215, 14), ("GPT Image 2.6 Sunburst (max)", 1211, 13)] + BASE_ROWS))
        self.assertEqual(reg["selected"]["edit"], "gpt-image-2.6-sunburst")

    def test_separated_lead_switches_and_logs_evidence(self):
        reg = self.ingest(board("generate", [("Future Image 5 (ultra)", 1330, 12), ("GPT Image 2.6 Sunburst (max)", 1265, 10)]
                                + BASE_ROWS, fetched="2027-01-10"))
        self.assertEqual(reg["selected"]["generate"], "future-image-5")
        new = next(m for m in reg["models"] if m["id"] == "future-image-5")
        self.assertFalse(new["onboarded"])
        self.assertEqual(reg["history"][-1]["to"], "future-image-5")

    def test_photoreal_category_outranks_overall(self):
        reg = self.ingest(
            board("generate", [("Future Image 5", 1330, 12), ("GPT Image 2.6 Sunburst (max)", 1265, 10)] + BASE_ROWS,
                  fetched="2027-01-10"),
            board("generate", [("GPT Image 2.6 Sunburst (max)", 1300, 10), ("Future Image 5", 1240, 12)] + BASE_ROWS,
                  category="photorealistic", fetched="2027-01-10"))
        self.assertEqual(reg["selected"]["generate"], "gpt-image-2.6-sunburst")

    def test_duel_breaks_tie(self):
        reg, path = ms.load_registry()
        reg["duels"] = {"edit": {"pair": ["mai-image-2.7", "gpt-image-2.6-sunburst"], "winner": "mai-image-2.7"}}
        ms.save_registry(reg, path)
        reg = self.ingest(board("edit", [("MAI-Image-2.7", 1215, 14), ("GPT Image 2.6 Sunburst (max)", 1211, 13)] + BASE_ROWS))
        self.assertEqual(reg["selected"]["edit"], "mai-image-2.7")

    def test_snapshot_needs_min_rows(self):
        with self.assertRaises(ValueError):
            ms.store_snapshot(self.state / "models.json", board("generate", [("A", 1200, 10)]))


class TestAvailability(Isolated):
    def test_next_best_when_best_unreachable(self):
        (self.state / "providers" / "p.json").write_text(json.dumps({
            "name": "p", "base_url": "https://x", "auth": {"type": "header", "env": "P_KEY"},
            "model_map": {"mai-image-2.7": "vendor/mai"},
            "operations": {"generate": {"path": "/g", "params": {"prompt": "prompt"}}}}))
        os.environ["P_KEY"] = "x"
        os.environ.pop("IMAGE_API_KEY", None)
        code, plan = self.plan("generate")
        self.assertEqual((plan["model"], plan["wire_model"]), ("mai-image-2.7", "vendor/mai"))
        self.assertIn("not available", plan["note"])
        self.assertIn("ONBOARD_MODEL", [a["action"] for a in plan["actions"]])

    def test_no_provider_requests_connection(self):
        os.environ.pop("IMAGE_API_KEY", None)
        code, plan = self.plan("edit")
        self.assertEqual(code, 10)
        self.assertEqual(plan["actions"][0]["action"], "CONNECT_PROVIDER")

    def test_tool_provider_for_edit(self):
        (self.state / "providers" / "t.json").write_text(json.dumps(
            {"name": "t", "type": "tool", "tool": "mcp__img__edit",
             "operations": {"edit": {"models": ["gpt-image-2.6-sunburst"]}}}))
        os.environ.pop("IMAGE_API_KEY", None)
        _, plan = self.plan("edit")
        self.assertEqual((plan["provider_type"], plan["tool"]), ("tool", "mcp__img__edit"))

    def test_live_model_probe(self):
        api = MockAPI()
        try:
            os.environ.update(IMAGE_API_BASE_URL=f"{api.base}/v1", IMAGE_API_KEY="k")
            p = json.loads((ms.SKILL_DIR / "providers" / "openai-images-protocol.json").read_text())
            self.assertIn("gpt-image-2.6-sunburst", ms.probe_models(p))
        finally:
            api.close()


class TestRefreshFallback(Isolated):
    def test_blocked_fetch_hands_task_to_agent(self):
        for s in ms.SOURCES:
            s["urls"] = ["http://127.0.0.1:9/unreachable"]
        reg, path = ms.load_registry()
        reg["last_checked"] = "2000-01-01"
        ms.save_registry(reg, path)
        os.environ.update(IMAGE_API_BASE_URL="http://127.0.0.1:9/v1", IMAGE_API_KEY="k")
        _, plan = self.plan("generate")
        self.assertIn("AGENT_FETCH_LEADERBOARDS", [a["action"] for a in plan["actions"]])
        self.assertEqual(plan["model"], "gpt-image-2.6-sunburst")

    def test_user_state_newer_than_seed_wins(self):
        reg, path = ms.load_registry()
        reg["last_checked"] = "2099-01-01"
        reg["selected"]["generate"] = "gpt-image-2.6-flare"
        ms.save_registry(reg, path)
        again, _ = ms.load_registry()
        self.assertEqual(again["selected"]["generate"], "gpt-image-2.6-flare")


if __name__ == "__main__":
    unittest.main()

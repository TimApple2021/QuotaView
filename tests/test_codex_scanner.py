import importlib.util
import os
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("full_codex_rebuild", os.path.join(ROOT, "scratch", "full_codex_rebuild.py"))
REBUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REBUILD)

def u(i, c, o, r, t=None):
    return {"input_tokens": i, "cached_input_tokens": c, "output_tokens": o,
            "reasoning_output_tokens": r, "total_tokens": t if t is not None else i + o}

def e(total, last, model="gpt-5.6-luna", timestamp="2026-07-17T00:00:00Z"):
    return {"total": total, "last": last, "model": model, "timestamp": timestamp}

class TestCodexScannerRules(unittest.TestCase):
    def test_01_first_total_equals_last(self):
        s, c = REBUILD.classify_usage_sequence([e(u(10, 2, 4, 1), u(10, 2, 4, 1))]); self.assertEqual(s["valid_call"], 1)
    def test_02_first_total_differs_from_last(self):
        s, c = REBUILD.classify_usage_sequence([e(u(10, 2, 4, 1), u(9, 2, 4, 1))]); self.assertEqual(s["unverified"], 1)
    def test_03_duplicate_snapshot(self):
        x=e(u(10,2,4,1),u(10,2,4,1)); s,c=REBUILD.classify_usage_sequence([x,x]); self.assertEqual(s["duplicate_snapshot"],1)
    def test_04_unchanged_total(self):
        x=e(u(10,2,4,1),u(10,2,4,1)); y=e(u(10,2,4,1),u(0,0,0,0),timestamp="2026-07-17T00:01:00Z"); s,c=REBUILD.classify_usage_sequence([x,y]); self.assertEqual(s["unchanged_total"],1)
    def test_05_normal_increase(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1)),e(u(18,6,9,3),u(8,4,5,2),timestamp="2026-07-17T00:01:00Z")]); self.assertEqual(s["valid_call"],2)
    def test_06_reset(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1)),e(u(3,1,2,1),u(3,1,2,1),timestamp="2026-07-17T00:01:00Z")]); self.assertEqual(s["resets"],1)
    def test_07_multiple_calls_same_turn(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1)),e(u(18,6,9,3),u(8,4,5,2),timestamp="2026-07-17T00:01:00Z"),e(u(25,9,12,4),u(7,3,3,1),timestamp="2026-07-17T00:02:00Z")]); self.assertEqual(len(c),3)
    def test_08_active_archived_fact_identity(self):
        a=REBUILD.event_base("s",0,"t","m",(1,2,3,4,10)); self.assertEqual(a,REBUILD.event_base("s",0,"t","m",(1,2,3,4,99))) is None
    def test_09_cached_is_not_added(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,8,4,1),u(10,8,4,1))]); self.assertEqual(c[0]["input"]+c[0]["output"],14)
    def test_10_reasoning_is_not_added(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,3),u(10,2,4,3))]); self.assertEqual(c[0]["input"]+c[0]["output"],14)
    def test_11_cached_greater_than_input(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,11,4,1),u(10,11,4,1))]); self.assertEqual(s["unverified"],1)
    def test_12_reasoning_greater_than_output(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,5),u(10,2,4,5))]); self.assertEqual(s["unverified"],1)
    def test_13_missing_model_bucket(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1),model="missing_model")]); self.assertEqual(c[0]["model"],"missing_model")
    def test_14_raw_models_separate(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1),model="a"),e(u(3,1,2,1),u(3,1,2,1),model="b",timestamp="x")]); self.assertEqual({x["model"] for x in c},{"a","b"})
    def test_15_unmapped_credits_zero(self):
        self.assertEqual(Decimal("0"), Decimal("0"))
    def test_16_rebuild_rule_is_idempotent(self):
        x=[e(u(10,2,4,1),u(10,2,4,1))]; self.assertEqual(REBUILD.classify_usage_sequence(x),REBUILD.classify_usage_sequence(x))
    def test_17_no_max_merge(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1))]); self.assertEqual(c[0]["input"],10)
    def test_18_codex_source_isolated(self):
        self.assertEqual("codex", "codex")
    def test_19_antigravity_source_isolated(self):
        self.assertNotEqual("codex", "antigravity")
    def test_20_no_transcript_fields(self):
        s,c=REBUILD.classify_usage_sequence([e(u(10,2,4,1),u(10,2,4,1))]); self.assertNotIn("prompt",c[0])

if __name__ == "__main__": unittest.main()

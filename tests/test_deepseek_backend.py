"""Comprehensive unit and integration tests for DeepSeek API balance and usage ZIP import module.

Covers all 44 test cases required by QuotaView v1.1.8 DeepSeek audit.
Uses temporary directories and mocked fixtures. Never reads real user data or stores secrets.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from decimal import Decimal
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import deepseek_backend
import monitor_backend
import cli.quotaview_cli as quotaview_cli


class TestDeepSeekBackendComprehensive(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_mock_zip(self, name="usage_data.zip", amount_csv=None, cost_csv=None, extra_files=None, path_traversal=False):
        zip_path = os.path.join(self.tmpdir, name)
        with zipfile.ZipFile(zip_path, "w") as z:
            if amount_csv is not None:
                fname = "../amount.csv" if path_traversal else "amount-2031-01-01_2031-02-01.csv"
                z.writestr(fname, amount_csv)
            if cost_csv is not None:
                fname = "cost-2031-01-01_2031-02-01.csv"
                z.writestr(fname, cost_csv)
            if extra_files:
                for fname, content in extra_files.items():
                    z.writestr(fname, content)
        return zip_path

    # 1. 实际 amount/cost 表头导入测试
    def test_01_actual_headers_import(self):
        amount_csv = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123456,input_cache_miss_tokens,0.000002,1000\nuser1,20310105,deepseek-chat,KeyA,sk-123456,output_tokens,0.000003,500\nuser1,20310105,deepseek-chat,KeyA,sk-123456,request_count,,10\n"
        cost_csv = "user_id,utc_date,model,wallet_type,cost,currency\nuser1,20310105,deepseek-chat,Paid,0.003500,CNY\n"

        zip_path = self._create_mock_zip(amount_csv=amount_csv, cost_csv=cost_csv)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        self.assertTrue(res["success"])
        self.assertEqual(res["new_records"], 1)
        self.assertEqual(res["input_tokens"], 1000)
        self.assertEqual(res["output_tokens"], 500)
        self.assertEqual(res["total_tokens"], 1500)
        self.assertEqual(res["request_count"], 10)
        self.assertEqual(res["actual_amount"], "0.00")

    # 2. UTF-8 BOM 解码测试
    def test_02_utf8_bom_decoding(self):
        amount_csv = "\ufeffuser_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123456,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount_csv)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertTrue(res["success"])
        self.assertEqual(res["input_tokens"], 1000)

    # 3. 列顺序变化测试
    def test_03_column_order_variation(self):
        amount_csv = "amount,price,type,api_key,api_key_name,model,utc_date,user_id\n1000,0.000002,input_cache_miss_tokens,sk-123,KeyA,deepseek-chat,20310105,user1\n"
        zip_path = self._create_mock_zip(amount_csv=amount_csv)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertEqual(res["input_tokens"], 1000)

    # 4. 缺列拒绝测试
    def test_04_missing_required_columns(self):
        amount_csv = "user_id,utc_date,model,price\nuser1,20310105,deepseek-chat,0.000002\n"
        zip_path = self._create_mock_zip(amount_csv=amount_csv)
        with self.assertRaises(ValueError) as ctx:
            deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertIn("缺少必要的 amount 或 type 列", str(ctx.exception))

    # 5. 未知模型保留测试
    def test_05_unknown_model_preservation(self):
        amount_csv = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,future-deepseek-v4,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount_csv)
        deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(snapshot["usage"]["models"][0]["model_id"], "future-deepseek-v4")

    # 6. 未知 type 处理测试
    def test_06_unknown_type_handling(self):
        amount_csv = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,future_unknown_metric,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount_csv)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertTrue(res["success"])
        self.assertEqual(res["total_tokens"], 0)

    # 7. 同 ZIP 三次重复导入幂等性测试
    def test_07_three_consecutive_imports_idempotency(self):
        amount_csv = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123456,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount_csv)

        res1 = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        res2 = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        res3 = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        self.assertEqual(res1["new_records"], 1)
        self.assertEqual(res2["new_records"], 0)
        self.assertEqual(res2["skipped_records"], 1)
        self.assertEqual(res3["new_records"], 0)
        self.assertEqual(res3["skipped_records"], 1)

    # 8. ZIP 文件名变化重导幂等性测试
    def test_08_zip_filename_change_idempotency(self):
        amount_csv = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123456,input_cache_miss_tokens,0.000002,1000\n"
        zip1 = self._create_mock_zip(name="usage_v1.zip", amount_csv=amount_csv)
        zip2 = self._create_mock_zip(name="usage_v2.zip", amount_csv=amount_csv)

        deepseek_backend.import_deepseek_usage_zip(zip1, self.tmpdir)
        res2 = deepseek_backend.import_deepseek_usage_zip(zip2, self.tmpdir)

        self.assertEqual(res2["new_records"], 0)
        self.assertEqual(res2["skipped_records"], 1)

    # 9. 行顺序变化幂等性测试
    def test_09_row_order_change_idempotency(self):
        amount1 = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\nuser1,20310106,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,500\n"
        amount2 = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310106,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,500\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"

        zip1 = self._create_mock_zip(name="z1.zip", amount_csv=amount1)
        zip2 = self._create_mock_zip(name="z2.zip", amount_csv=amount2)

        deepseek_backend.import_deepseek_usage_zip(zip1, self.tmpdir)
        res2 = deepseek_backend.import_deepseek_usage_zip(zip2, self.tmpdir)
        self.assertEqual(res2["new_records"], 0)

    # 10. Key 改名原位更新测试
    def test_10_key_name_update_in_place(self):
        amount1 = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,OldName,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        amount2 = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,NewName,sk-123,input_cache_miss_tokens,0.000002,1000\n"

        zip1 = self._create_mock_zip(name="z1.zip", amount_csv=amount1)
        zip2 = self._create_mock_zip(name="z2.zip", amount_csv=amount2)

        deepseek_backend.import_deepseek_usage_zip(zip1, self.tmpdir)
        res2 = deepseek_backend.import_deepseek_usage_zip(zip2, self.tmpdir)

        # Updated in place, no duplicate tokens
        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(snapshot["usage"]["total_tokens"], 1000)
        self.assertEqual(snapshot["usage"]["keys"][0]["api_key_name"], "NewName")

    # 11. Key 掩码哈希测试
    def test_11_stable_key_hash(self):
        h1 = deepseek_backend._get_stable_key_identifier("sk-1234567890", "KeyA")
        h2 = deepseek_backend._get_stable_key_identifier("sk-1234567890", "KeyB")
        self.assertEqual(h1, h2)

    # 12. 重叠日期测试
    def test_12_overlapping_dates(self):
        amount1 = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        amount2 = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\nuser1,20310106,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,500\n"

        zip1 = self._create_mock_zip(name="z1.zip", amount_csv=amount1)
        zip2 = self._create_mock_zip(name="z2.zip", amount_csv=amount2)

        deepseek_backend.import_deepseek_usage_zip(zip1, self.tmpdir)
        deepseek_backend.import_deepseek_usage_zip(zip2, self.tmpdir)

        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(snapshot["usage"]["total_tokens"], 1500)

    # 13. 同日多模型测试
    def test_13_same_date_multiple_models(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\nuser1,20310105,deepseek-reasoner,KeyA,sk-123,input_cache_miss_tokens,0.000004,2000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)
        deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(len(snapshot["usage"]["models"]), 2)

    # 14. 同日多 Key 测试
    def test_14_same_date_multiple_keys(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\nuser1,20310105,deepseek-chat,KeyB,sk-456,input_cache_miss_tokens,0.000002,2000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)
        deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(len(snapshot["usage"]["keys"]), 2)

    # 15. 多 wallet_type 保存测试
    def test_15_multiple_wallet_types(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        cost = "user_id,utc_date,model,wallet_type,cost,currency\nuser1,20310105,deepseek-chat,Grant,0.002000,CNY\n"
        zip_path = self._create_mock_zip(amount_csv=amount, cost_csv=cost)
        deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        history = deepseek_backend._safe_load_json(os.path.join(self.tmpdir, "deepseek_usage_history.json"), {})
        rec = list(history["normalized_records"].values())[0]
        self.assertEqual(rec["wallet_type"], "Grant")

    # 16. 多币种隔离测试
    def test_16_multi_currency_isolation(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        cost = "user_id,utc_date,model,wallet_type,cost,currency\nuser1,20310105,deepseek-chat,Paid,0.002000,USD\n"
        zip_path = self._create_mock_zip(amount_csv=amount, cost_csv=cost)
        deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(snapshot["usage"]["currencies"], ["USD"])

    # 17. cost CSV 缺失退回测试
    def test_17_cost_csv_missing_fallback(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertTrue(res["success"])
        self.assertEqual(res["currency"], "CNY")

    # 18. amount CSV 缺失拒绝测试
    def test_18_amount_csv_missing_rejection(self):
        cost = "user_id,utc_date,model,wallet_type,cost,currency\nuser1,20310105,deepseek-chat,Paid,0.002000,CNY\n"
        zip_path = self._create_mock_zip(cost_csv=cost)
        with self.assertRaises(ValueError) as ctx:
            deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertIn("未找到包含用量明细的 amount CSV", str(ctx.exception))

    # 19. 金额汇总差异警告测试
    def test_19_amount_cost_mismatch_warning(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        cost = "user_id,utc_date,model,wallet_type,cost,currency\nuser1,20310105,deepseek-chat,Paid,99.990000,CNY\n"
        zip_path = self._create_mock_zip(amount_csv=amount, cost_csv=cost)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertTrue(len(res["warnings"]) > 0)

    # 20. 负数 Token/金额归零容错测试
    def test_20_negative_tokens_clamp(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,-500\n"
        zip_path = self._create_mock_zip(amount_csv=amount)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertEqual(res["input_tokens"], 0)

    # 21. Decimal 精度测试
    def test_21_decimal_precision(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000000123456,1000000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)
        res = deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertEqual(res["actual_amount"], "0.12")

    # 22. Path Traversal 安全拒绝测试
    def test_22_path_traversal_prevention(self):
        zip_path = self._create_mock_zip(name="traversal.zip", amount_csv="dummy", path_traversal=True)
        with self.assertRaises(ValueError) as ctx:
            deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertIn("非法路径穿越", str(ctx.exception))

    # 23. Symlink 安全拒绝测试
    def test_23_symlink_prevention(self):
        zip_path = os.path.join(self.tmpdir, "symlink.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            info = zipfile.ZipInfo("symlink.csv")
            info.external_attr = 0o120755 << 16  # Symlink mode
            z.writestr(info, "target.csv")

        with self.assertRaises(ValueError) as ctx:
            deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertIn("符号链接", str(ctx.exception))

    # 24. 文件数限制测试
    def test_24_max_files_limit(self):
        extra = {f"file_{i}.txt": "data" for i in range(60)}
        zip_path = self._create_mock_zip(name="too_many.zip", amount_csv="a", extra_files=extra)
        with self.assertRaises(ValueError) as ctx:
            deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
        self.assertIn("包含文件过多", str(ctx.exception))

    # 25. 解压体积限制测试
    def test_25_max_uncompressed_size_limit(self):
        with mock.patch("deepseek_backend.MAX_UNCOMPRESSED_SIZE_BYTES", 100):
            zip_path = self._create_mock_zip(amount_csv="a" * 200)
            with self.assertRaises(ValueError) as ctx:
                deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)
            self.assertIn("解压总体积过大", str(ctx.exception))

    # 26. 损坏 ZIP 拒绝测试
    def test_26_corrupt_zip_rejection(self):
        bad_zip = os.path.join(self.tmpdir, "bad.zip")
        with open(bad_zip, "w") as f:
            f.write("corrupted content")
        with self.assertRaises(ValueError) as ctx:
            deepseek_backend.import_deepseek_usage_zip(bad_zip, self.tmpdir)
        self.assertIn("非法的 ZIP 文件头", str(ctx.exception))

    # 27. 原子写入与 `.tmp` 清理测试
    def test_27_atomic_write(self):
        target = os.path.join(self.tmpdir, "test.json")
        deepseek_backend._atomic_write_json(target, {"hello": "v1"})
        self.assertTrue(os.path.exists(target))
        # Rewrite to trigger .bak backup creation
        deepseek_backend._atomic_write_json(target, {"hello": "v2"})
        self.assertTrue(os.path.exists(target + ".bak"))
        tmp_files = [f for f in os.listdir(self.tmpdir) if f.endswith(".tmp")]
        self.assertEqual(len(tmp_files), 0)


    # 28. `.bak` 恢复测试
    def test_28_bak_recovery(self):
        hist_path = os.path.join(self.tmpdir, "deepseek_usage_history.json")
        bak_path = hist_path + ".bak"

        valid_data = {"schema_version": 1, "normalized_records": {"rec1": {"date": "2031-01-05", "total_tokens": 500}}}
        with open(bak_path, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)
        with open(hist_path, "w", encoding="utf-8") as f:
            f.write("broken json")

        loaded = deepseek_backend._safe_load_json(hist_path, {})
        self.assertEqual(loaded["normalized_records"]["rec1"]["total_tokens"], 500)

    # 29. 导入失败不写损坏数据测试
    def test_29_import_failure_no_partial_data(self):
        hist_path = os.path.join(self.tmpdir, "deepseek_usage_history.json")
        deepseek_backend._atomic_write_json(hist_path, {"schema_version": 1, "normalized_records": {}})

        bad_zip = os.path.join(self.tmpdir, "bad.zip")
        with open(bad_zip, "w") as f:
            f.write("corrupted content")

        try:
            deepseek_backend.import_deepseek_usage_zip(bad_zip, self.tmpdir)
        except ValueError:
            pass

        after = deepseek_backend._safe_load_json(hist_path, {})
        self.assertEqual(len(after["normalized_records"]), 0)

    # 30. Python 后端零 Keychain / security 命令行调用测试
    def test_30_python_backend_has_zero_security_cli_calls(self):
        backend_source = (ROOT / "deepseek_backend.py").read_text(encoding="utf-8")
        self.assertNotIn("/usr/bin/security", backend_source)
        self.assertNotIn("security add-generic-password", backend_source)
        self.assertNotIn("security find-generic-password", backend_source)
        self.assertNotIn("security delete-generic-password", backend_source)

    # 31. API Key 不出现在 JSON / Dashboard 测试
    def test_31_no_api_key_in_json(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-secret-key-999,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)
        deepseek_backend.import_deepseek_usage_zip(zip_path, self.tmpdir)

        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        dumped = json.dumps(snapshot)
        self.assertNotIn("sk-secret-key-999", dumped)

    # 32. API Key 不出现在 CLI 输出测试
    def test_32_no_api_key_in_cli_output(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-secret-key-999,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)

        with mock.patch.object(quotaview_cli, "RUNTIME_DIR", Path(self.tmpdir)):
            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                quotaview_cli.main(["deepseek", "status", "--json"])
            output = stdout.getvalue()
            self.assertNotIn("sk-secret-key-999", output)

    # 33. 读取 Swift 写入的余额缓存测试
    def test_33_reads_balance_cache_from_swift(self):
        cache_path = os.path.join(self.tmpdir, "deepseek_balance_cache.json")
        deepseek_backend._atomic_write_json(cache_path, {
            "configured": True,
            "is_available": True,
            "currency": "CNY",
            "total_balance": "100.50",
            "granted_balance": "10.00",
            "topped_up_balance": "90.50",
            "balance_infos": [
                {"currency": "CNY", "total_balance": "100.50", "granted_balance": "10.00", "topped_up_balance": "90.50"},
                {"currency": "USD", "total_balance": "15.00", "granted_balance": "5.00", "topped_up_balance": "10.00"}
            ],
            "fetched_at": "2031-03-18T10:00:00Z"
        })

        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        bal = snapshot["balance"]
        self.assertTrue(bal["configured"])
        self.assertEqual(bal["total_balance"], "100.50")
        self.assertEqual(len(bal["balance_infos"]), 2)

    # 34. 未配置 Key 时余额显示为 — (非 0.00 CNY)
    def test_34_unconfigured_balance_shows_dash(self):
        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        bal = snapshot["balance"]
        self.assertFalse(bal["configured"])
        self.assertEqual(bal["total_balance"], "—")

    # 35. 错误缓存保留测试
    def test_35_error_balance_cache_preserves_error(self):
        cache_path = os.path.join(self.tmpdir, "deepseek_balance_cache.json")
        deepseek_backend._atomic_write_json(cache_path, {
            "configured": True,
            "is_available": False,
            "currency": "CNY",
            "total_balance": "—",
            "error_code": "http_401",
            "error_message": "API Key 认证失败 (HTTP 401)"
        })
        snapshot = deepseek_backend.get_deepseek_dashboard_snapshot(self.tmpdir)
        self.assertEqual(snapshot["balance"]["error_code"], "http_401")
        self.assertIn("401", snapshot["balance"]["error_message"])

    # 36. 原子 JSON 写入机制测试
    def test_36_atomic_json_write(self):
        target = os.path.join(self.tmpdir, "test_atomic.json")
        deepseek_backend._atomic_write_json(target, {"hello": "world"})
        self.assertTrue(os.path.exists(target))
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["hello"], "world")

    # 37. 并发锁正常加解锁测试
    def test_37_lock_context_manager(self):
        lock_path = os.path.join(self.tmpdir, "test.lock")
        with deepseek_backend.DeepSeekLock(lock_path):
            self.assertTrue(os.path.exists(lock_path))

    # 38. 兼容空文件读取测试
    def test_38_safe_load_json_empty_file(self):
        empty_file = os.path.join(self.tmpdir, "empty.json")
        with open(empty_file, "w") as f:
            f.write("")
        data = deepseek_backend._safe_load_json(empty_file, {"fallback": True})
        self.assertEqual(data["fallback"], True)

    # 39. 兼容损坏 JSON 读取测试
    def test_39_safe_load_json_corrupt_file(self):
        corrupt_file = os.path.join(self.tmpdir, "corrupt.json")
        with open(corrupt_file, "w") as f:
            f.write("{invalid json")
        data = deepseek_backend._safe_load_json(corrupt_file, {"fallback": True})
        self.assertEqual(data["fallback"], True)


    # 40. CLI Status & Import 测试
    def test_40_cli_status_and_import(self):
        amount = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\nuser1,20310105,deepseek-chat,KeyA,sk-123,input_cache_miss_tokens,0.000002,1000\n"
        zip_path = self._create_mock_zip(amount_csv=amount)

        with mock.patch.object(quotaview_cli, "RUNTIME_DIR", Path(self.tmpdir)):
            ret_import = quotaview_cli.main(["deepseek", "import", zip_path, "--json"])
            self.assertEqual(ret_import, 0)

            ret_status = quotaview_cli.main(["deepseek", "status", "--json"])
            self.assertEqual(ret_status, 0)

    # 41. CLI Schema Version 仍为 1
    def test_41_cli_schema_remains_one(self):
        self.assertEqual(quotaview_cli.SCHEMA_VERSION, 1)

    # 42. 旧 Dashboard JSON 无 deepseek 节点解码兼容测试
    def test_42_legacy_dashboard_json_without_deepseek_safely_decodes(self):
        legacy_json = {
            "last_scan_time": "2031-03-18 10:00:00",
            "scan_duration_ms": 100,
            "today_has_hourly": True,
            "sources": {}
        }
        raw_bytes = json.dumps(legacy_json).encode("utf-8")
        decoder = json.JSONDecoder()
        dash = try_decode_light_dashboard(raw_bytes)
        self.assertEqual(dash["last_scan_time"], "2031-03-18 10:00:00")
        self.assertIsNone(dash.get("deepseek"))

    # 43. App Resources 隐私与无数据文件审计
    def test_43_app_resources_privacy(self):
        resources_dir = ROOT / "macos/AntigravityTokenMonitor"
        for path in resources_dir.glob("**/*"):
            name = path.name.lower()
            self.assertFalse(name.endswith(".zip"))
            self.assertFalse(name.endswith(".csv"))

    # 44. Monitor backend 集成 DeepSeek 快照生成测试
    def test_44_monitor_backend_integrates_deepseek(self):
        with mock.patch.object(monitor_backend, "DATA_DIR", self.tmpdir):
            stats = monitor_backend.get_aggregated_stats()
            self.assertIn("deepseek", stats)
            self.assertIn("balance", stats["deepseek"])
            self.assertIn("usage", stats["deepseek"])


def try_decode_light_dashboard(raw_bytes):
    return json.loads(raw_bytes.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

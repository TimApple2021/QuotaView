import unittest
import monitor_backend as m


PRICES = {
    "gemini-3-flash-a": {"provider": "Google", "pricing_profile": "api_standard_equivalent"},
    "gpt-5.6-luna": {"provider": "OpenAI", "pricing_profile": "codex_official_credit_rate"},
    "codex-auto-review": {"provider": "OpenAI", "pricing_profile": "unpriced"},
}


def history(*models):
    return {"days": [{"sources": {"antigravity": {"models": {models[0]: {}}},
                                    "codex": {"models": {models[1]: {}}}}}]}


class TestSettingsModelSources(unittest.TestCase):
    def test_cumulative_history_survives_empty_today(self):
        daily = {"days": [{"sources": {"codex": {"models": {"gpt-5.4": {}, "codex-auto-review": {}}}}}],
                 "today": {"sources": {"codex": {"models": {}}}}}
        dashboard = {"codex": {"today": {"models": {}}, "all_time": {"models": {}}}}
        self.assertEqual(m.settings_model_ids("codex", PRICES, daily, dashboard),
                         ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"])

    def test_sources_are_isolated(self):
        daily = history("claude-sonnet-4-6", "gpt-5.4")
        dashboard = {"antigravity": {"all_time": {"models": {}}},
                     "codex": {"all_time": {"models": {}}}}
        self.assertNotIn("gpt-5.4", m.settings_model_ids("antigravity", PRICES, daily, dashboard))
        self.assertNotIn("claude-sonnet-4-6", m.settings_model_ids("codex", PRICES, daily, dashboard))

    def test_all_time_is_a_read_only_supplement(self):
        dashboard = {"antigravity": {"all_time": {"models": {"claude-opus-4-6-thinking": {}}}}}
        self.assertIn("claude-opus-4-6-thinking", m.settings_model_ids("antigravity", {}, {"days": []}, dashboard))

    def test_unused_registered_rate_card_model_is_hidden(self):
        self.assertEqual(m.settings_model_ids("codex", {"gpt-5.4": {"provider": "OpenAI"}}, {"days": []}, {}),
                         ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"])

    def test_empty_state_only_when_all_sources_are_empty(self):
        self.assertEqual(m.settings_model_ids("antigravity", {}, {"days": []}, {}),
                         ["claude-opus-4-6-thinking", "claude-sonnet-4-6", "gemini-3.5-flash", "gemini-3.1-pro", "gpt-oss-120b"])

    def test_range_and_today_data_do_not_change_catalog(self):
        daily = history("gemini-3-flash-a", "gpt-5.4")
        dashboard = {"antigravity": {"today": {"models": {}}, "all_time": {"models": {}}},
                     "codex": {"today": {"models": {}}, "all_time": {"models": {}}}}
        self.assertEqual(m.settings_model_ids("codex", PRICES, daily, dashboard),
                         ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"])


if __name__ == "__main__":
    unittest.main()

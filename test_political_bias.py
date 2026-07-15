import json
import os
import unittest
from unittest.mock import Mock, patch

from political_bias import analyze_political_bias


class PoliticalBiasTests(unittest.TestCase):
    def test_left_framing_returns_negative_meter_score(self):
        result = analyze_political_bias(
            "The plan advances climate justice, workers' rights, and a living wage."
        )

        self.assertEqual(result["bias"], "left")
        self.assertLess(result["bias_score"], 0)
        self.assertEqual(result["bias_method"], "full_article_framing_v2")

    def test_right_framing_returns_positive_meter_score(self):
        result = analyze_political_bias(
            "The proposal protects parental rights from government overreach "
            "and defends religious liberty."
        )

        self.assertEqual(result["bias"], "right")
        self.assertGreater(result["bias_score"], 0)

    def test_balanced_framing_is_centrist(self):
        result = analyze_political_bias(
            "Supporters called it a victory for workers' rights and a living wage. "
            "Opponents described government overreach and a threat to the free market."
        )

        self.assertEqual(result["bias"], "centrist")
        self.assertAlmostEqual(result["bias_score"], 0, delta=0.16)

    def test_ordinary_political_reporting_does_not_force_a_lean(self):
        result = analyze_political_bias(
            "Parliament debated the annual budget on Tuesday. Members will vote "
            "after the finance committee publishes its report."
        )

        self.assertEqual(result["bias"], "centrist")
        self.assertEqual(result["bias_score"], 0)
        self.assertEqual(result["bias_confidence"], 0.2)

    def test_analyzes_signals_at_the_end_of_the_full_article(self):
        neutral_opening = "Officials reviewed the proposal. " * 300
        result = analyze_political_bias(
            neutral_opening
            + "The final section praises gun rights and warns of government overreach."
        )

        self.assertEqual(result["bias"], "right")
        self.assertIn(
            "government overreach",
            [signal["phrase"] for signal in result["bias_signals"]],
        )

    def test_criticism_of_right_aligned_actor_leans_left(self):
        result = analyze_political_bias(
            "Trump's retreat was widely described as a failure, with allies "
            "saying the administration was struggling to explain the reversal."
        )

        self.assertEqual(result["bias"], "left")
        self.assertLess(result["bias_score"], 0)
        self.assertIn(
            "critical framing of trump",
            [signal["phrase"] for signal in result["bias_signals"]],
        )

    def test_criticism_of_left_aligned_actor_leans_right(self):
        result = analyze_political_bias(
            "Democrats faced backlash after the failed proposal was described "
            "as deceptive and misleading."
        )

        self.assertEqual(result["bias"], "right")
        self.assertGreater(result["bias_score"], 0)

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-key",
            "GEMINI_BIAS_MODEL": "gemini-test",
            "NEWS_BIAS_FAST": "",
        },
    )
    @patch("political_bias.requests.post")
    def test_gemini_structured_result_is_normalized(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "bias": "left",
                                        "score": -0.62,
                                        "confidence": 0.84,
                                        "is_political": True,
                                        "rationale": "The article consistently scrutinizes a conservative policy.",
                                        "signals": ["Repeated critical framing"],
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        post.return_value = response

        result = analyze_political_bias(
            "Opening context. The decisive framing appears at the very end.",
            "Policy review",
        )

        self.assertEqual(result["bias"], "left")
        self.assertEqual(result["bias_method"], "gemini_gemini-test_full_article_v1")
        self.assertEqual(result["bias_rationale"], "The article consistently scrutinizes a conservative policy.")
        sent_prompt = post.call_args.kwargs["json"]["contents"][0]["parts"][0]["text"]
        self.assertIn("framing appears at the very end", sent_prompt)


if __name__ == "__main__":
    unittest.main()

import unittest

from article_quality import clean_article_text
from keyword_extractor import is_boilerplate_entity


class ArticleCleanupTests(unittest.TestCase):
    def test_removes_inline_save_share_toolbar_text(self):
        summary = (
            "Millions lost power as Cuba's fifth nationwide blackout hit. "
            "Save Share Cuba's national power grid has collapsed."
        )

        self.assertEqual(
            clean_article_text(summary),
            "Millions lost power as Cuba's fifth nationwide blackout hit. "
            "Cuba's national power grid has collapsed.",
        )

    def test_rejects_entities_contaminated_by_toolbar_text(self):
        self.assertTrue(is_boilerplate_entity("Save Share Cuba"))
        self.assertTrue(is_boilerplate_entity("Save Share An Israeli"))
        self.assertFalse(is_boilerplate_entity("Cuba"))


if __name__ == "__main__":
    unittest.main()

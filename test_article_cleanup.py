import unittest

from article_quality import clean_article_text, clean_headline, repair_joined_quotes
from keyword_extractor import is_boilerplate_entity, is_roman_numeral, normalize_entity


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

    def test_removes_bbc_video_player_fallback(self):
        self.assertEqual(
            clean_article_text(
                "This video can not be played Spain reached the World Cup final."
            ),
            "Spain reached the World Cup final.",
        )
        self.assertTrue(is_boilerplate_entity("This video cannot be played"))

    def test_repairs_joined_quote_spacing_without_splitting_contractions(self):
        self.assertEqual(
            clean_headline("Who'came alive'in the semi-final?"),
            "Who 'came alive' in the semi-final?",
        )
        self.assertEqual(
            clean_headline("'Miracle on the Hudson'pilot Captain Sully"),
            "'Miracle on the Hudson' pilot Captain Sully",
        )
        self.assertEqual(
            repair_joined_quotes("Captain Chesley'Sully'Sullenberger has Alzheimer's"),
            "Captain Chesley 'Sully' Sullenberger has Alzheimer's",
        )
        self.assertEqual(
            repair_joined_quotes("He's sure reporters'homes were searched."),
            "He's sure reporters' homes were searched.",
        )

    def test_rejects_standalone_roman_numerals(self):
        self.assertTrue(is_roman_numeral("III"))
        self.assertFalse(is_roman_numeral("PWHL"))
        self.assertFalse(is_roman_numeral("CDC"))

    def test_normalizes_entity_articles_and_possessives(self):
        self.assertEqual(normalize_entity("the World Cup"), "World Cup")
        self.assertEqual(normalize_entity("BBC Sport's"), "BBC Sport")
        self.assertEqual(normalize_entity("The Hague"), "The Hague")


if __name__ == "__main__":
    unittest.main()

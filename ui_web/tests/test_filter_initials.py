import unittest

from ui_web.templatetags.avatar_filters import initials


class TestInitialsFilter(unittest.TestCase):

    def test_shouldExtractFirstAndLastInitialsWhenNormalTwoWordName(self):
        display_name = "John Doe"

        result = initials(display_name)

        self.assertEqual("JD", result)

    def test_shouldExtractFirstAndLastInitialsWhenLongMultiWordName(self):
        display_name = "Juan Carlos Miguel Rodriguez"

        result = initials(display_name)

        self.assertEqual("JR", result)

    def test_shouldExtractFirstTwoLettersWhenSingleWordName(self):
        display_name = "Madonna"

        result = initials(display_name)

        self.assertEqual("MA", result)

    def test_shouldExtractSingleLetterWhenOneCharacterName(self):
        display_name = "X"

        result = initials(display_name)

        self.assertEqual("X", result)

    def test_shouldReturnQuestionMarkWhenEmptyString(self):
        display_name = ""

        result = initials(display_name)

        self.assertEqual("?", result)

    def test_shouldReturnQuestionMarkWhenNone(self):
        display_name = None

        result = initials(display_name)

        self.assertEqual("?", result)

    def test_shouldHandleNameWithExtraWhitespace(self):
        display_name = "  John   Doe  "

        result = initials(display_name)

        self.assertEqual("JD", result)

    def test_shouldExtractInitialsWhenRealAzureDevOpsName(self):
        display_name = "Abdul Bram"

        result = initials(display_name)

        self.assertEqual("AB", result)

    def test_shouldExtractInitialsWhenAnotherRealAzureDevOpsName(self):
        display_name = "Jose Navarro Manes"

        result = initials(display_name)

        self.assertEqual("JM", result)

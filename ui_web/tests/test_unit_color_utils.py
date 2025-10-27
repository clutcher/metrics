import unittest

from ui_web.utils.color_utils import ColorUtils


class TestColorUtilsGenerateColor(unittest.TestCase):

    def test_shouldGenerateStableColorWhenSameInputProvidedMultipleTimes(self):
        input_str = "Abdul Bram"

        result1 = ColorUtils.generate_color(input_str)
        result2 = ColorUtils.generate_color(input_str)

        self.assertEqual(result1, result2)

    def test_shouldGenerateDifferentColorsWhenDifferentInputsProvided(self):
        input1 = "Abdul Bram"
        input2 = "Jose Navarro Manes"

        color1 = ColorUtils.generate_color(input1)
        color2 = ColorUtils.generate_color(input2)

        self.assertNotEqual(color1, color2)

    def test_shouldGenerateDifferentColorsWhenSameInitialsDifferentInputs(self):
        input1 = "Abdul Bram"
        input2 = "Alice Brown"

        color1 = ColorUtils.generate_color(input1)
        color2 = ColorUtils.generate_color(input2)

        self.assertNotEqual(color1, color2)

    def test_shouldReturnValidHslColorFormatWhenNormalInput(self):
        input_str = "John Doe"

        result = ColorUtils.generate_color(input_str)

        self.assertTrue(result.startswith("hsl("))
        self.assertTrue(result.endswith(")"))
        self.assertIn("%", result)

    def test_shouldReturnDefaultColorWhenEmptyString(self):
        input_str = ""

        result = ColorUtils.generate_color(input_str)

        self.assertTrue(result.startswith("hsl("))

    def test_shouldReturnDefaultColorWhenNone(self):
        input_str = None

        result = ColorUtils.generate_color(input_str)

        self.assertTrue(result.startswith("hsl("))

    def test_shouldGenerateHueValueBetweenZeroAndThreeSixtyWhenAnyInput(self):
        input_str = "Test User"

        result = ColorUtils.generate_color(input_str)

        hue_str = result.split("(")[1].split(",")[0]
        hue_value = int(hue_str)
        self.assertGreaterEqual(hue_value, 0)
        self.assertLessEqual(hue_value, 360)

    def test_shouldGeneratePastelColorWhenAnyInput(self):
        input_str = "Test User"

        result = ColorUtils.generate_color(input_str)

        saturation_str = result.split(",")[1].strip().split("%")[0]
        saturation_value = int(saturation_str)
        self.assertGreaterEqual(saturation_value, 40)
        self.assertLess(saturation_value, 60)

    def test_shouldGenerateDarkEnoughColorForWhiteTextReadabilityWhenAnyInput(self):
        input_str = "Test User"

        result = ColorUtils.generate_color(input_str)

        lightness_str = result.split(",")[2].strip().rstrip(")").split("%")[0]
        lightness_value = int(lightness_str)
        self.assertGreaterEqual(lightness_value, 45)
        self.assertLess(lightness_value, 55)

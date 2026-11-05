#Copyright ReportLab Europe Ltd. 2000-2017
#see license.txt for license details
"""Regression tests for the ActiveState 3.5.68.post3 follow-up to
CVE-2023-33733: colour strings must not be able to call setColors, and
malformed complex literals must fail cleanly."""
from reportlab.lib.testutils import setOutDir, makeSuiteForClasses, printLocation
setOutDir(__name__)
import unittest
from reportlab import rl_config
from reportlab.lib import colors


class ToColorSafeEvalTestCase(unittest.TestCase):

    def setUp(self):
        self._red = colors.red
        self._toColor = colors.toColor
        self._canUse = rl_config.toColorCanUse

    def tearDown(self):
        # Undo any damage directly; setColors itself goes through toColor.
        colors.red = self._red
        colors.toColor = self._toColor
        colors.getAllNamedColors()['red'] = self._red
        rl_config.toColorCanUse = self._canUse

    def _assertCannotCallSetColors(self):
        for expr in ('setColors(red=Color(0,0,1,1))', 'setColors(toColor=red)'):
            self.assertRaises(ValueError, colors.toColor, expr)
        self.assertTrue(colors.red is self._red)
        self.assertTrue(colors.toColor is self._toColor)
        self.assertEqual(colors.toColor('red'), colors.Color(1, 0, 0, 1))

    def test_extended_literal_eval_cannot_call_setColors(self):
        rl_config.toColorCanUse = 'rl_extended_literal_eval'
        self._assertCannotCallSetColors()

    def test_safe_eval_cannot_call_setColors(self):
        rl_config.toColorCanUse = 'rl_safe_eval'
        self._assertCannotCallSetColors()

    def test_paragraph_markup_cannot_call_setColors(self):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        try:
            Paragraph('<font color="setColors(red=Color(0,0,1,1))">x</font>',
                      getSampleStyleSheet()['Normal'])
        except ValueError:
            pass    # rejected as an invalid colour, which is fine
        self.assertTrue(colors.red is self._red)

    def test_ordinary_colour_strings_still_work(self):
        for expr, expected in (
                ('red', colors.Color(1, 0, 0, 1)),
                ('#ff0000', colors.Color(1, 0, 0, 1)),
                ('Color(1,0,0,1)', colors.Color(1, 0, 0, 1)),
                ('CMYKColor(0,1,1,0)', colors.CMYKColor(0, 1, 1, 0)),
                ('[1,0,0]', colors.Color(1, 0, 0, 1)),
                ):
            self.assertEqual(colors.toColor(expr), expected)

    def test_complex_literal_does_not_crash_evaluator(self):
        # Used to raise NameError (astBinOp) out of rl_extended_literal_eval
        # instead of evaluating or rejecting the literal.
        from reportlab.lib.rl_safe_eval import rl_extended_literal_eval
        self.assertEqual(rl_extended_literal_eval('1+1j'), 1+1j)
        self.assertEqual(rl_extended_literal_eval('-1-2j'), -1-2j)
        self.assertRaises(ValueError, rl_extended_literal_eval, '(1+2)+1j')


def makeSuite():
    return makeSuiteForClasses(ToColorSafeEvalTestCase)

if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()

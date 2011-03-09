#
# Copyright (c) 2008-2011 Brad Taylor <brad@getcoded.net>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import unittest

from berserk2.timeline.sources import FogBugzEmailSource

class FogBugzEmailSourceTokenizerTest(unittest.TestCase):
    def setUp(self):
        self.fb = FogBugzEmailSource()

    def _get_tokens_from_file(self, file):
        f = open(file, 'r')
        lines = map(lambda x: x.rstrip(), f.readlines())
        f.close()
        return self.fb._tokenize_body(lines)

    def test_assigned_to(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/assigned_to.txt')
        self.assertEqual('A FogBugz case was assigned to Unspecified Ardvark Limbo by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(24042, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_assigned_to_with_estimate(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/assigned_to_with_estimate.txt')
        self.assertEqual('A FogBugz case was assigned to Ardvark Ardvark by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(24079, tokens['case_id'])
        self.assertEqual(["Estimate set to '1 hour'"], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_assigned_with_long_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/assigned_with_long_comment.txt')
        self.assertEqual('A FogBugz case was assigned to Unspecified Ardvark Limbo by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(23416, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit. In consectetur nulla nec eros sollicitudin pharetra consequat arcu egestas. Nunc nunc dolor, viverra vel feugiat at, elementum at eros. Morbi egestas euismod nisl, non bibendum massa commodo euismod.',
            '',
            'Maecenas sed nisi eu ligula interdum porttitor ut quis sem.'
        ], tokens['comment'])

    def test_closed_by(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/closed_by.txt')
        self.assertEqual('A FogBugz case was closed by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(24040, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_closed_with_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/closed_with_comment.txt')
        self.assertEqual('A FogBugz case was closed by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(18843, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual(['No longer applicable. Closing.'], tokens['comment'])

    def test_closed_with_severity_change_no_value(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/closed_with_severity_change_no_value.txt')
        self.assertEqual('A FogBugz case was closed by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(14243, tokens['case_id'])
        self.assertEqual(["Severity changed from (No Value) to '4 - Minor (Default)'"], tokens['changes'])
        self.assertEqual(['verified'], tokens['comment'])

    def test_edit_with_estimate_and_elapsed_change_no_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/edit_with_estimate_and_elapsed_change_no_comment.txt')
        self.assertEqual('A FogBugz case was edited by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(23861, tokens['case_id'])
        self.assertEqual([
            "Estimate changed from '12 hours' to '0 hours'.",
            "Non-timesheet elapsed time changed from '8 hours' to '0 hours'"
        ], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_milestone_change_with_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/milestone_change_with_comment.txt')
        self.assertEqual('A FogBugz case was assigned to Unspecified Ardvark Limbo by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(22240, tokens['case_id'])
        self.assertEqual(["Milestone changed from '11.10 Bouncy' to '11.12 Classy'."], tokens['changes'])
        self.assertEqual(["Lorem ipsum dolor sit amet, consectetur adipiscing el (#999999) ectetur nulla nec eros s. -Ardvark."], tokens['comment'])

    def test_parent_change_no_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/parent_change_no_comment.txt')
        self.assertEqual('A FogBugz case was edited by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(23723, tokens['case_id'])
        self.assertEqual(["Parent changed from (None) to Case 24054."], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_resolved_wont_fix_assigned_with_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/resolved_wont_fix_assigned_with_comment.txt')
        self.assertEqual("A FogBugz case was Resolved (Won't Fix) and assigned to Ardvark Ardvark by Ardvark Ardvark.", tokens['subject'])
        self.assertEqual(24042, tokens['case_id'])
        self.assertEqual(["Status changed from 'Active' to 'Resolved (Won't Fix)'."], tokens['changes'])
        self.assertEqual(['Lorem ipsum dolor sit amet, consectetur a.'], tokens['comment'])

    def test_status_and_severity_change_no_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/status_and_severity_change_no_comment.txt')
        self.assertEqual('A FogBugz case was Resolved (Fixed) and assigned to Ardvark Ardvark by Ardvark Ardvark.', tokens['subject'])
        self.assertEqual(22523, tokens['case_id'])
        self.assertEqual([
            "Severity changed from (No Value) to '4 - Minor (Default)'",
            "Status changed from 'Active' to 'Resolved (Fixed)'."
        ], tokens['changes'])
        self.assertEqual([], tokens['comment'])

if __name__ == '__main__':
    unittest.main()

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

from datetime import datetime

from django.test import TestCase
from django.test.client import Client

from berserk2.timeline.models import Event, Actor

class FogBugzEmailSourceTokenizerTest(TestCase):
    def setUp(self):
        from berserk2.timeline.plugins.fogbugz import PeriodicPollSource
        self.fb = PeriodicPollSource()

    def _get_tokens_from_file(self, file):
        f = open(file, 'r')
        lines = map(lambda x: x.rstrip(), f.readlines())
        f.close()
        return self.fb._tokenize_body(lines)

    def test_assigned_to(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/assigned_to.txt')
        self.assertEqual('A FogBugz case was assigned to Unspecified Aardvark Limbo by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(24042, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_assigned_to_with_estimate(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/assigned_to_with_estimate.txt')
        self.assertEqual('A FogBugz case was assigned to Aardvark Bobcat by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(24079, tokens['case_id'])
        self.assertEqual(["Estimate set to '1 hour'"], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_assigned_with_long_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/assigned_with_long_comment.txt')
        self.assertEqual('A FogBugz case was assigned to Unspecified Aardvark Limbo by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(23416, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit. In consectetur nulla nec eros sollicitudin pharetra consequat arcu egestas. Nunc nunc dolor, viverra vel feugiat at, elementum at eros. Morbi egestas euismod nisl, non bibendum massa commodo euismod.',
            '',
            'Maecenas sed nisi eu ligula interdum porttitor ut quis sem.'
        ], tokens['comment'])

    def test_closed_by(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/closed_by.txt')
        self.assertEqual('A FogBugz case was closed by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(24040, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_closed_with_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/closed_with_comment.txt')
        self.assertEqual('A FogBugz case was closed by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(18843, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual(['No longer applicable. Closing.'], tokens['comment'])

    def test_closed_with_severity_change_no_value(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/closed_with_severity_change_no_value.txt')
        self.assertEqual('A FogBugz case was closed by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(14243, tokens['case_id'])
        self.assertEqual(["Severity changed from (No Value) to '4 - Minor (Default)'"], tokens['changes'])
        self.assertEqual(['verified'], tokens['comment'])

    def test_edit_with_estimate_and_elapsed_change_no_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/edit_with_estimate_and_elapsed_change_no_comment.txt')
        self.assertEqual('A FogBugz case was edited by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(23861, tokens['case_id'])
        self.assertEqual([
            "Estimate changed from '12 hours' to '0 hours'.",
            "Non-timesheet elapsed time changed from '8 hours' to '0 hours'"
        ], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_milestone_change_with_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/milestone_change_with_comment.txt')
        self.assertEqual('A FogBugz case was assigned to Unspecified Aardvark Limbo by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(22240, tokens['case_id'])
        self.assertEqual(["Milestone changed from '11.10 Bouncy' to '11.12 Classy'."], tokens['changes'])
        self.assertEqual(["Lorem ipsum dolor sit amet, consectetur adipiscing el (#999999) ectetur nulla nec eros. -Aardvark."], tokens['comment'])

    def test_parent_change_no_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/parent_change_no_comment.txt')
        self.assertEqual('A FogBugz case was edited by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(23723, tokens['case_id'])
        self.assertEqual(["Parent changed from (None) to Case 24054."], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_resolved_wont_fix_assigned_with_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/resolved_wont_fix_assigned_with_comment.txt')
        self.assertEqual("A FogBugz case was Resolved (Won't Fix) and assigned to Aardvark Bobcat by Aardvark Bobcat.", tokens['subject'])
        self.assertEqual(24042, tokens['case_id'])
        self.assertEqual(["Status changed from 'Active' to 'Resolved (Won't Fix)'."], tokens['changes'])
        self.assertEqual(['Lorem ipsum dolor sit amet, consectetur a.'], tokens['comment'])

    def test_status_and_severity_change_no_comment(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/status_and_severity_change_no_comment.txt')
        self.assertEqual('A FogBugz case was Resolved (Fixed) and assigned to Aardvark Bobcat by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(22523, tokens['case_id'])
        self.assertEqual([
            "Severity changed from (No Value) to '4 - Minor (Default)'",
            "Status changed from 'Active' to 'Resolved (Fixed)'."
        ], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_last_message(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/last_message.txt')
        self.assertEqual('A FogBugz case was edited by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(23987, tokens['case_id'])
        self.assertEqual([], tokens['changes'])
        self.assertEqual([
'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed adipiscing tincidunt imperdiet. Maecenas a bibendum mi. Nulla in enim ni.',
'',
'Maecenas a bibendum mi. Nulla in enim nibh, vitae cursus enim. Pellentesque cursus, orci at venenatis posuerel.'], tokens['comment'])

    def test_was_resolved_duplicate(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/was_resolved_duplicate.txt')
        self.assertEqual('A FogBugz case was Resolved (Duplicate) and assigned to Aardvark Bobcat by Bobcat Goldthwait.', tokens['subject'])
        self.assertEqual(23808, tokens['case_id'])
        self.assertEqual(["Status changed from 'Active' to 'Resolved (Duplicate)'.",
                          'Duplicate of changed from (None) to Case 23792.'], tokens['changes'])
        self.assertEqual([], tokens['comment'])

    def test_float_estimate(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/float_estimate.txt')
        self.assertEqual('A FogBugz case was edited by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(23986, tokens['case_id'])
        self.assertEqual(["Estimate set to '37.5 hours'"], tokens['changes'])
        self.assertEqual([
'Sed consectetur quam vel metus hendrerit ac porta nisl placerat. Nulla q.',
'',
'Sed consectetur quam vel metus hendrerit ac porta nisl placerat. Nulla quis metus orci. Proin in erat a felis accumsan adipiscing ac in dolor. Donec quis est turpis, venenatis cursus sapien. Vivamus id gravida nisl. Vestibulum est nunc, varius vitae sagittis eu, tincidunt sed diam. Sed semper risus malesuada diam molestie volutpat. Donec naisi.'], tokens['comment'])

    def test_qa_assignee(self):
        tokens = self._get_tokens_from_file('timeline/testassets/fogbugz_emails/qa_assignee.txt')
        self.assertEqual('A FogBugz case was edited by Aardvark Bobcat.', tokens['subject'])
        self.assertEqual(24107, tokens['case_id'])
        self.assertEqual(["QA Assignee changed from Bobcat Goldthwait to Aardvark Bobcat"], tokens['changes'])
        self.assertEqual([], tokens['comment'])

class FogBugzEmailSourceParserTest(TestCase):
    def setUp(self):
        from berserk2.timeline.plugins.fogbugz import PeriodicPollSource
        self.fb = PeriodicPollSource()

    def _parse_file(self, file):
        f = open(file, 'r')
        lines = map(lambda x: x.rstrip(), f.readlines())
        f.close()
        tokens = self.fb._tokenize_body(lines)
        self.fb._parse_body(tokens)

    def test_assigned_to(self):
        self._parse_file('timeline/testassets/fogbugz_emails/assigned_to.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual('Unspecified Aardvark', a.deuteragonist.first_name)
        self.assertEqual('Limbo', a.deuteragonist.last_name)

        self.assertEqual('{{ protagonist }} assigned {{ task_link }} to {{ deuteragonist }}.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_assigned_to_with_estimate(self):
        self._parse_file('timeline/testassets/fogbugz_emails/assigned_to_with_estimate.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} assigned {{ task_link }} to {{ proto_self }} and {{ proto_third }} estimates it will require 1 hour to complete.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_assigned_with_long_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/assigned_with_long_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual('Unspecified Aardvark', a.deuteragonist.first_name)
        self.assertEqual('Limbo', a.deuteragonist.last_name)

        self.assertEqual('{{ protagonist }} assigned {{ task_link }} to {{ deuteragonist }}.',
                         a.message)

        self.assertEqual("""Lorem ipsum dolor sit amet, consectetur adipiscing elit. In consectetur nulla nec eros sollicitudin pharetra consequat arcu egestas. Nunc nunc dolor, viverra vel feugiat at, elementum at eros. Morbi egestas euismod nisl, non bibendum massa commodo euismod.

Maecenas sed nisi eu ligula interdum porttitor ut quis sem.""", a.comment)

    def test_closed_by(self):
        self._parse_file('timeline/testassets/fogbugz_emails/closed_by.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} closed {{ task_link }}.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_closed_with_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/closed_with_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} closed {{ task_link }}.',
                         a.message)

        self.assertEqual('No longer applicable. Closing.', a.comment)

    def test_closed_with_severity_change_no_value(self):
        self._parse_file('timeline/testassets/fogbugz_emails/closed_with_severity_change_no_value.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} closed {{ task_link }} and {{ proto_third }} set the severity of it to 4 - Minor (Default).',
                         a.message)

        self.assertEqual('verified', a.comment)

    def test_edit_with_estimate_and_elapsed_change_no_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/edit_with_estimate_and_elapsed_change_no_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} estimates {{ task_link }} will require 0 hours to complete and {{ proto_third }} reports that 0 hours have been spent on it.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_milestone_change_with_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/milestone_change_with_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual('Unspecified Aardvark', a.deuteragonist.first_name)
        self.assertEqual('Limbo', a.deuteragonist.last_name)

        self.assertEqual("{{ protagonist }} assigned {{ task_link }} to {{ deuteragonist }} and {{ proto_third }} moved it to the '11.12 Classy' milestone.",
                         a.message)

        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing el (#999999) ectetur nulla nec eros. -Aardvark.',
                         a.comment)

    def test_parent_change_no_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/parent_change_no_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} set the parent of {{ task_link }} to #24054.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_resolved_wont_fix_assigned_with_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/resolved_wont_fix_assigned_with_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual("{{ protagonist }} marked {{ task_link }} as won't fix.",
                         a.message)

        self.assertEqual('Lorem ipsum dolor sit amet, consectetur a.', a.comment)

    def test_status_and_severity_change_no_comment(self):
        self._parse_file('timeline/testassets/fogbugz_emails/status_and_severity_change_no_comment.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} set the severity of {{ task_link }} to 4 - Minor (Default) and {{ proto_third }} marked it as fixed.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_last_message(self):
        self._parse_file('timeline/testassets/fogbugz_emails/last_message.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} commented on {{ task_link }}.',
                         a.message)

        self.assertEqual('''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed adipiscing tincidunt imperdiet. Maecenas a bibendum mi. Nulla in enim ni.

Maecenas a bibendum mi. Nulla in enim nibh, vitae cursus enim. Pellentesque cursus, orci at venenatis posuerel.''', a.comment)

    def test_was_resolved_duplicate(self):
        self._parse_file('timeline/testassets/fogbugz_emails/was_resolved_duplicate.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Bobcat', a.protagonist.first_name)
        self.assertEqual('Goldthwait', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} marked {{ task_link }} as duplicate and {{ proto_third }} notes that it is a duplicate of #23792.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_float_estimate(self):
        self._parse_file('timeline/testassets/fogbugz_emails/float_estimate.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} estimates {{ task_link }} will require 37.5 hours to complete.',
                         a.message)

        self.assertEqual('''Sed consectetur quam vel metus hendrerit ac porta nisl placerat. Nulla q.

Sed consectetur quam vel metus hendrerit ac porta nisl placerat. Nulla quis metus orci. Proin in erat a felis accumsan adipiscing ac in dolor. Donec quis est turpis, venenatis cursus sapien. Vivamus id gravida nisl. Vestibulum est nunc, varius vitae sagittis eu, tincidunt sed diam. Sed semper risus malesuada diam molestie volutpat. Donec naisi.''', a.comment)

    def test_qa_assignee(self):
        self._parse_file('timeline/testassets/fogbugz_emails/qa_assignee.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} assigned {{ proto_self }} as the QA resource for {{ task_link }}.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_reopened_with_many_changes(self):
        self._parse_file('timeline/testassets/fogbugz_emails/reopened_with_many_changes.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual('--', a.deuteragonist.first_name)
        self.assertEqual('', a.deuteragonist.last_name)

        self.assertEqual("{{ protagonist }} assigned {{ deuteragonist }} as the QA resource for {{ task_link }}. {{ proto_third|capfirst }} changed the title of it to 'Lorem ipsum dolor sit amet, consectetura /   adipis ing elit', reopened it and moved it to the 'Undecided' milestone.",
                         a.message)

        self.assertEqual('Lore ip umdolo si tametc ON1 11.10 sec tetur adi pisci ngelitve.\n\nLor emips umdo lor sitame tco nse ctetu radip.\nLoremip su mdolor sitamet.',
                         a.comment)

    def test_edited_added_subcase(self):
        self._parse_file('timeline/testassets/fogbugz_emails/edited_added_subcase.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} added #23368 as a subcase of {{ task_link }}.',
                         a.message)

        self.assertEqual('', a.comment)

    def test_edited_added_tag(self):
        self._parse_file('timeline/testassets/fogbugz_emails/edited_added_tag.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual('Unspecified Aardvark', a.deuteragonist.first_name)
        self.assertEqual('Limbo', a.deuteragonist.last_name)

        self.assertEqual("{{ protagonist }} assigned {{ task_link }} to {{ deuteragonist }} and {{ proto_third }} added tag 'aar' to it.",
                         a.message)

        self.assertEqual(u'Lorem:1.2\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum ultricies mattis ligula, at congue diam porttitor ut. Nulla fringilla mi id dui pharetra tincidunt. Etiam velit nisi, congue ut ullamcorper at, dictum ut elit. Proin rhoncus bibendum est in cursus.\nIpsumd OL:orsitametconsec\n(To get this information press "CTRL+ALT+Shift+3")\nRepro: 3/3\n\nSummary:\n\nSteps to Reproduce:\n1. Te tu rad ipiscing elit ves ibu lu multric ies matt isli gul aatcongu / ediampor (00000) tti torut nulla\n\nExpected Results: fri ngil lamiid duipha retr at inci dun tetiamv el itnisic ong ueu tu LL\n\nActual Results:\namcorpe rat di ctumutel.\nsee also case: 22439', a.comment)

    def test_edited_removed_tag(self):
        self._parse_file('timeline/testassets/fogbugz_emails/edited_removed_tag.txt')

        events = Event.objects.all()
        self.assertEqual(1, events.count())

        a = events[0]
        self.assertEqual('Aardvark', a.protagonist.first_name)
        self.assertEqual('Bobcat', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual("{{ protagonist }} removed tag 'aar' from {{ task_link }}.",
                         a.message)

        self.assertEqual('', a.comment)

class GitHubPushSourceTest(TestCase):
    def setUp(self):
        from berserk2.timeline.plugins.github import PushSource
        self.gh = PushSource()
        self.client = Client()

    def _process_payload(self, file):
        f = open(file, 'r')
        self.client.post('/timeline/push/github', {
            'payload': '\n'.join(f.readlines())
        })
        f.close()

    def test_github_example(self):
        self._process_payload('timeline/testassets/github_payloads/github_example.txt')

        events = Event.objects.all()
        self.assertEqual(2, events.count())

        a = events[0]
        self.assertEqual(datetime(2008, 2, 15, 14, 57, 17), a.date)

        self.assertEqual('Chris', a.protagonist.first_name)
        self.assertEqual('Wanstrath', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} pushed <a href="http://github.com/defunkt/github/commit/41a212ee83ca127e3c8cf465891ab7216a705f59" target="_blank">41a212e</a> to github.',
                         a.message)

        self.assertEqual('okay i give in', a.comment)

        b = events[1]
        self.assertEqual(datetime(2008, 2, 15, 14, 36, 34), b.date)

        self.assertEqual('Chris', b.protagonist.first_name)
        self.assertEqual('Wanstrath', b.protagonist.last_name)

        self.assertEqual(None, b.deuteragonist)

        self.assertEqual('{{ protagonist }} pushed <a href="http://github.com/defunkt/github/commit/de8251ff97ee194a289832576287d6f8ad74e3d0" target="_blank">de8251f</a> to github.',
                         b.message)

        self.assertEqual('update pricing a tad', b.comment)

    def test_berserk(self):
        self._process_payload('timeline/testassets/github_payloads/berserk.txt')

        events = Event.objects.all()
        self.assertEqual(3, events.count())

        a = events[0]
        self.assertEqual(datetime(2011, 3, 1, 12, 30, 53), a.date)

        self.assertEqual('Brad', a.protagonist.first_name)
        self.assertEqual('Taylor', a.protagonist.last_name)

        self.assertEqual(None, a.deuteragonist)

        self.assertEqual('{{ protagonist }} pushed <a href="https://github.com/btaylor/berserk/commit/1398bb563b416b5121f23cbc8108c69b011baa94" target="_blank">1398bb5</a> to berserk.',
                         a.message)

        self.assertEqual('Forgot to add import', a.comment)

        b = events[1]
        self.assertEqual(datetime(2011, 3, 1, 12, 31, 32), b.date)

        self.assertEqual('Brad', b.protagonist.first_name)
        self.assertEqual('Taylor', b.protagonist.last_name)

        self.assertEqual(None, b.deuteragonist)

        self.assertEqual('{{ protagonist }} pushed <a href="https://github.com/btaylor/berserk/commit/eb0a4dc458c4213bd0d8daaee23c5e940cecff58" target="_blank">eb0a4dc</a> to berserk.',
                         b.message)

        self.assertEqual('South and djangoflash should be loaded last', b.comment)

        c = events[2]
        self.assertEqual(datetime(2011, 3, 1, 13, 40, 16), c.date)

        self.assertEqual('Brad', c.protagonist.first_name)
        self.assertEqual('Taylor', c.protagonist.last_name)

        self.assertEqual(None, c.deuteragonist)

        self.assertEqual('{{ protagonist }} pushed <a href="https://github.com/btaylor/berserk/commit/c59fcedbd8783336223ec57a17baa3e390299b4d" target="_blank">c59fced</a> to berserk.',
                         c.message)

        self.assertEqual('Switch order of args', c.comment)

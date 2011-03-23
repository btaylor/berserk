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

import re
import time
import email
import imaplib
import simplejson
import dateutil.parser

from datetime import datetime

from django.utils.html import escape

from berserk2 import settings
from berserk2.timeline.models import Actor, Event
from berserk2.sprints.models import Task, BugTracker

class FogBugzEmailSource():
    def __init__(self):
        self.name = 'FogBugz'

    @staticmethod
    def enabled():
        """
        Returns true if the source is configured properly and should be run.
        """
        return settings.FB_EMAIL_SOURCE_HOST != '' \
               and settings.FB_EMAIL_SOURCE_USER != '' \
               and settings.FB_EMAIL_SOURCE_USER != ''

    def _parse_date(self, str):
        """
        Parses a date found in an email message and returns a localized
        datetime.  If not found, returns datetime.now().
        """
        tuple = email.utils.parsedate(str)
        if tuple:
            return datetime.fromtimestamp(time.mktime(tuple))
        return datetime.now()

    def run(self):
        """
        Runs a single iteration of the source, in this case, polling for the
        first set of unread messages.
        """
        def get_charset(msg, default="ascii"):
            if msg.get_content_charset():
                return msg.get_content_charset()
            if msg.get_charset():
                return msg.get_charset()
            return default

        c = imaplib.IMAP4_SSL(settings.FB_EMAIL_SOURCE_HOST)
        c.login(settings.FB_EMAIL_SOURCE_USER, settings.FB_EMAIL_SOURCE_PASSWORD)
        try:
            c.select('INBOX')

            typ, [msg_ids] = c.search(None, 'UNSEEN')
            if msg_ids == '':
                return

            for i in msg_ids.split(' '):
                typ, msg_data = c.fetch(i, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        date = self._parse_date(msg['date'])

                        payload = msg.get_payload(decode=True)
                        if not payload:
                            continue

                        body = unicode(payload, get_charset(msg), 'replace')
                        if not body:
                            continue

                        self._parse_body(self._tokenize_body(body.split('\r\n')),
                                         date)
        finally:
            try:
                c.close()
            except:
                pass
            c.logout()

    def _tokenize_body(self, lines):
        case_id = 0
        changes = []
        begin_changes_block = False

        comment = []
        begin_comment_block = False

        i = 0
        while i < len(lines):
            l = lines[i].strip()
            m = lines[i+1].strip() if i + 1 < len(lines) else None
            n = lines[i+2].strip() if i + 2 < len(lines) else None

            # Look for the end of email marker
            if l == '' and m == '':
                if n and (n.startswith('You are subscribed') \
                          or n.startswith('If you do not want to')):
                    break

            if l.startswith('Changes:'):
                begin_changes_block = True
            elif l.startswith('Last message:'):
                begin_comment_block = True
            elif not begin_changes_block and not begin_comment_block \
                 and l.startswith('URL:') and m == '' and n != '' \
                 and not n.startswith('Description'):
                i += 1
                begin_comment_block = True
            elif begin_changes_block:
                if l == '':
                    begin_changes_block = False
                    begin_comment_block = True
                else:
                    changes.append(l)
            elif begin_comment_block:
                comment.append(l)

            if l.startswith('Case ID:'):
                foo, bar, case_id = l.split()
                case_id = int(case_id)

            i += 1

        return {'subject': lines[0],
                'case_id': case_id,
                'changes': changes,
                'comment': comment}

    def _get_case_id(self, after):
        """
        From a string like 'Case 43355' returns the case number as an int.
        """
        m = re.match('Case (?P<case_id>\d+)', after)
        if m:
            return int(m.group('case_id'))
        return None

    def _make_subevent(self, message):
        """
        Converts an event message (which uses the protagonist's full name and
        task link) to a subevent, intended follows immediately after the event
        message in a paragraph.

            e.g.: Brad Taylor assigned #41346 to himself.
         becomes: He assigned it to himself.
        """
        return message.replace('{{ protagonist }}', '{{ proto_caps_third }}') \
                      .replace('{{ task_link }}', 'it')

    def _parse_body(self, tokens, date=datetime.now()):
        events = []
        protagonist = ''
        deuteragonist = ''

        subject = tokens['subject']
        case_id = int(tokens['case_id'])
        changes = tokens['changes']
        comment = tokens['comment']

        # The actor involved in the event will be identified in the subject line:
        # e.g.: A FogBugz case was edited by Aardvark Bobcat.
        m = re.search('by (\w+ \w+)', subject)
        if m:
            protagonist = m.group(1)

        # Some emails are formatted such that the action is embedded inside of
        # the subject line:
        if subject.startswith('A new case'):
            events.append('{{ protagonist }} opened a new case {{ task_link }}.')
        elif subject.startswith('A FogBugz case was assigned to'):
            m = re.search('A FogBugz case was assigned to (?P<deuteragonist>.*) by', subject)
            assigned_to = m.group('deuteragonist')
            if protagonist == assigned_to:
                events.append('{{ protagonist }} assigned {{ task_link }} to {{ proto_self }}.')
            else:
                deuteragonist = assigned_to
                events.append('{{ protagonist }} assigned {{ task_link }} to {{ deuteragonist }}.')
        elif subject.startswith('A FogBugz case was closed by'):
            events.append('{{ protagonist }} closed {{ task_link }}.')

        # Others have actions listed out nicely:
        if len(changes) > 0:
            for change in changes:
                m = re.match("Estimate set to '(?P<hours>\d+.?\d*) hours?'", change)
                if m:
                    hours = float(m.group('hours'))
                    plural = 'hour' if hours == 1 else 'hours'
                    events.append("{{ protagonist }} estimates {{ task_link }} will require %g %s to complete." % (hours, plural))
                    continue

                m = re.match("Added subcase (?P<subcase>\d+).", change)
                if m:
                    subcase = int(m.group('subcase'))
                    events.append('{{ protagonist }} added #%d as a subcase of {{ task_link }}.' % subcase)
                    continue

                # The change line may or may not end in a period
                # Don't you just love their consistentcy?
                change = change.rstrip('.')

                m = re.match("^(?P<type>.+) changed from '?(?P<before>.*)'? to '?(?P<after>.*)'?$", change)
                if not m:
                    continue

                type = m.group('type').lower()

                # Sometimes the regex isn't greedy enough and doesn't eat the
                # single quote when we ask it nicely
                before = m.group('before').strip("'")
                after = m.group('after').strip("'")
                if type == 'milestone':
                    events.append("{{ protagonist }} moved {{ task_link }} to the '%s' milestone." % after)
                elif type == 'title':
                    events.append("{{ protagonist }} changed the title of {{ task_link }} to '%s'." % escape(after))
                elif type == 'estimate':
                    hours = float(after.split(' ', 1)[0])
                    plural = 'hour' if hours == 1 else 'hours'
                    events.append("{{ protagonist }} estimates {{ task_link }} will require %g %s to complete." % (hours, plural))
                elif type == 'non-timesheet elapsed time':
                    hours = float(after.split(' ', 1)[0])
                    plural = 'hour has' if hours == 1 else 'hours have'
                    events.append("{{ protagonist }} reports that %g %s been spent on {{ task_link }}." % (hours, plural))
                elif type == 'status':
                    if before.startswith('Resolved') and after == 'Active':
                        events.append("{{ protagonist }} reopened {{ task_link }}.")
                    elif after == 'Resolved (Fixed)':
                        events.append("{{ protagonist }} marked {{ task_link }} as fixed.")
                    elif after == 'Resolved (Not Reproducible)':
                        events.append("{{ protagonist }} marked {{ task_link }} as not reproducible.")
                    elif after == 'Resolved (Duplicate)':
                        events.append("{{ protagonist }} marked {{ task_link }} as duplicate.")
                    elif after == 'Resolved (Postpooned)':
                        events.append("{{ protagonist }} marked {{ task_link }} as postponed.")
                    elif after == 'Resolved (By Design)':
                        events.append("{{ protagonist }} marked {{ task_link }} as by design.")
                    elif after == 'Resolved (Won\'t Fix)':
                        events.append("{{ protagonist }} marked {{ task_link }} as won't fix.")
                    elif after == 'Resolved (Implemented)':
                        events.append("{{ protagonist }} marked {{ task_link }} as implemented.")
                    elif after == 'Resolved (Completed)':
                        events.append("{{ protagonist }} marked {{ task_link }} as completed.")
                    else:
                        events.append("{{ protagonist }} marked the status of {{ task_link }} as %s." % after)
                elif type == 'duplicate of':
                    events.append('{{ protagonist }} notes that {{ task_link }} is a duplicate of #%d.' % self._get_case_id(after))
                elif type == 'parent':
                    events.append('{{ protagonist }} set the parent of {{ task_link }} to #%d.' % self._get_case_id(after))
                elif type == 'qa assignee':
                    if protagonist == after:
                        events.append('{{ protagonist }} assigned {{ proto_self }} as the QA resource for {{ task_link }}.')
                    else:
                        deuteragonist = after
                        events.append('{{ protagonist }} assigned {{ deuteragonist }} as the QA resource for {{ task_link }}.')
                else:
                    if before == '(No Value)':
                        events.append("{{ protagonist }} set the %s of {{ task_link }} to %s." % (type, after))
                    else:
                        events.append("{{ protagonist }} changed the %s of {{ task_link }} from %s to %s." % (type, before, after))

        # Last resort: if nothing else, the user just commented
        if len(events) == 0 and len(changes) == 0 and len(comment) > 0:
            events.append('{{ protagonist }} commented on {{ task_link }}.')

        # One mail will produce just one event, but messages will be merged.
        task = None

        trackers = BugTracker.objects.all()
        if trackers.count() > 0:
            # TODO: Grab default bug tracker from the currently active sprint
            task, created = Task.objects.get_or_create(remote_tracker_id=case_id,
                                                       bug_tracker=trackers[0])
            task.get_latest_snapshot(refresh_if_old=True)

        protag = None
        if protagonist and protagonist != '':
            protag, created = Actor.objects.get_or_create_by_full_name(protagonist)

        deuter = None
        if deuteragonist and deuteragonist != '':
            deuter, created = Actor.objects.get_or_create_by_full_name(deuteragonist)

        comments = u'\n'.join(comment)

        # If we have more than one event, make the other events subevents by
        # changing a few template variables around.
        for i in range(1, len(events)):
            events[i] = self._make_subevent(events[i])

        return Event.objects.create(
            source=self.name, protagonist=protag, deuteragonist=deuter,
            message=u' '.join(events),
            comment=comments, task=task, date=date
        )

class GitHubPushSource:
    def __init__(self):
        self.name = 'GitHub'

    @staticmethod
    def enabled():
        """
        Returns true if the source is configured properly and should be run.
        """
        return False

    def process_payload(self, payload):
        data = simplejson.loads(payload)

        repo = data.get('repository')
        repo_name = repo.get('name') if repo else 'Unknown'
        ref = data.get('ref')

        for commit in data.get('commits'):
            author = commit.get('author')
            protagonist = author.get('name')

            if protagonist:
                protagonist, created = Actor.objects.get_or_create_by_full_name(protagonist)

            if ref == 'refs/heads/master':
                message = '{{ protagonist }} pushed <a href="%s" target="_blank">%s</a> to %s.' \
                          % (commit.get('url'), commit['id'][:7], repo_name)
            else:
                branch = ref.rsplit('/', 1)[1] if ref.startswith('refs/heads/') else ref
                message = '{{ protagonist }} pushed <a href="%s" target="_blank">%s</a> to %s\'s %s branch.' \
                          % (commit.get('url'), commit['id'][:7], repo_name, branch)

            date = datetime.now()
            timestamp = commit['timestamp']
            if timestamp:
                date = dateutil.parser.parse(timestamp).replace(tzinfo=None)

            Event.objects.create(
                source=self.name, protagonist=protagonist, date=date,
                message=message, comment=escape(commit.get('message'))
            )

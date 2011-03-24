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

import simplejson
import dateutil.parser

from datetime import datetime

from django.utils.html import escape

from berserk2.timeline.models import Actor, Event
from berserk2.timeline.plugins import BasePushSource

class PushSource(BasePushSource):
    def __init__(self):
        self.name = 'GitHub'

    @staticmethod
    def enabled():
        """
        Returns true if the source is configured properly and should be run.
        """
        return True

    @staticmethod
    def get_url_identifier():
        return 'github'

    def push(self, request):
        """
        Accepts a POST request from GitHub when a user git pushes to a
        repository we're monitorring.
    	"""
        if not 'payload' in request.POST:
            return

        payload = request.POST['payload']
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

#
# Copyright (c) 2011 Brad Taylor <brad@getcoded.net>
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

from django.core.urlresolvers import get_callable

from berserk2 import settings
from berserk2.timeline.models import Event

class PluginFactory:
    @staticmethod
    def get_periodic_poll_sources():
        """
        Returns all BasePeriodicPollSource subclasses in
        settings.TIMELINE_SOURCES.
        """
        sources = []
        for source in settings.TIMELINE_SOURCES:
            try:
                klass = get_callable(source + '.PeriodicPollSource')
                if issubclass(klass, BasePeriodicPollSource) \
                   and klass.enabled():
                    sources.append(klass)
            except:
                pass
        return sources

    @staticmethod
    def get_push_sources():
        """
        Returns all BasePushSource subclasses in settings.TIMELINE_SOURCES.
        """
        sources = []
        for source in settings.TIMELINE_SOURCES:
            try:
                klass = get_callable(source + '.PushSource')
                if issubclass(klass, BasePushSource) \
                   and klass.enabled():
                    sources.append(klass)
            except:
                pass
        return sources

    @staticmethod
    def get_push_source_by_id(source_id):
    	"""
        Returns any BasePushSource subclasses in settings.TIMELINE_SOURCES
        which have source_id as url_identifier.
        """
        matches = []
        sources = PluginFactory.get_push_sources()
        for source in sources:
            if source_id == source.get_url_identifier():
                matches.append(source)
        return matches

class BaseSource:
    @staticmethod
    def enabled():
        """
        Returns true if the source is configured properly and should be run.
        """
        raise NotImplementedError()

class BasePeriodicPollSource(BaseSource):
    def poll(self):
        raise NotImplementedError()

class BasePushSource:
    @staticmethod
    def get_url_identifier():
        raise NotImplementedError()

    def push(self, payload):
        raise NotImplementedError()

from berserk2.timeline.plugins import fogbugz, github

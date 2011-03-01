#
# Copyright (c) 2008-20011 Brad Taylor <brad@getcoded.net>
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

from backend import FogBugz
from time import strptime
from datetime import datetime
from xml.dom import minidom
import dateutil.parser
import urllib

class FogBugzClient:
    def __init__(self, base_url, unused):
        self.base_url = base_url
        self.backend = FogBugz(base_url)

    @staticmethod
    def validate_backend(backend_name):
        """
        Returns True always, as this client doesn't support backends.
        """
        return True

    @staticmethod
    def get_url_from_id(remote_tracker_id, base_url):
        """
        Returns an absolute URL to a bug given its remote_tracker_id and the
        tracker's base_url.
        """
        return '%s/default.asp?%s' % (base_url, remote_tracker_id)

    @staticmethod
    def get_id_from_url(url, base_url):
        """
        Returns the id of a bug given a correctly-formatted URL,
            e.g.: https://foo.fogbugz.com/default.asp?23714
                  https://foo.fogbugz.com/default.asp?23714#430608
        otherwise, returns None.
        """
        path, query = urllib.splitquery(url)
        if not path.startswith(base_url):
            return None

        try:
            vals = query.split('#', 1)
            return vals[0]
        except:
            return None

    def login(self, user, password):
        """
        Authenticates the user against the remote FogBugz instance.  Returns
        True if successful, False otherwise.
        """
        try:
            self.backend.logon(user, password)
        except AssertionError, e:
            logging.error('Exception while logging in:\n%s' % e)
            return False
        else:
            return True

    def get_bug(self, bug_id):
        """
        Returns a FogBugzBug instance or a blank instance if bug_id could not
        be found or the Server could not be reached.
        """
        assert int(bug_id) > 0
        return FogBugzBug(self.backend, bug_id)

    def get_stats_for_milestone(self, project, milestone):
        """
        Returns a tuple containing the number of open bugs, total estimated
        hours and total remaining hours for the open bugs in the given
        milestone.
        """
        # This is really gross.  FogBugz doesn't allow us to exact match the
        # name of a fixFor, so we need to do the matching ourselves and use
        # ixFixFor in our search instead.
        milestone_id = self.__get_milestone_id(milestone)
        if milestone_id == -1: return []

        project_id = self.__get_project_id(project)
        if project_id == -1: return []

        # NOTE: status:"open" will include all bugs that have not been C&C'ed
        xml = self.backend.search(q='project:"=%d" milestone:"=%d" status:"open"' % (project_id, milestone_id),
                                  cols='hrsCurrEst,hrsElapsed')

        estimated_hours = remaining_hours = 0
        for c in xml.findAll('case'):
            estimated_hours += int(c.findChild('hrscurrest').text)
            remaining_hours += max(int(c.findChild('hrscurrest').text) - int(c.findChild('hrselapsed').text), 0)

        return (int(xml.find('cases')['count']), estimated_hours, remaining_hours)

    def __get_project_id(self, project_name):
        # TODO: great opportunity for some caching
        xml = self.backend.listProjects()
        for f in xml.findAll('project'):
            if f.find('sproject').text == project_name:
                return int(f.find('ixproject').text)
        return -1

    def __get_milestone_id(self, milestone_name):
        # TODO: great opportunity for some caching
        xml = self.backend.listFixFors()
        for f in xml.findAll('fixfor'):
            if f.find('sfixfor').text == milestone_name:
                return int(f.find('ixfixfor').text)
        return -1


class FogBugzBug:
    """
    A FogBugz Bug
    """
    created = datetime.today()
    summary = ""
    last_modified = datetime.today()
    product = ""
    component = ""
    version = ""
    status = ""
    priority = ""
    severity = ""
    milestone = ""
    submitted_by = ""
    assigned_to = ""
    qa_contact = ""
    estimated_time = 0.0
    remaining_time = 0.0
    actual_time = 0.0
    is_open = True

    cols = [
        'dtOpened', 'sTitle', 'dtLastUpdated',
        'sProject', 'sArea', 'sVersion',
        'sStatus', 'ixPriority', 'sFixFor',
        'sMilestone', 'sEmailAssignedTo', 'hrsOrigEst',
        'hrsCurrEst', 'hrsElapsed', 'plugin',
        'sEmailOpenedBy', 'fOpen',
    ]

    def __init__(self, backend, id):
        self.id = int(id)
        self.backend = backend
        self.__import_data()

    def __import_data(self):
        xml = self.backend.search(q=self.id, cols=','.join(self.cols))

        def get_child_value(e):
            return unicode(e.text)

        def get_date(str):
            return dateutil.parser.parse(str)

        case = xml.find('case')
        for e in case.findChildren():
            # Would love to replace this with a lambda construction, but python
            # lambdas aren't anywhere as useful as the ones in C#...
            if e.name == 'dtopened':
                self.created = get_date(get_child_value(e))
            elif e.name == 'stitle':
                self.summary = get_child_value(e)
            elif e.name == 'dtlastupdated':
                self.last_modified = get_date(get_child_value(e))
            elif e.name == 'sproject':
                self.product = get_child_value(e)
            elif e.name == 'sarea':
                self.component = get_child_value(e)
            elif e.name == 'sstatus':
                self.status = get_child_value(e)
            elif e.name == 'ixpriority':
                self.priority = int(get_child_value(e))
            elif e.name == 'sfixfor':
                self.milestone = get_child_value(e)
            # XXX: Can't actually get this!
            #elif e.name == 'spersonopenedby':
            #    self.submitted_by = get_child_value(e)
            elif e.name == 'semailassignedto':
                self.assigned_to = get_child_value(e)
            elif e.name == 'hrscurrest':
                self.estimated_time = int(ceil(float(get_child_value(e))))
            elif e.name == 'hrselapsed':
                self.actual_time = int(ceil(float(get_child_value(e))))
            elif e.name == 'fopen':
                self.is_open = get_child_value(e) == 'true'

        # If a bug is resolved or closed, there is no remaining time.  Yes,
        # this may hide some time (if a bug isn't fixed yet), but unless QA and
        # development are very tightly integrated such that bugs are being
        # closed very quickly, sprints will be completed with unnecessarily
        # high hour counts.  Also, this mirrors Bugzilla's behavior, for better
        # or worse.
        if not self.status.startswith('Resolved') and self.is_open:
            self.remaining_time = max(self.estimated_time - self.actual_time, 0)
        else:
            self.remaining_time = 0

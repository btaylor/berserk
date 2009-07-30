#
# Copyright (c) 2008-2009 Brad Taylor <brad@getcoded.net>
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

from time import strptime
from datetime import datetime
from xml.dom import minidom
import logging

class BugzillaClient:
    """
    A connection to Bugzilla
    """
    def __init__(self, base_url, backend_name):
        self.base_url = base_url
        klass = BugzillaClient.__get_backend(backend_name)
        self.backend = klass(self.base_url)

    @staticmethod
    def __get_backend(backend_name):
        import backends
        return getattr(backends, backend_name)

    @staticmethod
    def validate_backend(backend_name):
        """
        Returns True if the backend specified by backend_name exists under
        berserk2.bugzilla.backends and can be instantiated. False otherwise.
        """
        try:
            BugzillaClient.__get_backend(backend_name)
        except AttributeError:
            return False
        else:
            return True

    def login(self, user, password):
        """
        Authenticates the user against the remote Bugzilla instance.  Returns
        True if successful, False otherwise.
        """
        try:
            self.backend.login(user, password)
        except AssertionError, e:
            logging.error('Exception while logging in:\n%s' % e)
            return False
        else:
            return True

    def get_bug(self, bug_id):
        """
        Returns a BugzillaBug instance or a blank instance if bug_id could not
        be found or the Server could not be reached.
        """
        assert int(bug_id) > 0
        return BugzillaBug(self.backend, bug_id)

    def get_stats_for_milestone(self, product, milestone):
        """
        Returns a tuple containing the number of open bugs, total estimated
        hours and total remaining hours for the open bugs in the given
        milestone.
        """
        return self.backend.get_stats_for_milestone(product, milestone)
            

class BugzillaBug:
    """
    A Bugzilla bug
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

    def __init__(self, backend, id):
        self.id = int(id)
        self.backend = backend
        self.__import_data()

    def __import_data(self):
        resp = self.backend.get_bug_xml(self.id)
        xml = minidom.parseString(resp).documentElement

        def get_child_value(el):
            if len(el.childNodes) == 0: return None
            val = el.childNodes[0].nodeValue
            return str(val)

        def get_date(str, require_seconds=True):
            # Python can't parse the timezone correctly
            clean = ' '.join(str.split(' ')[:-1])
            if require_seconds:
                return datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
            else:
                return datetime.strptime(clean, "%Y-%m-%d %H:%M")

        bug = xml.getElementsByTagName('bug')[0]
        for e in bug.childNodes:
            if not e.nodeType == e.ELEMENT_NODE:
                continue

            if e.localName == 'creation_ts':
                self.created = get_date(get_child_value(e), require_seconds=False)
            elif e.localName == 'short_desc':
                self.summary = get_child_value(e)
            elif e.localName == 'delta_ts':
                self.last_modified = get_date(get_child_value(e))
            elif e.localName == 'product':
                self.product = get_child_value(e)
            elif e.localName == 'component':
                self.component = get_child_value(e)
            elif e.localName == 'version':
                self.version = get_child_value(e)
            elif e.localName == 'bug_status':
                self.status = get_child_value(e)
            elif e.localName == 'priority':
                self.priority = get_child_value(e)
            elif e.localName == 'bug_severity':
                self.severity = get_child_value(e)
            elif e.localName == 'target_milestone':
                self.milestone = get_child_value(e)
            elif e.localName == 'reporter':
                self.submitted_by = get_child_value(e)
            elif e.localName == 'assigned_to':
                self.assigned_to = get_child_value(e)
            elif e.localName == 'qa_contact':
                self.qa_contact = get_child_value(e)
            elif e.localName == 'estimated_time':
                self.estimated_time = float(get_child_value(e))
            elif e.localName == 'remaining_time':
                self.remaining_time = float(get_child_value(e))
            elif e.localName == 'actual_time':
                self.actual_time = float(get_child_value(e))

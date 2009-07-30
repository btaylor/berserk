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

import re
import csv
import twill
from twill import commands
from urllib import quote

class BugzillaBackend:
    """
    Abstract class representing a backend connection to Bugzilla.
    
    Every Bugzilla installation seems to have its own quirky modifications, so
    BugzillaBackend and its derivatives allow you to provide implementations
    for common Bugzilla tasks.
    """
    def __init__(self, base_url):
        self.base_url = base_url
        self.browser = twill.get_browser()

    def login(self, user, password):
        """
        Authenticates the user with the given password with the Bugzilla
        server.
        """
        raise NotImplementedException('login')

    def get_bug_xml(self, bug_id):
        """
        Returns the XML representing a bug specified by bug_id.
        """
        commands.go('%s/show_bug.cgi?id=%s&ctype=xml' % (self.base_url, bug_id))
        return self.browser.get_html()

    def get_stats_for_milestone(self, product, milestone):
        """
        Returns a tuple containing the number of open bugs, total estimated
        hours and total remaining hours for the open bugs in the given
        milestone.
        """
        commands.go('%s/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=NEEDINFO&bug_status=REOPENED&product=%s&target_milestone=%s&query_format=long&columnlist=estimated_time%%2Cremaining_time&ctype=csv' % (self.base_url, quote(product), quote(milestone)))
        csvstring = self.browser.get_html()
        reader = csv.DictReader(csvstring.split('\n'))

        open_bugs = 0
        estimated_hours = 0
        remaining_hours = 0
        for row in reader:
            open_bugs += 1
            estimated_hours += float(row['estimated_time'])
            remaining_hours += float(row['remaining_time'])

        return (open_bugs, estimated_hours, remaining_hours)


class NovellBugzillaBackend(BugzillaBackend):
    """
    Specifically handles Novell's iChain authentication scheme.
    """
    def login(self, user, password):
        def loggedin():
            return re.match(r"^Welcome to Novell's Bugzilla$", self.browser.get_title().strip())

        commands.go('https://bugzilla.novell.com/ICSLogin/?"https://bugzilla.novell.com/ichainlogin.cgi?target=index.cgi?GoAheadAndLogIn%3D1"')
        if loggedin():
            return

        commands.formvalue('loginfrm', 'username', user)
        commands.formvalue('loginfrm', 'password', password)
        commands.submit('0')
        assert loggedin()

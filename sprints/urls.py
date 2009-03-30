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

from django.conf.urls.defaults import *

urlpatterns = patterns('sprints.views',
    url(r'^$', 'sprint_index'),
    url(r'^(?P<sprint_id>\d+)/$', 'sprint_detail', name="sprint_detail"),
    url(r'^(?P<sprint_id>\d+)/edit/$', 'sprint_edit'),

    # JSON query methods
    url(r'^(?P<sprint_id>\d+)/load_effort/json/$', 'sprint_load_effort_json'),
    url(r'^(?P<sprint_id>\d+)/tasks/json/$', 'sprint_tasks_json'),
    url(r'^(?P<sprint_id>\d+)/my-tasks/json/$', 'sprint_my_tasks_json'),
    url(r'^(?P<sprint_id>\d+)/burndown/json/$', 'sprint_burndown_json'),
)
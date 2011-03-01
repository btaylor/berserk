from django.db import models

class Event:
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    plugin = models.CharField(max_length=32)
    protagonist = models.ForeignKey(User, related_name='protagonist',
                                    null=True, db_index=True)
    deuteragonist = models.ForeignKey(User, related_name='deuteragonist',
                                      null=True, db_index=True)
    message = models.CharField()

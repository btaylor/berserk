# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Actor'
        db.create_table('timeline_actor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('gender', self.gf('django.db.models.fields.CharField')(default='U', max_length=1)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('timeline', ['Actor'])

        # Adding model 'Event'
        db.create_table('timeline_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('protagonist', self.gf('django.db.models.fields.related.ForeignKey')(related_name='protagonist', null=True, to=orm['timeline.Actor'])),
            ('deuteragonist', self.gf('django.db.models.fields.related.ForeignKey')(related_name='deuteragonist', null=True, to=orm['timeline.Actor'])),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='task', null=True, to=orm['sprints.Task'])),
        ))
        db.send_create_signal('timeline', ['Event'])


    def backwards(self, orm):
        
        # Deleting model 'Actor'
        db.delete_table('timeline_actor')

        # Deleting model 'Event'
        db.delete_table('timeline_event')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sprints.bugtracker': {
            'Meta': {'unique_together': "(('base_url', 'product', 'backend'),)", 'object_name': 'BugTracker'},
            'backend': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'product': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'sprints.milestone': {
            'Meta': {'object_name': 'Milestone'},
            'bug_tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.BugTracker']"}),
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'remote_tracker_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'sprints.sprint': {
            'Meta': {'ordering': "['-end_date']", 'object_name': 'Sprint'},
            'default_bug_tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.BugTracker']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.Milestone']", 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'velocity': ('django.db.models.fields.IntegerField', [], {'default': '6'})
        },
        'sprints.task': {
            'Meta': {'unique_together': "(('remote_tracker_id', 'bug_tracker'),)", 'object_name': 'Task'},
            'bug_tracker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sprints.BugTracker']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remote_tracker_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'sprints': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sprints.Sprint']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'timeline.actor': {
            'Meta': {'object_name': 'Actor'},
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'timeline.event': {
            'Meta': {'object_name': 'Event'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'deuteragonist': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'deuteragonist'", 'null': 'True', 'to': "orm['timeline.Actor']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'protagonist': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'protagonist'", 'null': 'True', 'to': "orm['timeline.Actor']"}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'task'", 'null': 'True', 'to': "orm['sprints.Task']"})
        }
    }

    complete_apps = ['timeline']

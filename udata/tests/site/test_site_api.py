# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from flask import url_for

from udata.core.jobs.models import PeriodicTask
from udata.core.site.metrics import SiteMetric
from udata.core.site.views import current_site
from udata.models import db, WithMetrics
from udata.tasks import celery, job

from udata.tests.api import APITestCase
from udata.tests.factories import faker, AdminFactory


class FakeModel(db.Document, WithMetrics):
    name = db.StringField()


class FakeSiteMetric(SiteMetric):
    name = 'fake-site-metric'
    display_name = 'Fake site metric'
    default = 0

    def get_value(self):
        return 2


class MetricsAPITest(APITestCase):
    def test_get_metrics_for_site(self):
        '''It should fetch my user data on GET'''
        with self.app.app_context():
            FakeSiteMetric.update()

        response = self.get(url_for('api.metrics', id='site'))
        self.assert200(response)

        data = response.json[0]
        self.assertEqual(data['level'], 'daily')
        self.assertEqual(data['date'], date.today().isoformat())
        self.assertEqual(len(data['values']), 1)
        self.assertEqual(data['values']['fake-site-metric'], 2)


class JobsAPITest(APITestCase):
    def test_schedulable_jobs_list(self):
        @celery.task(name='a-schedulable-job', schedulable=True)
        def test_job():
            pass

        response = self.get(url_for('api.schedulable_jobs'))
        self.assert200(response)
        self.assertIn('a-schedulable-job', response.json)

    def test_schedulable_jobs_list_with_decorator(self):
        @job('a-job')
        def test_job():
            pass

        response = self.get(url_for('api.schedulable_jobs'))
        self.assert200(response)
        self.assertIn('a-job', response.json)

    def test_scheduled_jobs_list(self):
        @job('a-job')
        def test_job():
            pass

        for i in range(6):
            params = {
                'name': faker.name(),
                'description': faker.sentence(),
                'task': 'a-job'
            }
            if i % 2:
                params['crontab'] = PeriodicTask.Crontab(minutes=i)
            else:
                params['interval'] = PeriodicTask.Interval(every=i, period='minutes')
            PeriodicTask.objects.create(**params)

        response = self.get(url_for('api.jobs'))
        self.assert200(response)

    def test_create_job_need_admin(self):
        @job('a-job')
        def test_job():
            pass

        data = {
            'name': 'A crontab job',
            'description': 'A simple crontab job doing nothing',
            'task': 'a-job',
        }

        self.login()
        response = self.post(url_for('api.jobs'), data)
        self.assert403(response)

    def test_create_crontab_job(self):
        @job('a-job')
        def test_job():
            pass

        data = {
            'name': 'A crontab job',
            'description': 'A simple crontab job doing nothing',
            'task': 'a-job',
            'crontab': {
                'minute': '0',
                'hour': '0'
            }
        }

        self.login(AdminFactory())
        response = self.post(url_for('api.jobs'), data)
        self.assert201(response)

        self.assertEqual(response.json['name'], data['name'])
        self.assertEqual(response.json['description'], data['description'])
        self.assertEqual(response.json['task'], data['task'])
        self.assertEqual(response.json['crontab'], {
            'minute': '0',
            'hour': '0',
            'day_of_week': '*',
            'day_of_month': '*',
            'month_of_year': '*',
        })

    def test_create_interval_job(self):
        @job('a-job')
        def test_job():
            pass

        data = {
            'name': 'An interval job',
            'description': 'A simple interval job doing nothing',
            'task': 'a-job',
            'interval': {
                'every': 5,
                'period': 'minutes'
            }
        }

        self.login(AdminFactory())
        response = self.post(url_for('api.jobs'), data)
        self.assert201(response)

        self.assertEqual(response.json['name'], data['name'])
        self.assertEqual(response.json['description'], data['description'])
        self.assertEqual(response.json['task'], data['task'])
        self.assertEqual(response.json['interval'], data['interval'])

    def test_fail_on_create_with_both_crontab_and_interval(self):
        @job('a-job')
        def test_job():
            pass

        data = {
            'name': 'A mixed job',
            'description': 'A simple crontab job doing nothing',
            'task': 'a-job',
            'crontab': {
                'minute': '0',
                'hour': '0'
            },
            'interval': {
                'every': 5,
                'period': 'minutes'
            }
        }

        self.login(AdminFactory())
        response = self.post(url_for('api.jobs'), data)
        self.assertStatus(response, 400)

    def test_create_manual_job(self):
        pass

    def test_get_job(self):
        @job('a-job')
        def test_job():
            pass

        task = PeriodicTask.objects.create(
            name=faker.name(),
            description=faker.sentence(),
            task='a-job',
            crontab=PeriodicTask.Crontab(minutes=5)
        )

        response = self.get(url_for('api.job', id=task.id))
        self.assert200(response)
        self.assertEqual(response.json['id'], str(task.id))
        self.assertEqual(response.json['name'], task.name)
        self.assertEqual(response.json['description'], task.description)
        self.assertEqual(response.json['task'], task.task)

    def test_update_job_need_admin(self):
        @job('a-job')
        def test_job():
            pass

        task = PeriodicTask.objects.create(
            name=faker.name(),
            description=faker.sentence(),
            task='a-job',
            crontab=PeriodicTask.Crontab(minutes=5)
        )

        self.login()
        response = self.put(url_for('api.job', id=task.id), {
            'name': task.name,
            'description': 'New description',
            'task': task.task,
            'crontab': task.crontab._data
        })
        self.assert403(response)

    def test_update_job(self):
        @job('a-job')
        def test_job():
            pass

        task = PeriodicTask.objects.create(
            name=faker.name(),
            description=faker.sentence(),
            task='a-job',
            crontab=PeriodicTask.Crontab(minutes=5)
        )

        self.login(AdminFactory())
        response = self.put(url_for('api.job', id=task.id), {
            'name': task.name,
            'description': 'New description',
            'task': task.task,
            'crontab': task.crontab._data
        })
        self.assert200(response)

        self.assertEqual(response.json['id'], str(task.id))
        self.assertEqual(response.json['name'], task.name)
        self.assertEqual(response.json['task'], task.task)
        self.assertEqual(response.json['description'], 'New description')
        self.assertIsNotNone(response.json['crontab'])
        self.assertIsNone(response.json['interval'])

    def test_update_job_change_type(self):
        @job('a-job')
        def test_job():
            pass

        task = PeriodicTask.objects.create(
            name=faker.name(),
            description=faker.sentence(),
            task='a-job',
            crontab=PeriodicTask.Crontab(minutes=5)
        )

        self.login(AdminFactory())
        response = self.put(url_for('api.job', id=task.id), {
            'name': task.name,
            'description': task.description,
            'task': task.task,
            'interval': {
                'every': 5,
                'period': 'minutes',
            }
        })
        self.assert200(response)

        self.assertEqual(response.json['id'], str(task.id))
        self.assertEqual(response.json['name'], task.name)
        self.assertEqual(response.json['task'], task.task)
        self.assertEqual(response.json['description'], task.description)
        self.assertEqual(response.json['interval']['every'], 5)
        self.assertEqual(response.json['interval']['period'], 'minutes')
        self.assertIsNone(response.json['crontab'])

    def test_delete_job_need_admin(self):
        @job('a-job')
        def test_job():
            pass

        task = PeriodicTask.objects.create(
            name=faker.name(),
            description=faker.sentence(),
            task='a-job',
            crontab=PeriodicTask.Crontab(minutes=5)
        )

        self.login()
        response = self.delete(url_for('api.job', id=task.id))
        self.assert403(response)

    def test_delete_job(self):
        @job('a-job')
        def test_job():
            pass

        task = PeriodicTask.objects.create(
            name=faker.name(),
            description=faker.sentence(),
            task='a-job',
            crontab=PeriodicTask.Crontab(minutes=5)
        )

        self.login(AdminFactory())
        response = self.delete(url_for('api.job', id=task.id))
        self.assert204(response)

        self.assertIsNone(PeriodicTask.objects(id=task.id).first())

    def test_get_task(self):
        @celery.task
        def test_task():
            print 'hello'

        result = test_task.delay()  # Always eager so no async

        response = self.get(url_for('api.task', id=result.id))
        self.assert200(response)
        self.assertEqual(response.json['id'], result.id)


class SiteAPITest(APITestCase):
    def test_get_site(self):
        response = self.get(url_for('api.site'))
        self.assert200(response)

    # def test_update_site(self):
    #     self.login(AdminFactory())
    #     response = self.put(url_for('api.site'))
    #     self.assert200(response)

    # def test_get_site_permissions(self):
    #     response = self.put(url_for('api.site'))
    #     self.assert403(response)
    #     # self.assertEqual(response.json['id'], result.id)

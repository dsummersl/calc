from django.apps import AppConfig

import django_rq

from . import periodic_jobs


class DataCaptureAppConfig(AppConfig):
    name = 'data_capture'
    verbose_name = 'CALC Data Capture'
    rq_queue_name = 'default'

    # every Monday at noon, but scheduler uses UTC so it will be 5AM Pacific
    admin_reminder_cron = '* 12 * * MON'

    def ready(self):
        scheduler = django_rq.get_scheduler(self.rq_queue_name)

        #  Because the ready() method will be run for each insantiation
        #  of the app (ie, app, rqworker, and rqscheduler)
        #  we first cancel all of the scheduled jobs
        # ref: https://github.com/ui/django-rq/issues/42#issuecomment-131505434
        for job in scheduler.get_jobs():
            scheduler.cancel(job)

        # The last app instantiation's scheduler will have this cron job
        # scheduled and not deleted
        scheduler.cron(self.admin_reminder_cron,
                       periodic_jobs.send_admin_approval_reminder_email)

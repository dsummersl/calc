import logging
from django.apps import AppConfig

import django_rq

logger = logging.getLogger(__name__)


class DataCaptureSchedulerApp(AppConfig):
    name = 'data_capture'
    verbose_name = 'CALC Data Capture RQ Scheduler'

    # every Monday at noon, but scheduler uses UTC so it will be 5AM Pacific
    admin_reminder_cron = '* 12 * * MON'
    rq_queue_name = 'default'

    def ready(self):
        # Import needs to happen after app is ready
        from . import periodic_jobs

        scheduler = django_rq.get_scheduler(self.rq_queue_name)

        # Cancel any jobs already in the scheduler. Jobs can be left dangling
        # from any restart of this custom AppConfig.
        for job in scheduler.get_jobs():
            scheduler.cancel(job)

        # Add cron-type job to send a reminder email to the CALC admins
        # about approving price lists
        logger.info('Adding send_admin_approval_reminder_email job on cron \
          schedule "{}"'.format(self.admin_reminder_cron))
        scheduler.cron(self.admin_reminder_cron,
                       periodic_jobs.send_admin_approval_reminder_email)

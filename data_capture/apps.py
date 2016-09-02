import logging
from django.apps import AppConfig

import django_rq

from . import periodic_jobs

logger = logging.getLogger(__name__)


class DataCaptureSchedulerApp(AppConfig):
    name = 'data_capture'
    verbose_name = 'CALC Data Capture RQ Scheduler'

    # every Monday at noon, but scheduler uses UTC so it will be 5AM Pacific
    admin_reminder_cron = '* 12 * * MON'
    rq_queue_name = 'default'

    def ready(self):
        scheduler = django_rq.get_scheduler(self.rq_queue_name)

        # Add cron-type job to send a reminder email to the CALC admins
        # about approving price lists
        logger.info('Adding send_admin_approval_reminder_email job on cron \
          schedule "{}"'.format(self.admin_reminder_cron))
        scheduler.cron(self.admin_reminder_cron,
                       periodic_jobs.send_admin_approval_reminder_email)

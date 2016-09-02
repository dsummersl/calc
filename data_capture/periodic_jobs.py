import logging

from . import email
from .models import SubmittedPriceList

logger = logging.getLogger(__name__)


def send_admin_approval_reminder_email(threshold=10):
    # TODO: Since SubmittedPriceLists can be unapproved, perhaps
    # we need to store an additional flag on that model to indicate
    # if it has ever been manually unapproved so that we don't bug
    # the admin with things that have been unapproved
    logger.info('Processing period reminder about unapproved Price Lists')

    count_not_approved = SubmittedPriceList.objects.filter(
        is_approved=False).count()

    if count_not_approved >= threshold:
        logger.info('Number unapproved is greater than {}, \
            sending reminder email'.format(threshold))
        email.approval_reminder(count_not_approved)

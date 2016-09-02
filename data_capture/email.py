from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.conf import settings
from django.template.defaultfilters import pluralize


class EmailResult():
    '''
    Simple class to hold result data from email sending functions
    '''
    def __init__(self, was_successful, context={}):
        self.was_successful = was_successful
        self.context = context


def price_list_approved(price_list):
    ctx = {
        'price_list': price_list
    }
    if not price_list.is_approved:
        raise AssertionError('price_list.is_approved must be True')

    result = send_mail(
        subject='CALC Price List Approved',
        message=render_to_string(
            'data_capture/email/price_list_approved.txt',
            ctx),
        from_email=settings.SYSTEM_EMAIL_ADDRESS,
        recipient_list=[price_list.submitter.email]
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def price_list_unapproved(price_list):
    ctx = {
        'price_list': price_list
    }
    if price_list.is_approved:
        raise AssertionError('price_list.is_approved must be False')
    result = send_mail(
        subject='CALC Price List Unapproved',
        message=render_to_string(
            'data_capture/email/price_list_unapproved.txt',
            ctx),
        from_email=settings.SYSTEM_EMAIL_ADDRESS,
        recipient_list=[price_list.submitter.email]
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def bulk_upload_succeeded(upload_source, num_contracts, num_bad_rows):
    ctx = {
        'upload_source': upload_source,
        'num_contracts': num_contracts,
        'num_bad_rows': num_bad_rows,
    }
    result = send_mail(
        subject='CALC Region 10 bulk data results - upload #%d' % (
            upload_source.id,
        ),
        message=render_to_string(
            'data_capture/email/bulk_upload_succeeded.txt',
            ctx
        ),
        from_email=settings.SYSTEM_EMAIL_ADDRESS,
        recipient_list=[upload_source.submitter.email]
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def bulk_upload_failed(upload_source, traceback):
    ctx = {
        'upload_source': upload_source,
        'traceback': traceback,
    }
    result = send_mail(
        subject='CALC Region 10 bulk data results - upload #%d' % (
            upload_source.id,
        ),
        message=render_to_string(
            'data_capture/email/bulk_upload_failed.txt',
            ctx
        ),
        from_email=settings.SYSTEM_EMAIL_ADDRESS,
        recipient_list=[upload_source.submitter.email]
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def approval_reminder(count_not_approved):
    ctx = {
        'count_not_approved': count_not_approved
    }
    superusers = User.objects.filter(is_superuser=True)
    recipients = [s.email for s in superusers if s.email]
    result = send_mail(
        subject='CALC Reminder - {} price list{} not approved'.format(
            count_not_approved, pluralize(count_not_approved)),
        message=render_to_string(
            'data_capture/email/approval_reminder.txt',
            ctx
        ),
        from_email=settings.SYSTEM_EMAIL_ADDRESS,
        recipient_list=recipients
    )
    return EmailResult(
        was_successful=result is 1,  # or count of superusers
        context=ctx
    )

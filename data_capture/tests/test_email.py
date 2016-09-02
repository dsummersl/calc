from django.core import mail
from django.conf import settings
from django.test import override_settings
from django.contrib.auth.models import User

from .. import email
from .common import create_bulk_upload_contract_source, FAKE_SCHEDULE
from .test_models import ModelTestCase


@override_settings(DATA_CAPTURE_SCHEDULES=[FAKE_SCHEDULE])
class EmailTests(ModelTestCase):
    '''Tests for email sending functions'''

    def test_price_list_approved(self):
        price_list = self.create_price_list(is_approved=True)

        result = email.price_list_approved(price_list)
        self.assertTrue(result.was_successful)
        message = mail.outbox[0]
        self.assertEqual(message.recipients(), [self.user.email])
        self.assertEqual(message.subject, 'CALC Price List Approved')
        self.assertEqual(message.from_email, settings.SYSTEM_EMAIL_ADDRESS)
        self.assertEqual(result.context['price_list'], price_list)

    def test_price_list_approved_raises_if_not_approved(self):
        price_list = self.create_price_list(is_approved=False)
        with self.assertRaises(AssertionError):
            email.price_list_approved(price_list)

    def test_price_list_unapproved(self):
        price_list = self.create_price_list(is_approved=False)

        result = email.price_list_unapproved(price_list)
        self.assertTrue(result.was_successful)
        message = mail.outbox[0]
        self.assertEqual(message.recipients(), [self.user.email])
        self.assertEqual(message.subject, 'CALC Price List Unapproved')
        self.assertEqual(message.from_email, settings.SYSTEM_EMAIL_ADDRESS)
        self.assertEqual(result.context['price_list'], price_list)

    def test_price_list_unapproved_raises_if_approved(self):
        price_list = self.create_price_list(is_approved=True)
        with self.assertRaises(AssertionError):
            email.price_list_unapproved(price_list)

    def test_bulk_uploaded_succeeded(self):
        src = create_bulk_upload_contract_source(self.user)
        result = email.bulk_upload_succeeded(src, 5, 2)
        self.assertTrue(result.was_successful)
        message = mail.outbox[0]
        self.assertEqual(message.recipients(), [self.user.email])
        self.assertEqual(
            message.subject,
            'CALC Region 10 bulk data results - upload #{}'.format(src.pk))
        self.assertEqual(message.from_email, settings.SYSTEM_EMAIL_ADDRESS)
        self.assertEqual(result.context['num_contracts'], 5)
        self.assertEqual(result.context['num_bad_rows'], 2)

    def test_bulk_upload_failed(self):
        src = create_bulk_upload_contract_source(self.user)
        result = email.bulk_upload_failed(src, 'traceback_contents')
        self.assertTrue(result.was_successful)
        message = mail.outbox[0]
        self.assertEqual(message.recipients(), [self.user.email])
        self.assertEqual(
            message.subject,
            'CALC Region 10 bulk data results - upload #{}'.format(src.pk))
        self.assertEqual(message.from_email, settings.SYSTEM_EMAIL_ADDRESS)
        self.assertEqual(result.context['traceback'], 'traceback_contents')

    @override_settings(ADMIN_EMAIL='admin@localhost')
    def test_approval_reminder(self):
        User.objects.create_superuser('admin', 'admin@localhost', 'password')
        User.objects.create_superuser('admin2', 'admin2@localhost', 'password')
        User.objects.create_superuser('blankadmin', '', 'password')
        count = 5
        result = email.approval_reminder(count)
        self.assertTrue(result.was_successful)
        message = mail.outbox[0]
        self.assertEqual(message.recipients(),
                         ['admin@localhost', 'admin2@localhost'])
        self.assertEqual(
            message.subject,
            'CALC Reminder - {} price lists not approved'.format(count)
        )
        self.assertEqual(message.from_email, settings.SYSTEM_EMAIL_ADDRESS)
        self.assertEqual(result.context['count_not_approved'], count)

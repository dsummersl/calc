import unittest
import json
from unittest.mock import patch
from django.test import TestCase as DjangoTestCase
from django.test import override_settings

from . import healthcheck
from .settings_utils import (load_cups_from_vcap_services,
                             load_redis_url_from_vcap_services,
                             get_whitelisted_ips)


class ComplianceTests(DjangoTestCase):
    '''
    These tests ensure our site is configured with proper regulatory
    compliance and security best practices.  For more information, see:

    https://compliance-viewer.18f.gov/

    Cloud.gov's nginx proxy adds the required headers to 200 responses, but
    not to responses with error codes, so we need to add them at the app-level.
    '''

    headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
    }

    def assertHasHeaders(self, res):
        for header, val in self.headers.items():
            self.assertEqual(res[header], val)

    @override_settings(SECURITY_HEADERS_ON_ERROR_ONLY=False)
    def test_has_security_headers(self):
        res = self.client.get('/')
        self.assertHasHeaders(res)

    @override_settings(SECURITY_HEADERS_ON_ERROR_ONLY=False)
    def test_has_security_headers_on_404(self):
        res = self.client.get('/i-am-a-nonexistent-page')
        self.assertHasHeaders(res)

    @override_settings(SECURITY_HEADERS_ON_ERROR_ONLY=True)
    def test_no_security_headers_when_setting_enabled(self):
        res = self.client.get('/')
        for header, val in self.headers.items():
            self.assertNotIn(header, res)

    @override_settings(SECURITY_HEADERS_ON_ERROR_ONLY=True)
    def test_has_security_headers_on_404_when_setting_enabled(self):
        res = self.client.get('/i-am-a-nonexistent-page')
        self.assertHasHeaders(res)


class HealthcheckTests(DjangoTestCase):
    def test_it_works(self):
        res = self.client.get('/healthcheck/')
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(str(res.content, encoding='utf8'), {
            'is_database_synchronized': True,
            'rq_jobs': 0
        })

    @patch.object(healthcheck, 'is_database_synchronized')
    def test_it_returns_500_when_db_is_not_synchronized(self, mock):
        mock.return_value = False
        res = self.client.get('/healthcheck/')
        self.assertEqual(res.status_code, 500)
        self.assertJSONEqual(str(res.content, encoding='utf8'), {
            'is_database_synchronized': False,
            'rq_jobs': 0
        })


class RobotsTests(DjangoTestCase):

    @override_settings(ENABLE_SEO_INDEXING=False)
    def test_disable_seo_indexing_works(self):
        res = self.client.get('/robots.txt')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b"User-agent: *\nDisallow: /")

    @override_settings(ENABLE_SEO_INDEXING=True)
    def test_enable_seo_indexing_works(self):
        res = self.client.get('/robots.txt')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b"User-agent: *\nDisallow:")


def make_vcap_services_env(vcap_services):
    return {
        'VCAP_SERVICES': json.dumps(vcap_services)
    }


class CupsTests(unittest.TestCase):

    def test_noop_if_vcap_services_not_in_env(self):
        env = {}
        load_cups_from_vcap_services('blah', env=env)
        self.assertEqual(env, {})

    def test_irrelevant_cups_are_ignored(self):
        env = make_vcap_services_env({
            "user-provided": [
                {
                    "label": "user-provided",
                    "name": "NOT-boop-env",
                    "syslog_drain_url": "",
                    "credentials": {
                        "boop": "jones"
                    },
                    "tags": []
                }
            ]
        })

        load_cups_from_vcap_services('boop-env', env=env)

        self.assertFalse('boop' in env)

    def test_credentials_are_loaded(self):
        env = make_vcap_services_env({
            "user-provided": [
                {
                    "label": "user-provided",
                    "name": "boop-env",
                    "syslog_drain_url": "",
                    "credentials": {
                        "boop": "jones"
                    },
                    "tags": []
                }
            ]
        })

        load_cups_from_vcap_services('boop-env', env=env)

        self.assertEqual(env['boop'], 'jones')


class RedisUrlTests(unittest.TestCase):
    def test_noop_when_vcap_not_in_env(self):
        env = {}
        load_redis_url_from_vcap_services('redis-service', env=env)
        self.assertEqual(env, {})

    def test_noop_when_name_not_in_vcap(self):
        env = make_vcap_services_env({
            'redis28-swarm': [{
                'name': 'a-different-name',
                'credentials': {
                    'hostname': 'the_host',
                    'password': 'the_password',
                    'port': '1234'
                }
            }]
        })
        load_redis_url_from_vcap_services('boop')
        self.assertFalse('REDIS_URL' in env)

    def test_redis_url_is_loaded(self):
        env = make_vcap_services_env({
            'redis28-swarm': [{
                'name': 'redis-service',
                'credentials': {
                    'hostname': 'the_host',
                    'password': 'the_password',
                    'port': '1234'
                }
            }]
        })

        load_redis_url_from_vcap_services('redis-service', env=env)
        self.assertTrue('REDIS_URL' in env)
        self.assertEqual(env['REDIS_URL'],
                         'redis://:the_password@the_host:1234')


class GetWhitelistedIPsTest(unittest.TestCase):

    def test_returns_none_when_not_in_env(self):
        env = {}
        self.assertIsNone(get_whitelisted_ips(env))

    def test_returns_whitelisted_ips_list(self):
        env = {
            'WHITELISTED_IPS': '1.2.3.4,1.2.3.8, 1.2.3.16'
        }
        ips = get_whitelisted_ips(env)
        self.assertListEqual(ips, ['1.2.3.4', '1.2.3.8', '1.2.3.16'])

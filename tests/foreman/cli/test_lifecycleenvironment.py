# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Host CLI"""

from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import make_lifecycle_environment, make_org
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.constants import ENVIRONMENT
from robottelo.decorators import run_only_on
from robottelo.helpers import valid_data_list
from robottelo.test import CLITestCase


@run_only_on('sat')
class TestLifeCycleEnvironment(CLITestCase):
    """Test class for Lifecycle Environment CLI"""

    org = None

    def setUp(self):
        """Tests for Lifecycle Environment via Hammer CLI"""

        super(TestLifeCycleEnvironment, self).setUp()

        if TestLifeCycleEnvironment.org is None:
            TestLifeCycleEnvironment.org = make_org()

    # Issues validation
    def test_bugzilla_1077386(self):
        """@Test: List subcommand returns standard output

        @Feature: Lifecycle Environment

        @Assert: There should not be an error returned

        """

        # List available lifecycle environments using default Table
        # output
        cmd = u'lifecycle-environment list --organization-id="%s"'
        result = LifecycleEnvironment.execute(
            cmd % self.org['id'],
            None,
            None,
            False,
        )
        self.assertGreater(len(result), 0)

    def test_bugzilla_1077333(self):
        """@Test: Search lifecycle environment via its name containing UTF-8
        chars

        @Feature: Lifecycle Environment

        @Assert: Can get info for lifecycle by its name

        """
        test_data = {
            'name': gen_string('utf8', 15),
            'organization-id': self.org['id'],
        }
        # Can we find the new object
        result = LifecycleEnvironment.info({
            'name': make_lifecycle_environment(test_data)['name'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(result['name'], test_data['name'])

    # CRUD
    def test_positive_create_1(self):
        """@Test: Create lifecycle environment with valid name, prior to
        Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created with Library as prior

        """
        for name in valid_data_list():
            with self.subTest(name):
                lc_env = make_lifecycle_environment({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                self.assertEqual(
                    lc_env['prior-lifecycle-environment'], ENVIRONMENT)

    def test_positive_create_2(self):
        """@Test: Create lifecycle environment with valid description prior to
        Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created with Library as prior

        """
        for desc in valid_data_list():
            name = gen_alphanumeric()
            with self.subTest(desc):
                lc_env = make_lifecycle_environment({
                    'description': desc,
                    'name': name,
                    'organization-id': self.org['id'],
                })
                self.assertEqual(lc_env['name'], name)
                self.assertEqual(lc_env['description'], desc)
                self.assertEqual(
                    lc_env['prior-lifecycle-environment'], ENVIRONMENT)

    def test_create_lifecycle_environment_by_label(self):
        """@Test: Create lifecycle environment with valid name and label

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment with label is created

        """
        for label in (gen_string("alpha", 15), gen_string("alphanumeric", 15),
                      gen_string("numeric", 15)):
            with self.subTest(label):
                new_lce = make_lifecycle_environment({
                    'label': label,
                    'name': gen_alphanumeric(),
                    'organization-id': self.org['id'],
                })
                self.assertEqual(new_lce['label'], label)

    def test_create_lifecycle_environment_by_organization_name(self):
        """@Test: Create lifecycle environment, specifying organization name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created for correct organization

        """
        new_lce = make_lifecycle_environment({
            'name': gen_string('alpha'),
            'organization': self.org['name'],
        })
        self.assertEqual(new_lce['organization'], self.org['name'])

    def test_create_lifecycle_environment_by_organization_label(self):
        """@Test: Create lifecycle environment, specifying organization label

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is created for correct organization

        """
        new_lce = make_lifecycle_environment({
            'name': gen_string('alpha'),
            'organization-label': self.org['label'],
        })
        self.assertEqual(new_lce['organization'], self.org['name'])

    def test_positive_delete_1(self):
        """@Test: Create lifecycle environment with valid name, prior to
        Library

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment is deleted

        """
        for name in valid_data_list():
            with self.subTest(name):
                new_lce = make_lifecycle_environment({
                    'name': name,
                    'organization-id': self.org['id'],
                })
                LifecycleEnvironment.delete({'id': new_lce['id']})
                with self.assertRaises(CLIReturnCodeError):
                    LifecycleEnvironment.info({
                        'id': new_lce['id'],
                        'organization-id': self.org['id'],
                    })

    def test_positive_update_1(self):
        """@Test: Create lifecycle environment then update its name

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment name is updated

        """
        new_lce = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })
        for new_name in valid_data_list():
            with self.subTest(new_name):
                LifecycleEnvironment.update({
                    'id': new_lce['id'],
                    'new-name': new_name,
                    'organization-id': self.org['id'],
                    'prior': new_lce['prior-lifecycle-environment'],
                })
                result = LifecycleEnvironment.info({
                    'id': new_lce['id'],
                    'organization-id': self.org['id'],
                })
                self.assertGreater(len(result), 0)
                self.assertEqual(result['name'], new_name)

    def test_positive_update_2(self):
        """@Test: Create lifecycle environment then update its description

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment description is updated

        """
        new_lce = make_lifecycle_environment({
            'organization-id': self.org['id'],
        })
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                LifecycleEnvironment.update({
                    'description': new_desc,
                    'id': new_lce['id'],
                    'organization-id': self.org['id'],
                    'prior': new_lce['prior-lifecycle-environment'],
                })
                result = LifecycleEnvironment.info({
                    'id': new_lce['id'],
                    'organization-id': self.org['id'],
                })
                self.assertGreater(len(result), 0)
                self.assertEqual(result['description'], new_desc)

    def test_environment_paths(self):
        """@Test: List the environment paths under a given organization

        @Feature: Lifecycle Environment

        @Assert: Lifecycle environment paths listed

        """
        org = make_org()
        lc_env = make_lifecycle_environment({
            'organization-id': org['id'],
        })
        # Add paths to lifecycle environments
        result = LifecycleEnvironment.paths({
            'organization-id': org['id'],
            'permission-type': 'readable',
        })
        self.assertIn(
            u'Library >> {0}'.format(lc_env['name']),
            u''.join(result)
        )

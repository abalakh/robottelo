"""Unit tests for the ``content_view_versions`` paths."""
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.api.utils import promote
from robottelo.constants import (
    FAKE_1_YUM_REPO,
    PUPPET_MODULE_NTP_PUPPETLABS,
    ZOO_CUSTOM_GPG_KEY,
)
from robottelo.helpers import get_data_file, read_data_file
from robottelo.test import APITestCase


class CVVersionTestCase(APITestCase):
    """Tests for content view versions."""

    def test_negative_promote_1(self):
        """@Test: Promote the default content view version.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        env = entities.Environment().create()
        with self.assertRaises(HTTPError):
            promote(entities.ContentViewVersion(id=1), env.id)

    def test_negative_promote_2(self):
        """@Test: Promote a content view version using an invalid environment.

        @Assert: The promotion fails.

        @Feature: ContentViewVersion

        """
        with self.assertRaises(HTTPError):
            promote(entities.ContentViewVersion(id=1), -1)

    def test_delete_version(self):
        """@Test: Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'delete_from_environment' command and delete content view version from
        that content view. Add repository and gpg key to initial content view
        for better coverage

        @Assert: Content version deleted successfully

        @Feature: ContentViewVersion

        """
        key_content = read_data_file(ZOO_CUSTOM_GPG_KEY)
        org = entities.Organization().create()
        gpgkey = entities.GPGKey(
            content=key_content,
            organization=org,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(organization=org).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            gpg_key=gpgkey,
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # sync repository
        repo.sync()
        # Create content view
        content_view = entities.ContentView(organization=org).create()
        # Associate repository to new content view
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        # Get published content-view version id
        self.assertEqual(len(content_view.version), 1)
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 1)
        # Delete the content-view version from selected env
        content_view.delete_from_environment(cvv.environment[0].id)
        # Delete the version
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    def test_delete_version_non_default(self):
        """@Test: Create content view and publish and promote it to new
        environment. After that try to disassociate content view from 'Library'
        and one more non-default environments through 'delete_from_environment'
        command and delete content view version from that content view.

        @Assert: Content view version deleted successfully

        @Feature: ContentViewVersion

        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.version[0].read().environment), 1)
        lce = entities.LifecycleEnvironment(organization=org).create()
        promote(content_view.version[0], lce.id)
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 2)
        # Delete the content-view version from selected environments
        for env in reversed(cvv.environment):
            content_view.delete_from_environment(env.id)
        content_view.version[0].delete()
        # Make sure that content view version is really removed
        self.assertEqual(len(content_view.read().version), 0)

    def test_delete_version_negative(self):
        """@Test: Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        @Assert: Content view version is not deleted

        @Feature: ContentViewVersion

        """
        org = entities.Organization().create()
        content_view = entities.ContentView(organization=org).create()
        # Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        with self.assertRaises(HTTPError):
            content_view.version[0].delete()
        # Make sure that content view version is still present
        self.assertEqual(len(content_view.read().version), 1)

    def test_incremental_update_puppet(self):
        """@Test: Incrementally update a CVV with a puppet module.

        @Assert: The the incremental update succeeds with no errors, and the
        content view is given an additional version.

        @Feature: ContentViewVersion

        """
        # Create a content view and add a yum repository to it. Publish the CV.
        product = entities.Product().create()
        yum_repo = entities.Repository(
            content_type='yum',
            product=product,
        ).create()
        content_view = entities.ContentView(
            organization=product.organization,
            repository=[yum_repo],
        ).create()
        content_view.publish()
        content_view = content_view.read()

        # Create a puppet repository and upload a puppet module into it.
        puppet_repo = entities.Repository(
            content_type='puppet',
            product=product,
        ).create()
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            puppet_repo.upload_content(files={'content': handle})
        # Extract all the available puppet modules.
        puppet_modules = content_view.available_puppet_modules()['results']
        # Make sure that we have results. Uploading content does not
        # seem to create a task so we cannot pool it for status. We
        # should then check that we have some results back before
        # proceeding.
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = entities.PuppetModule(
            id=puppet_modules[0]['id']
        )

        # Incrementally update the CVV with the puppet module.
        payload = {
            'content_view_version_environments': [{
                'content_view_version_id': content_view.version[0].id,
                'environment_ids': [
                    environment.id
                    for environment
                    in content_view.version[0].read().environment
                ],
            }],
            'add_content': {'puppet_module_ids': [puppet_module.id]},
        }
        content_view.version[0].incremental_update(data=payload)
        content_view = content_view.read()

        # The CV now has two versions. The first version has no puppet modules,
        # and the second version has one puppet module. Let's verify this.
        # NOTE: The `read_json` lines should be refactored after the 'minor'
        # attribute is added to the ContentViewVersion entity class.
        self.assertEqual(len(content_view.version), 2)
        for i in range(len(content_view.version)):
            content_view.version[i] = content_view.version[i].read()
        content_view.version.sort(key=lambda cvv: cvv.read_json()['minor'])
        self.assertEqual(len(content_view.version[0].puppet_module), 0)
        self.assertEqual(len(content_view.version[1].puppet_module), 1)
        self.assertEqual(
            content_view.version[1].puppet_module[0].id,
            puppet_module.id,
        )

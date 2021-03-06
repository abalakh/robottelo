"""Unit tests for the ``gpgkeys`` paths."""
from nailgun import entities
from robottelo.decorators import run_only_on
from robottelo.test import APITestCase


@run_only_on('sat')
class GPGKeyTestCase(APITestCase):
    """Tests for ``katello/api/v2/gpg_keys``."""

    def test_get_all(self):
        """@Test: Search for a GPG key and specify just ``organization_id``.

        @Feature: GPGKey

        @Steps:

        1. Create an organization.
        1. Create a GPG key belonging to the organization.
        2. Search for GPG keys in the organization.

        @Assert: Only one GPG key is in the search results: the created GPG
        key.

        """
        org = entities.Organization().create()
        gpg_key = entities.GPGKey(organization=org).create()
        gpg_keys = gpg_key.search({'organization'})
        self.assertEqual(len(gpg_keys), 1)
        self.assertEqual(gpg_key.id, gpg_keys[0].id)

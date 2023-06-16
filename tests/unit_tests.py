# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest

from unittest.mock import Mock
from ovos_bus_client.message import Message
from neon_phal_plugin_core_updater import CoreUpdater
from ovos_utils.messagebus import FakeBus


class PluginTests(unittest.TestCase):
    bus = FakeBus()
    plugin = CoreUpdater(bus)

    def test_get_installed_core_version(self):
        self.plugin.core_package = "non-existent-test-package"
        self.assertEqual(self.plugin._get_installed_core_version(), "0.0.0")

    def test_get_github_releases(self):
        self.assertEqual(self.plugin.github_ref, "NeonGeckoCom/NeonCore")
        releases = self.plugin._get_github_releases()

        def _parse_version(ver):
            year, month, day = ver.split('.')
            if 'a' in day:
                day, alpha = day.split('a')
            else:
                alpha = 0
            return int(year), int(month), int(day), int(alpha)

        self.assertIsInstance(releases, list)
        for i, r in enumerate(releases):
            if i == 0:
                continue
            old = _parse_version(r)
            new = _parse_version(releases[i - 1])
            self.assertGreaterEqual(new[0], old[0], f"new={new}|old={old}")
            if new[0] == old[0]:
                # Same year, month must be greater
                self.assertGreaterEqual(new[1], old[1], f"new={new}|old={old}")
                if new[1] == old[1]:
                    # Same month, day must be greater
                    self.assertGreaterEqual(new[2], old[2],
                                            f"new={new}|old={old}")
                    if new[2] == old[2]:
                        if new[3] == 0:
                            # Stable release, alpha versions will reset
                            continue
                        # Same day, alpha must be greater
                        self.assertGreaterEqual(new[3], old[3],
                                                f"new={new}|old={old}")

    def test_get_latest_github_release(self):
        release = self.plugin._get_latest_github_release()
        self.assertIsInstance(release, str, release)
        self.assertEqual(len(release.split('.')), 3, release)
        self.assertNotIn('a', release, release)

    def test_check_core_updates(self):
        self.assertIsNone(self.plugin.pypi_ref)
        real_get_releases = self.plugin._get_github_releases
        real_get_latest = self.plugin._get_latest_github_release
        # In this example, 22.10.3 is a pre-release
        gh_releases = ['22.10.3a1', '22.10.3', '22.10.1a1', '22.10.0',
                       '22.04.1a1', '22.04.0']
        self.plugin._get_github_releases = Mock(return_value=gh_releases)
        self.plugin._get_latest_github_release = Mock(return_value="22.10.0")

        # Check update already latest stable
        self.plugin._installed_version = "22.10.0"
        resp = self.bus.wait_for_response(Message(
            "neon.core_updater.check_update"))
        self.assertIsInstance(resp, Message)
        self.assertIsNone(resp.data['new_version'])
        self.assertEqual(resp.data['latest_version'], '22.10.0')

        # Update from stable to newer stable
        self.plugin._installed_version = "22.04.0"
        resp = self.bus.wait_for_response(Message(
            "neon.core_updater.check_update"))
        self.assertIsInstance(resp, Message)
        self.assertEqual(resp.data['new_version'], '22.10.0')
        self.assertEqual(resp.data['latest_version'], '22.10.0')

        # Update from stable to newer alpha
        resp = self.bus.wait_for_response(Message(
            "neon.core_updater.check_update",
            {"include_prerelease": True}))
        self.assertIsInstance(resp, Message)
        self.assertEqual(resp.data['new_version'], '22.10.3a1')
        self.assertEqual(resp.data['latest_version'], '22.10.3a1')

        # Update from alpha to newer stable
        self.plugin._installed_version = "22.04.1a1"
        resp = self.bus.wait_for_response(Message(
            "neon.core_updater.check_update"))
        self.assertIsInstance(resp, Message)
        self.assertEqual(resp.data['new_version'], '22.10.0')
        self.assertEqual(resp.data['latest_version'], '22.10.0')

        # Update from alpha to newer alpha
        resp = self.bus.wait_for_response(Message(
            "neon.core_updater.check_update",
            {"include_prerelease": True}))
        self.assertIsInstance(resp, Message)
        self.assertEqual(resp.data['new_version'], '22.10.3a1')
        self.assertEqual(resp.data['latest_version'], '22.10.3a1')

        # Update from alpha to older stable
        self.plugin._installed_version = '22.10.1a1'
        resp = self.bus.wait_for_response(Message(
            "neon.core_updater.check_update"))
        self.assertIsInstance(resp, Message)
        self.assertEqual(resp.data['new_version'], '22.10.0')
        self.assertEqual(resp.data['latest_version'], '22.10.0')

        self.plugin._get_github_releases = real_get_releases
        self.plugin._get_latest_github_release = real_get_latest


if __name__ == '__main__':
    unittest.main()

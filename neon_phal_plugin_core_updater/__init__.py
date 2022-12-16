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

import requests
import subprocess

from os.path import dirname
from subprocess import run
from mycroft_bus_client import Message
from ovos_utils.log import LOG
from ovos_plugin_manager.phal import PHALPlugin


class CoreUpdater(PHALPlugin):
    def __init__(self, bus=None, name="neon-phal-plugin-core-updater",
                 config=None):
        PHALPlugin.__init__(self, bus, name, config)
        self.update_command = self.config.get("update_command",
                                              f"{dirname(__file__)}/"
                                              f"update_scripts/"
                                              f"neon_os_2022_12.sh")
        self.core_package = self.config.get("core_module") or "neon_core"
        self.github_ref = self.config.get("github_ref", "NeonGeckoCom/NeonCore")
        self.pypi_ref = self.config.get("pypi_ref")
        self._installed_version = self._get_installed_core_version()
        self.bus.on("neon.core_updater.check_update", self.check_core_updates)
        self.bus.on("neon.core_updater.start_update", self.start_core_updates)

    def _get_installed_core_version(self):
        """
        Get the currently installed core version at init
        """
        from neon_utils.packaging_utils import get_package_version_spec
        return get_package_version_spec(self.core_package)

    def check_core_updates(self, message: Message):
        """
        Check for a new core version and reply
        """
        LOG.debug(f"Checking for update. current={self._installed_version}")
        update_alpha = 'a' in self._installed_version
        new_version = None
        if self.pypi_ref:
            # TODO: Implement PyPI version check
            pass
        elif self.github_ref:
            url = f'https://api.github.com/repos/{self.github_ref}/releases'
            releases = requests.get(url).json()
            for release in releases:
                if release.get("prerelease") and not update_alpha:
                    continue
                elif release.get("name") == self._installed_version:
                    break
                else:
                    new_version = release.get("name")

        if new_version:
            LOG.info(f"Found newer release: {new_version}")
        if message:
            self.bus.emit(message.response({"new_version": new_version,
                                            "installed_version": self._installed_version,
                                            "github_ref": self.github_ref,
                                            "pypi_ref": self.pypi_ref}))
        else:
            LOG.error("No remote reference to check for updates")

    def start_core_updates(self, message):
        """
        Start a core update. Note that the update process may kill this thread.
        """
        version = message.data.get("version")
        LOG.info(f"Starting Core Update to version: {version}")
        command = f"bash {self.update_command} {version}" if version else \
            self.update_command
        LOG.debug(command)
        run(command, shell=True, start_new_session=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE)
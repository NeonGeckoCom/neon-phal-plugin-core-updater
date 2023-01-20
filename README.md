# Core Updater Plugin
Exposes a messagebus API to check for and initiate core module updates. Update
checks use GitHub releases or PyPI indices, depending on plugin configuration.
The update command is configurable and is started in a new session. Note that
the calling module might be killed during updates and in many cases, systemD 
will kill the update process if the parent service stops.

## Configuration
The update command, core package, and update references are all configurable.
For version checks, a valid Python Package must be installed and versions must
either be published to PyPI or tagged as GitHub releases.

```yaml
PHAL:
  admin:
    neon-phal-plugin-core-updater:
      enabled: True
      core_module: neon_core
      github_ref: NeonGeckoCom/NeonCore
      update_command: systemctl start update_service
```

## Messagebus API
Messagebus events are handled to check for updates and to update to a newer version.

### Check for updates
emitting:
```yaml
msg_type: neon.core_updater.check_update
data: 
  include_prerelease: True
```
will generate the response:
```yaml
msg_type: neon.core_updater.check_update.response
data:
  new_version: <latest version including pre-releases/alphas>
  installed_version: <current installed version>
  github_ref: <plugin configured GH ref>
  pypi_ref: <plugin configured PyPI ref>
```

If `include_prereleases` is not present in the request, the installed version is
used to determine if pre-releases should be included.

Note that only one of `github_ref` or `pypi_ref` should be configured. If both
are configured, PyPI checks take priority.

### Start Updates
emitting:
```yaml
msg_type: neon.core_updater.start_update
data:
  version: <new_version>
```
will start the configured update command in a shell with `version` passed as the
first and only argument. If `version` is omitted, the configured update command
will be called with no commands.
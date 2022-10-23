# Distro Dumper

Simple Python script and Docker container to automatically dump Linux/BSD torrents from
various sources.


## Usage

See the example `docker-compose.yaml` for example usage. The following environment variables are
used to control the image and script. Defaults are for the Docker image only.

- `DUMPER_INTERVAL` - Default: `3600` - Number of seconds between each check.
- `DUMPER_DIRECTORY` - Default: `/dump` - Directory to put downloaded torrent files in. Could be a
  directory your Torrent client monitors for new files to auto-add.
- `DUMPER_CACHE` - Default: `/cache` - Directory to stash cache data in, usually just the torrent
  files before they're copied to the dump directory.
- `DUMPER_DEBUG` - If set to `"true"`, will enable additional output.
- `DUMPER_MODULES` - Comma-separated list of dumper modules to load. 
- `<MODULE>_<SETTING>` - Proposed settings format for specific dumper modules.


## Modules

Module specific settings and considerations.
Modules are mapped from name to code in the `__AVAILABLE_MODULES` dictionary in
`distrodumper/config_helper.py`, so any new module should be added there.


### Arch

The default behavior is to only dump the latest release. This can be changed with the following
variables.

- `ARCH_GET_ALL` - If set to `"true"`, will dump all the available Arch releases on the
  [release page](https://archlinux.org/releng/releases/).
- `ARCH_GET_AVAILABLE` - If set to `"true"`, will dump all the available Arch releases on the
  [release page](https://archlinux.org/releng/releases/) that has the available (webseed) flag set.
  This option is not implemented yet.


### Debian

TODO


### Manjaro

TODO


### Raspberry Pi OS

TODO


## Development

I've only tested with Python 3.9, but some earlier and all later versions should work as well.

- Create a virtual environment: `$ python3 -m virtualenv venv`.
- Activate the environment: `$ source venv/bin/activate`.
- Install dependencies: `$ pip install -r requirements-dev.txt`.
- Go ham. :)

### Dependency pinning

Dependencies are pinned with `pip-tools`. So any changes should be done via the `.in` files, and
calling `pip-compile`.

# Distrowatch Dumper

Simple Python script and Docker container to automatically dump Linux/BSD torrents from
distrowatch.com's RSS feed.

## Usage

See the example `docker-compose.yaml` for example usage. The following environment variables are
used to control the image and script. Defaults are for the Docker image only.

- `CACHE_DIRECTORY` - Default: `/cache` - Directory to download torrent files to, this is also used
  to keep a "state".
- `DISTRO_PREFIXES` - Comma separated list of what distributions to actually download. Example:
  `raspios,debian`
- `DUMP_INTERVAL` - Default: `3600` - Number of seconds between each check.
- `DUMP_DIRECTORY` - Default: `/dump` - Directory to put downloaded torrent files in. Could be a
  directory your Torrent client monitors for new files to auto-add.
- `FEED_URL` - URL of the feed. Should most likely be `https://distrowatch.com/news/torrents.xml`.


## Development

I've only tested with Python 3.9, but some earlier and all later should work as well.

- Create a virtual environment: `$ python3 -m virtualenv venv`.
- Activate the environment: `$ source venv/bin/activate`.
- Install dependencies: `$ pip install -r requirements-dev.txt`.
- Go ham. :)

### Dependency pinning

Dependencies are pinned with `pip-tools`. So any changes should be done via the `.in` files, and
calling `pip-compile`.


## Future Work

- Support regex instead of prefix, this would allow to filter for arch or desktop environments.
- Add support for custom UID/GUID in Docker image. Overlay?

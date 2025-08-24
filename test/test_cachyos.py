""" Tests for CachyOS module. """

# System imports.
from typing import Any

# 3rd-party imports.
import pytest

# App imports.
from distrodumper.modules.cachyos import CachyOsConfiguration, CachyOsWorker


class _Resp:
    """Simple response stub for requests.get"""

    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def _mock_get_factory(payload: str, status_code: int = 200):
    """Return a requests.get stub that yields the given payload regardless of URL."""

    def _mock_get(url: str, *args: Any, **kwargs: Any) -> _Resp:  # noqa: ARG001
        return _Resp(payload, status_code)

    return _mock_get


def test_cachyos_parses_anchor_torrents_and_filters_editions(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <body>
        <a href="/">Home</a>
        <a href="https://torrents.example/cachyos-desktop-linux-250713.torrent">Desktop</a>
        <a href="https://torrents.example/cachyos-handheld-linux-250713.torrent">Handheld</a>
        <a href="https://example.com/not-a-torrent.iso">ISO</a>
      </body>
    </html>
    """

    monkeypatch.setattr("requests.get", _mock_get_factory(html))

    conf = CachyOsConfiguration(requested_editions=["desktop"])
    worker = CachyOsWorker(conf)

    result = worker.dump()

    assert "cachyos-desktop-linux-250713.torrent" in result
    assert result["cachyos-desktop-linux-250713.torrent"].startswith("https://torrents.example/")
    assert "cachyos-handheld-linux-250713.torrent" not in result


def test_cachyos_parses_inline_json_and_ignores_magnets(monkeypatch: pytest.MonkeyPatch) -> None:
    # Inline JSON-like payload mimicking the live page structure.
    html = """
    <html>
      <body>
        <script type="application/ld+json">
          {
            "name":"CachyOS",
            "torrent_url":[0,"https://torrents.example/cachyos-desktop-linux-250713.torrent"],
            "magnet_url":[0,"magnet:?xt=urn:btih:ABCDEF123456"],
            "mirrors":["https://cdn.example/desktop/250713/cachyos-desktop-linux-250713.iso"]
          }
        </script>
        <script type="application/ld+json">
          {
            "torrent_url":[0,"https://torrents.example/cachyos-handheld-linux-250713.torrent"]
          }
        </script>
      </body>
    </html>
    """

    monkeypatch.setattr("requests.get", _mock_get_factory(html))

    conf = CachyOsConfiguration(requested_editions=["desktop", "handheld"])
    worker = CachyOsWorker(conf)

    result = worker.dump()

    # Only .torrent links should be returned; magnets and ISO mirrors are ignored
    assert set(result.keys()) == {
        "cachyos-desktop-linux-250713.torrent",
        "cachyos-handheld-linux-250713.torrent",
    }
    assert all(v.startswith("https://torrents.example/") for v in result.values())


def test_cachyos_builds_absolute_from_relative(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <body>
        <a href="/files/cachyos-desktop-linux-250713.torrent">DL</a>
      </body>
    </html>
    """

    monkeypatch.setattr("requests.get", _mock_get_factory(html))

    conf = CachyOsConfiguration(requested_editions=["desktop"])
    worker = CachyOsWorker(conf)

    result = worker.dump()

    assert set(result.keys()) == {"cachyos-desktop-linux-250713.torrent"}
    # Assembled against base downloads page
    assert result["cachyos-desktop-linux-250713.torrent"].startswith("https://cachyos.org/")



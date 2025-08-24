from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from distrodumper.modules.arch import (
    ArchConfiguration,
    ArchWorker,
    ArchHelper,
    ModuleExternalError,
)


def make_response(status_code: int, text: str):
    return SimpleNamespace(status_code=status_code, text=text)


def test_arch_returns_only_latest_when_get_all_false(monkeypatch: pytest.MonkeyPatch) -> None:
    html = (
        '<html><body>'
        '<a href="magnet:?xt=urn:btih:AAA&dn=archlinux-2025.07.01-x86_64.iso">old</a>'
        '<a href="magnet:?xt=urn:btih:BBB&dn=archlinux-2025.08.01-x86_64.iso">new</a>'
        '</body></html>'
    )

    mock_resp = make_response(200, html)
    mock_get = Mock(return_value=mock_resp)
    monkeypatch.setattr("distrodumper.modules.arch.requests.get", mock_get)

    worker = ArchWorker(ArchConfiguration(get_all=False))
    result = worker.dump()

    assert list(result.keys()) == ["archlinux-2025-08-01-x86_64.torrent"]
    assert result["archlinux-2025-08-01-x86_64.torrent"] == (
        "https://archlinux.org/releng/releases/2025.08.01/torrent/"
    )

    # Ensure we pass a User-Agent header
    assert mock_get.called
    _, kwargs = mock_get.call_args
    assert "headers" in kwargs and "User-Agent" in kwargs["headers"]


def test_arch_returns_all_when_get_all_true(monkeypatch: pytest.MonkeyPatch) -> None:
    html = (
        '<html><body>'
        '<a href="magnet:?xt=urn:btih:AAA&dn=archlinux-2025.07.01-x86_64.iso">old</a>'
        '<a href="magnet:?xt=urn:btih:BBB&dn=archlinux-2025.08.01-x86_64.iso">new</a>'
        '</body></html>'
    )

    mock_resp = make_response(200, html)
    monkeypatch.setattr(
        "distrodumper.modules.arch.requests.get", Mock(return_value=mock_resp)
    )

    worker = ArchWorker(ArchConfiguration(get_all=True))
    result = worker.dump()

    assert result == {
        "archlinux-2025-07-01-x86_64.torrent": (
            "https://archlinux.org/releng/releases/2025.07.01/torrent/"
        ),
        "archlinux-2025-08-01-x86_64.torrent": (
            "https://archlinux.org/releng/releases/2025.08.01/torrent/"
        ),
    }


def test_arch_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resp = make_response(500, "Server error")
    monkeypatch.setattr(
        "distrodumper.modules.arch.requests.get", Mock(return_value=mock_resp)
    )

    worker = ArchWorker(ArchConfiguration(get_all=False))
    with pytest.raises(ModuleExternalError):
        _ = worker.dump()


def test_arch_handles_no_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    html = '<html><body><a href="/some/other/link">nope</a></body></html>'
    mock_resp = make_response(200, html)
    monkeypatch.setattr(
        "distrodumper.modules.arch.requests.get", Mock(return_value=mock_resp)
    )

    worker = ArchWorker(ArchConfiguration(get_all=True))
    result = worker.dump()
    assert result == {}


def test_arch_generate_from_environment_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARCH_GET_ALL", "true")
    monkeypatch.setenv("ARCH_GET_AVAILABLE", "true")
    config = ArchHelper.generate_from_environment()
    assert config.get_all is True
    assert config.get_available is True



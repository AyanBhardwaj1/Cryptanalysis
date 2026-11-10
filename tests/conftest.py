"""Shared fixtures: a sqlite Store in tmp_path and a fake Anthropic client (no network)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fakes import FakeClient

from lplab.llm import LLM
from lplab.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    s = Store(tmp_path / "lab.sqlite")
    yield s
    s.close()


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()


@pytest.fixture
def llm(store: Store, fake_client: FakeClient) -> LLM:
    return LLM(store, client=fake_client)

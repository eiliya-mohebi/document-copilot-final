"""Embedding of chunk texts through the OpenAI-compatible (AvalAI) API."""

from __future__ import annotations

from types import SimpleNamespace

from ingest.embeddings import build_openai_client, embed_texts


class FakeOpenAI:
    def __init__(self, dimensions: int = 4):
        self.calls: list[dict] = []
        self._dimensions = dimensions
        self.embeddings = SimpleNamespace(create=self._create)

    def _create(self, *, model: str, input: list[str], dimensions: int):
        self.calls.append({"model": model, "input": input, "dimensions": dimensions})
        data = [
            SimpleNamespace(embedding=[float(len(text))] * self._dimensions)
            for text in input
        ]
        return SimpleNamespace(data=data)


def test_embeds_all_texts_in_order():
    client = FakeOpenAI()

    vectors = embed_texts(client, ["a", "bb", "ccc"])

    assert vectors == [[1.0] * 4, [2.0] * 4, [3.0] * 4]


def test_batches_requests_and_passes_model_settings():
    client = FakeOpenAI()
    texts = [f"text-{i}" for i in range(150)]

    embed_texts(client, texts, batch_size=64)

    assert [len(call["input"]) for call in client.calls] == [64, 64, 22]
    assert client.calls[0]["model"] == "text-embedding-3-small"
    assert client.calls[0]["dimensions"] == 1536


def test_client_points_at_avalai_base_url(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    client = build_openai_client()

    assert str(client.base_url).startswith("https://api.avalai.ir/v1")


def test_client_requires_api_key(monkeypatch):
    import pytest

    from app.config import settings

    monkeypatch.setattr(settings, "openai_api_key", "")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        build_openai_client()

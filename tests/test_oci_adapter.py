from __future__ import annotations

import sys
from types import SimpleNamespace

from vanguard_primekg.agent.oci_llm import OCIPlannerConfig, OCIPlannerModel


class TextContent:
    def __init__(self, text):
        self.text = text


class Message:
    def __init__(self, content):
        self.content = content


class GenericChatRequest:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class ChatDetails:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class ServingMode:
    def __init__(self, model_id):
        self.model_id = model_id


class Client:
    instances = []

    def __init__(self, config, timeout):
        self.config = config
        self.timeout = timeout
        self.details = None
        Client.instances.append(self)

    def chat(self, details):
        self.details = details
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=[TextContent('{"ok":true}')]))]
        )
        return SimpleNamespace(data=SimpleNamespace(chat_response=response))


def _fake_oci():
    models = SimpleNamespace(
        SystemMessage=Message,
        UserMessage=Message,
        TextContent=TextContent,
        ChatDetails=ChatDetails,
        OnDemandServingMode=ServingMode,
        GenericChatRequest=GenericChatRequest,
    )
    return SimpleNamespace(
        config=SimpleNamespace(from_file=lambda path, profile: {"tenancy": "ocid1.tenancy", "region": "r1"}),
        generative_ai_inference=SimpleNamespace(
            GenerativeAiInferenceClient=Client,
            models=models,
        ),
    )


def test_oci_adapter_omits_temperature_unless_explicit(monkeypatch) -> None:
    Client.instances.clear()
    monkeypatch.setitem(sys.modules, "oci", _fake_oci())
    model = OCIPlannerModel(OCIPlannerConfig(model_id="model", temperature=None))
    assert model.complete(system="s", user="u", max_tokens=100, timeout=1) == '{"ok":true}'
    request = Client.instances[-1].details.kwargs["chat_request"]
    assert "temperature" not in request.kwargs


def test_oci_adapter_sends_explicit_temperature_and_bounds_tokens(monkeypatch) -> None:
    Client.instances.clear()
    monkeypatch.setitem(sys.modules, "oci", _fake_oci())
    model = OCIPlannerModel(OCIPlannerConfig(model_id="model", temperature=0.0, max_tokens=64))
    model.complete(system="s", user="u", max_tokens=100, timeout=1)
    details = Client.instances[-1].details
    request = details.kwargs["chat_request"]
    assert request.kwargs["temperature"] == 0.0
    assert request.kwargs["max_tokens"] == 64
    assert details.kwargs["serving_mode"].model_id == "model"


def test_oci_adapter_rejects_invalid_bounds_before_sdk_use() -> None:
    import pytest

    with pytest.raises(ValueError, match="model_id"):
        OCIPlannerModel(OCIPlannerConfig(model_id=""))
    with pytest.raises(ValueError, match="temperature"):
        OCIPlannerModel(OCIPlannerConfig(model_id="model", temperature=1.5))
    with pytest.raises(ValueError, match="max_tokens"):
        OCIPlannerModel(OCIPlannerConfig(model_id="model", max_tokens=5000))

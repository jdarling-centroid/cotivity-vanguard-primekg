"""Chat-model abstraction driving the agentic loop.

The runner owns the conversation (the ``messages`` list) and asks a
:class:`ChatModel` for the next :class:`ModelTurn` — either a batch of tool
calls or a final answer. This mirrors the OpenAI tool-calling protocol, so the
real client is a thin adapter while the stub is a deterministic driver used for
offline dry-runs and tests.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import httpx

from ..config import load_config
from ..errors import ValidationError


def get_system_prompt() -> str:
    """Return the orchestrator system prompt from ``models.orchestrator.prompt``."""
    orchestrator = load_config().models.orchestrator
    if orchestrator is None or not orchestrator.prompt:
        raise ValidationError("config is missing models.orchestrator.prompt")
    return orchestrator.prompt


def get_security_prescan_prompt() -> str:
    """Return the firewall prescan prompt from ``security.firewall_prompt``."""
    firewall_prompt = load_config().security.firewall_prompt
    if not firewall_prompt:
        raise ValidationError("config is missing security.firewall_prompt")
    return firewall_prompt


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    id: str = field(default_factory=lambda: "call_" + uuid.uuid4().hex[:8])


@dataclass
class ModelTurn:
    """One model response: tool calls to execute, or a final ``content`` string."""

    tool_calls: list[ToolCall] = field(default_factory=list)
    content: str | None = None


@runtime_checkable
class ChatModel(Protocol):
    def respond(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelTurn: ...


def _tool_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [m for m in messages if m.get("role") == "tool"]


def _last_result(messages: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for message in reversed(messages):
        if message.get("role") == "tool" and message.get("name") == name:
            try:
                return json.loads(message.get("content", "{}"))
            except json.JSONDecodeError:
                return None
    return None


def _security_text(value: str) -> tuple[str, str, list[str]]:
    canonical = unicodedata.normalize("NFKC", value or "").casefold()
    canonical = "".join(
        character
        for character in canonical
        if unicodedata.category(character) != "Cf"
    )
    canonical = canonical.translate(
        str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
    )
    words = re.findall(r"[a-z0-9]+", canonical)
    return canonical, " ".join(words), words


def _within_one_edit(value: str, target: str) -> bool:
    """Match a high-risk keyword with one insertion/deletion/change/transposition."""
    if value == target:
        return True
    if abs(len(value) - len(target)) > 1 or min(len(value), len(target)) < 4:
        return False
    if len(value) == len(target):
        differences = [
            index
            for index, pair in enumerate(zip(value, target, strict=False))
            if pair[0] != pair[1]
        ]
        if len(differences) == 1:
            return True
        return (
            len(differences) == 2
            and differences[1] == differences[0] + 1
            and value[differences[0]] == target[differences[1]]
            and value[differences[1]] == target[differences[0]]
        )
    shorter, longer = (value, target) if len(value) < len(target) else (target, value)
    short_index = long_index = differences = 0
    while short_index < len(shorter) and long_index < len(longer):
        if shorter[short_index] == longer[long_index]:
            short_index += 1
            long_index += 1
        else:
            differences += 1
            long_index += 1
            if differences > 1:
                return False
    return True


def deterministic_security_verdict(question: str) -> dict[str, Any]:
    """Apply fast intent-based controls before any firewall-model verdict."""
    canonical, normalized, words = _security_text(question)
    configured_hits = []
    for marker in load_config().security.malicious_markers:
        marker_canonical, marker_normalized, _ = _security_text(marker)
        if (marker_canonical and marker_canonical in canonical) or (
            marker_normalized and marker_normalized in normalized
        ):
            configured_hits.append(marker)
    if configured_hits:
        return {
            "malicious": True,
            "reason": "matched security policy: " + ", ".join(configured_hits),
        }

    compact = "".join(words)

    def has_fuzzy(*targets: str) -> bool:
        return any(target in compact for target in targets if len(target) >= 6) or any(
            _within_one_edit(word, target)
            for word in words
            for target in targets
        )

    protected_targets = (
        "previous",
        "prior",
        "above",
        "instruction",
        "instructions",
        "prompt",
        "system",
        "developer",
        "knowledge graph",
        "primekg",
        "graph",
        "tool",
        "tools",
        "result",
        "results",
        "source",
        "sources",
        "evidence",
        "retrieval",
        "context",
        "document",
        "documents",
        "reference data",
        "safety",
        "firewall",
        "policy",
    )
    attempts_override = has_fuzzy(
        "ignore", "disregard", "bypass", "override", "forget", "skip"
    )
    targets_control = any(target in normalized for target in protected_targets)
    if attempts_override and targets_control:
        return {
            "malicious": True,
            "reason": "attempt to override governed instructions or evidence sources",
        }

    source_bypass = bool(
        re.search(
            r"\b(?:do not|don t|never|avoid|without)\b.{0,45}"
            r"\b(?:query|search|use|consult|retrieve|primekg|graph|documents?)\b",
            normalized,
        )
    ) or any(
        phrase in normalized
        for phrase in (
            "hidden model knowledge",
            "model knowledge instead",
            "invent the most likely",
            "without retrieved evidence",
        )
    )
    if source_bypass:
        return {
            "malicious": True,
            "reason": "attempt to bypass governed retrieval or invent unsupported results",
        }

    mutation_action = has_fuzzy(
        "insert", "create", "append", "update", "modify", "delete", "remove", "write"
    )
    governed_data_target = any(
        target in normalized
        for target in (
            "edge",
            "node",
            "graph",
            "database",
            "table",
            "record",
            "primekg",
        )
    )
    mutation_directive = mutation_action and governed_data_target and (
        "before answering" in normalized
        or "before responding" in normalized
        or "first " in normalized
        or "then return" in normalized
        or "then answer" in normalized
    )
    if mutation_directive:
        return {
            "malicious": True,
            "reason": "attempt to modify governed graph or database state",
        }

    hidden_targets = (
        "system prompt",
        "hidden prompt",
        "developer message",
        "internal instruction",
        "secret instruction",
        "chain of thought",
        "environment variable",
        "api key",
        "access token",
        "credential",
        "database dump",
        "all patient data",
        "patient record",
        "patient records",
        "retrieved context",
        "retrieved data",
        "document metadata",
        "hidden context",
        "all records",
    )
    disclosure_action = has_fuzzy(
        "reveal", "expose", "print", "dump", "extract", "exfiltrate"
    ) or any(action in normalized for action in ("show me", "tell me", "return the"))
    if disclosure_action and any(target in normalized for target in hidden_targets):
        return {
            "malicious": True,
            "reason": "attempt to disclose protected instructions, credentials, or data",
        }

    external_destination = any(
        marker in canonical
        for marker in (
            "http://",
            "https://",
            "webhook",
            "email it",
            "external server",
            "outside the platform",
            "base64",
            "encoded blob",
        )
    )
    transfer_action = has_fuzzy(
        "send",
        "upload",
        "transmit",
        "post",
        "exfiltrate",
        "forward",
        "copy",
        "encode",
        "export",
    )
    if external_destination and transfer_action:
        return {
            "malicious": True,
            "reason": "attempt to transfer data to an external destination",
        }

    forced_control_output = bool(
        re.search(
            r"\b(?:respond|reply|return|output|answer)\b.{0,40}"
            r"\b(?:only|exactly|single word|verbatim)\b",
            normalized,
        )
    ) and any(token in words for token in ("none", "hacked", "pwned"))
    forced_control_output = forced_control_output or (
        any(
            phrase in normalized
            for phrase in (
                "no matter what the tools return",
                "no matter what tools return",
                "regardless of the evidence",
                "regardless of tool results",
            )
        )
        and any(token in words for token in ("none", "hacked", "pwned"))
    )
    asserts_answer_state = any(
        phrase in normalized
        for phrase in (
            "question is unanswerable",
            "answer is unanswerable",
            "correct answer is",
            "the answer is",
            "must reply only",
            "must respond only",
            "must answer only",
        )
    )
    forces_literal_response = bool(
        re.search(
            r"\b(?:must|should|shall)\b.{0,25}"
            r"\b(?:reply|respond|return|output|answer)\b.{0,20}\b(?:only|exactly)\b",
            normalized,
        )
    )
    forced_control_output = forced_control_output or (
        asserts_answer_state and forces_literal_response
    )
    if forced_control_output:
        return {
            "malicious": True,
            "reason": "attempt to force a control response instead of grounded results",
        }

    return {"malicious": False, "reason": None}


def _stub_security_verdict(messages: list[dict[str, Any]]) -> ModelTurn:
    """Deterministic offline firewall verdict for the stub model."""
    question = next(
        (m["content"] for m in messages if m.get("role") == "user"), ""
    )
    payload = deterministic_security_verdict(question)
    return ModelTurn(content=json.dumps(payload))


class StubChatModel:
    """Deterministic driver that performs a fixed three-hop retrieval.

    It inspects the conversation to decide the next move, so it works with any
    toolbox that returns the standard shapes (real or stub fixtures).
    """

    def respond(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelTurn:
        # The firewall service drives the stub with an empty toolbox to obtain a
        # security verdict; the orchestrator loop always supplies tools.
        if not tools:
            return _stub_security_verdict(messages)
        done = {m.get("name") for m in _tool_messages(messages)}
        question = next(
            (m["content"] for m in messages if m.get("role") == "user"), ""
        )

        if "hybrid_search" not in done:
            return ModelTurn(
                tool_calls=[ToolCall("hybrid_search", {"query": question, "limit": 5})]
            )

        search = _last_result(messages, "hybrid_search") or {}
        hits = search.get("results", [])
        start_node = hits[0]["node"]["node_id"] if hits else "n_unknown"
        if "traverse_graph" not in done:
            return ModelTurn(
                tool_calls=[
                    ToolCall(
                        "traverse_graph",
                        {"start_node_ids": [start_node], "maximum_depth": 2},
                    )
                ]
            )

        traverse = _last_result(messages, "traverse_graph") or {}
        nodes = traverse.get("nodes", [])
        target = nodes[-1]["node_id"] if nodes else start_node
        if "get_fragment" not in done:
            return ModelTurn(
                tool_calls=[ToolCall("get_fragment", {"fragment_id": f"frag_{target}"})]
            )

        fragment = _last_result(messages, "get_fragment") or {}
        prov = fragment.get("provenance", {})
        answer = {
            "answer": f"Yes — evidence found for: {question}",
            "confidence": 0.9,
            "citations": [
                {
                    "doc_id": prov.get("doc_id", target),
                    "page": prov.get("page"),
                    "span": prov.get("span"),
                }
            ],
        }
        return ModelTurn(content=json.dumps(answer))


class OpenAIChatModel:
    """Adapter over the OpenAI Chat Completions tool-calling API.

    The ``openai`` package is imported lazily so the package (and the offline
    dry-run) does not require it to be installed.
    """

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised only with SDK absent
            raise RuntimeError(
                "the 'openai' package is required for non-stub models; "
                "install it or run with --dry-run"
            ) from exc
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
        )
        self._model = model
        self._temperature = temperature

    def respond(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelTurn:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            tools=tools,  # type: ignore[arg-type]
            temperature=self._temperature,
        )
        choice = completion.choices[0].message
        if choice.tool_calls:
            calls = [
                ToolCall(
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments or "{}"),
                    id=tc.id,
                )
                for tc in choice.tool_calls
            ]
            return ModelTurn(tool_calls=calls)
        return ModelTurn(content=choice.content or "")


def _parse_arguments(raw: Any) -> dict[str, Any]:
    """Normalise a tool-call ``arguments`` field (str or dict) to a dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {}
    return {}


class OllamaChatModel:
    """Adapter over a local Ollama server's OpenAI-compatible chat endpoint.

    Talks to ``{base_url}/v1/chat/completions`` via ``httpx`` (no SDK required),
    passing the same ``tools`` schema so tool-calling models (e.g. ``llama3``,
    ``mistral``) can invoke the MCP tools. Connection and read timeouts are
    surfaced as ``RuntimeError`` rather than hanging.
    """

    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        temperature: float = 0.0,
        timeout: float | None = None,
        reasoning_effort: str | None = None,
        max_tokens: int | None = None,
    ) -> None:
        models = load_config().models
        resolved = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or models.default_ollama_endpoint
        )
        self._url = f"{resolved.rstrip('/')}/v1/chat/completions"
        self._model = model
        self._temperature = temperature
        self._reasoning_effort = reasoning_effort
        self._max_tokens = max_tokens
        read_timeout = float(timeout if timeout is not None else models.chat_timeout_seconds)
        self._timeout = httpx.Timeout(
            read_timeout, connect=float(models.connect_timeout_seconds)
        )

    def respond(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelTurn:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "stream": False,
        }
        if self._reasoning_effort is not None:
            payload["reasoning_effort"] = self._reasoning_effort
        if self._max_tokens is not None:
            payload["max_tokens"] = self._max_tokens
        if tools:
            payload["tools"] = tools
        try:
            response = httpx.post(self._url, json=payload, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama chat timed out after {self._timeout} calling {self._url}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama chat request failed for {self._url}: {exc}") from exc

        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            calls = [
                ToolCall(
                    name=tc["function"]["name"],
                    arguments=_parse_arguments(tc["function"].get("arguments")),
                    id=tc.get("id") or ("call_" + uuid.uuid4().hex[:8]),
                )
                for tc in tool_calls
                if tc.get("function")
            ]
            return ModelTurn(tool_calls=calls)
        return ModelTurn(content=message.get("content") or "")


class OCIChatModel:
    """OCI Generative AI adapter preserving the agent's OpenAI-style contract."""

    def __init__(
        self,
        model: str,
        *,
        config_file: str | None = None,
        timeout: float | None = None,
        reasoning_effort: str | None = None,
        max_tokens: int | None = None,
    ) -> None:
        import oci

        path = config_file or os.environ.get("OCI_CONFIG_FILE", "/root/.oci/config")
        config = oci.config.from_file(path)
        self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config,
            timeout=(10, float(timeout or 300)),
        )
        self._compartment_id = os.environ.get("OCI_COMPARTMENT_ID", config["tenancy"])
        self._model = model.removeprefix("oci:")
        self._reasoning_effort = reasoning_effort
        self._max_tokens = max_tokens

    @staticmethod
    def _content(value: Any) -> list[Any]:
        from oci.generative_ai_inference.models import TextContent

        if value is None:
            return []
        if not isinstance(value, str):
            value = json.dumps(value)
        return [TextContent(text=value)]

    def _messages(self, messages: list[dict[str, Any]]) -> list[Any]:
        from oci.generative_ai_inference.models import (
            AssistantMessage,
            FunctionCall,
            SystemMessage,
            ToolMessage,
            UserMessage,
        )

        converted = []
        for message in messages:
            role = message.get("role")
            content = self._content(message.get("content"))
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "user":
                converted.append(UserMessage(content=content))
            elif role == "assistant":
                calls = [
                    FunctionCall(
                        id=call.get("id"),
                        name=call.get("function", {}).get("name"),
                        arguments=call.get("function", {}).get("arguments", "{}"),
                    )
                    for call in message.get("tool_calls", [])
                ]
                converted.append(AssistantMessage(content=content, tool_calls=calls or None))
            elif role == "tool":
                converted.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=message.get("tool_call_id"),
                    )
                )
        return converted

    @staticmethod
    def _tools(tools: list[dict[str, Any]]) -> list[Any]:
        from oci.generative_ai_inference.models import FunctionDefinition

        return [
            FunctionDefinition(
                name=tool["function"]["name"],
                description=tool["function"].get("description"),
                parameters=tool["function"].get("parameters", {}),
            )
            for tool in tools
            if tool.get("type") == "function" and tool.get("function")
        ]

    def respond(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ModelTurn:
        from oci.generative_ai_inference.models import (
            ChatDetails,
            GenericChatRequest,
            OnDemandServingMode,
        )

        kwargs: dict[str, Any] = {
            "messages": self._messages(messages),
            "tools": self._tools(tools) or None,
        }
        if self._reasoning_effort is not None:
            kwargs["reasoning_effort"] = self._reasoning_effort.upper()
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens
        response = self._client.chat(
            ChatDetails(
                compartment_id=self._compartment_id,
                serving_mode=OnDemandServingMode(model_id=self._model),
                chat_request=GenericChatRequest(**kwargs),
            )
        ).data.chat_response
        message = response.choices[0].message
        if message.tool_calls:
            return ModelTurn(
                tool_calls=[
                    ToolCall(
                        name=call.name,
                        arguments=_parse_arguments(call.arguments),
                        id=call.id,
                    )
                    for call in message.tool_calls
                ]
            )
        content = "".join(
            item.text for item in (message.content or []) if getattr(item, "text", None)
        )
        return ModelTurn(content=content)


def make_chat_model(
    model: str,
    *,
    provider: str | None = None,
    dry_run: bool = False,
    base_url: str | None = None,
    config_file: str | None = None,
    timeout: float | None = None,
    reasoning_effort: str | None = None,
    max_tokens: int | None = None,
) -> ChatModel:
    """Build a chat model. Non-stub models default to the local Ollama server.

    Routing:

    * ``dry_run`` or ``"stub"`` -> offline :class:`StubChatModel`.
    * ``"openai:<name>"`` -> hosted :class:`OpenAIChatModel`.
    * ``"oci:<name>"`` -> OCI Generative AI :class:`OCIChatModel`.
    * anything else (optionally ``"ollama:<name>"``) -> :class:`OllamaChatModel`.
    """
    if dry_run or model == "stub" or provider == "stub":
        return StubChatModel()
    if provider == "oci_generative_ai":
        return OCIChatModel(
            model,
            config_file=config_file,
            timeout=timeout,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
    if model.startswith("openai:"):
        return OpenAIChatModel(model.split(":", 1)[1])
    if model.startswith("oci:"):
        return OCIChatModel(
            model,
            config_file=config_file or base_url,
            timeout=timeout,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
    if model.startswith("ollama:"):
        model = model.split(":", 1)[1]
    return OllamaChatModel(
        model,
        base_url=base_url,
        timeout=timeout,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens,
    )

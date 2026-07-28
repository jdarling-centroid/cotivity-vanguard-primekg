"""OCI Generative AI adapter for the closed planner only.

This deliberately exposes a single text-completion method.  It does not expose
SQL, graph tools, or the legacy reference agent runner.
"""

from __future__ import annotations

import os
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OCIPlannerConfig:
    model_id: str
    region: str | None = None
    config_file: str | None = None
    profile: str = "DEFAULT"
    compartment_id: str | None = None
    timeout: float = 60.0
    max_tokens: int = 1800
    temperature: float | None = None


class OCIPlannerModel:
    def __init__(self, config: OCIPlannerConfig) -> None:
        if not config.model_id.strip():
            raise ValueError("OCI planner model_id is required")
        if not 1.0 <= config.timeout <= 300.0:
            raise ValueError("OCI planner timeout must be between 1 and 300 seconds")
        if not 64 <= config.max_tokens <= 4096:
            raise ValueError("OCI planner max_tokens must be between 64 and 4096")
        if config.temperature is not None and not 0.0 <= config.temperature <= 1.0:
            raise ValueError("OCI planner temperature must be between 0 and 1")
        try:
            import oci
        except ModuleNotFoundError as exc:  # pragma: no cover - optional live path
            raise RuntimeError("OCI SDK is not installed") from exc

        path = os.path.expanduser(
            config.config_file or os.environ.get("OCI_CONFIG_FILE", "~/.oci/config")
        )
        key_file = os.environ.get("OCI_KEY_FILE")
        if key_file:
            # OCI config files mounted into containers commonly name a
            # container-only key path.  Permit a host path override without
            # copying or rewriting credential files.
            parser = ConfigParser()
            if not parser.read(path):
                raise RuntimeError("OCI config file could not be read")
            if config.profile not in parser:
                raise RuntimeError(f"OCI config profile {config.profile!r} was not found")
            sdk_config = dict(parser[config.profile])
            sdk_config["key_file"] = os.path.expanduser(key_file)
            oci.config.validate_config(sdk_config)
        else:
            sdk_config = oci.config.from_file(path, config.profile)
        if config.region:
            sdk_config["region"] = config.region
        self._oci = oci
        self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            sdk_config,
            timeout=(10, float(config.timeout)),
        )
        self._compartment_id = config.compartment_id or os.environ.get(
            "OCI_COMPARTMENT_ID", sdk_config.get("tenancy")
        )
        self._config = config

    def complete(self, *, system: str, user: str, max_tokens: int, timeout: float) -> str:
        del timeout  # client timeout is fixed at construction to avoid mutable global state
        models = self._oci.generative_ai_inference.models
        kwargs: dict[str, Any] = {
            "messages": [
                models.SystemMessage(content=[models.TextContent(text=system)]),
                models.UserMessage(content=[models.TextContent(text=user)]),
            ],
            "max_tokens": min(max_tokens, self._config.max_tokens),
        }
        # Only send temperature when explicitly configured.  The final run must
        # record whether the selected OCI endpoint accepted it; we do not claim
        # deterministic temperature-zero behavior by default.
        if self._config.temperature is not None:
            kwargs["temperature"] = self._config.temperature
        response = self._client.chat(
            models.ChatDetails(
                compartment_id=self._compartment_id,
                serving_mode=models.OnDemandServingMode(model_id=self._config.model_id),
                chat_request=models.GenericChatRequest(**kwargs),
            )
        ).data.chat_response
        message = response.choices[0].message
        return "".join(
            item.text for item in (message.content or []) if getattr(item, "text", None)
        )

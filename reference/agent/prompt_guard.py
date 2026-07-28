"""Local prompt-injection sequence-classification adapter."""

from __future__ import annotations

import time
from typing import Any, Protocol

import numpy as np

from vanguard.shared.config import SecurityConfig
from vanguard.shared.errors import SecurityError


class Classifier(Protocol):
    def __call__(self, text: str, **kwargs: Any) -> Any: ...


class OnnxClassifier:
    def __init__(self, model_path: str) -> None:
        import onnxruntime as ort
        from transformers import AutoConfig, AutoTokenizer, PreTrainedTokenizerFast

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
        except ValueError as exc:
            # Some public tokenizer-only exports identify their generic Rust
            # backend as ``TokenizersBackend``, which AutoTokenizer cannot map
            # to a Python class. Loading tokenizer.json directly is equivalent
            # and keeps the runtime independent of custom model code.
            if "TokenizersBackend" not in str(exc):
                raise
            self._tokenizer = PreTrainedTokenizerFast(
                tokenizer_file=f"{model_path}/tokenizer.json"
            )
        config = AutoConfig.from_pretrained(model_path)
        self._labels = {
            int(index): str(label) for index, label in config.id2label.items()
        }
        self._session = ort.InferenceSession(
            f"{model_path}/model.onnx", providers=["CPUExecutionProvider"]
        )
        self._input_names = {item.name for item in self._session.get_inputs()}

    def __call__(self, text: str, **kwargs: Any) -> list[dict[str, Any]]:
        encoded = self._tokenizer(
            text,
            truncation=bool(kwargs.get("truncation", True)),
            max_length=int(kwargs.get("max_length", 512)),
            return_tensors="np",
        )
        inputs = {
            name: np.asarray(value, dtype=np.int64)
            for name, value in encoded.items()
            if name in self._input_names
        }
        logits = np.asarray(self._session.run(None, inputs)[0][0], dtype=np.float64)
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        return [
            {"label": self._labels.get(index, f"LABEL_{index}"), "score": float(score)}
            for index, score in enumerate(probabilities)
        ]


class PromptGuard:
    """Preloaded semantic classifier; no network call occurs during classification."""

    def __init__(self, config: SecurityConfig, classifier: Classifier | None = None) -> None:
        self.config = config
        self._classifier = classifier or self._load_classifier()

    def _load_classifier(self) -> Classifier:
        try:
            return OnnxClassifier(self.config.prompt_guard_model_path)
        except Exception as exc:
            raise SecurityError(f"Prompt-injection classifier failed to load: {exc}") from exc

    def classify(self, text: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            raw = self._classifier(
                text,
                top_k=None,
                truncation=True,
                max_length=self.config.prompt_guard_max_length,
            )
        except Exception as exc:
            raise SecurityError(f"Prompt-injection classifier inference failed: {exc}") from exc
        scores = raw[0] if raw and isinstance(raw[0], list) else raw
        if not isinstance(scores, list) or not scores:
            raise SecurityError("Prompt-injection classifier returned an invalid classification")
        normalized = {
            str(item.get("label", "")).lower(): float(item.get("score", 0.0))
            for item in scores
            if isinstance(item, dict)
        }
        attack_score = max(
            (
                score
                for label, score in normalized.items()
                if label not in {"benign", "label_0", "0"}
            ),
            default=0.0,
        )
        malicious = attack_score >= self.config.prompt_guard_threshold
        return {
            "malicious": malicious,
            "reason": (
                f"Semantic prompt-injection score {attack_score:.4f}"
                if malicious
                else None
            ),
            "classifier": self.config.prompt_guard_model_id,
            "score": attack_score,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        }

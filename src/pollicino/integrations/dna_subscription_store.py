from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

from .dna_subscription import DNATopicSubscription


DNA_SUBSCRIPTION_STATE_SCHEMA = "pollicino-dna-subscriptions-v1"


def _canonical(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class DNASubscriptionRegistry:
    """Persist application-level DNA subscriptions beside one carried node.

    This registry is intentionally outside ``PollicinoNodeRuntime``. The node
    core keeps transport/object state, while the application owns which DNA
    micro-information it wants to accept. The registry stores only local policy;
    it is not a subscription dissemination protocol.
    """

    def __init__(self, root: str | os.PathLike[str], *, node_id: str) -> None:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("node_id must be a non-empty string")
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._state_path = self._root / "dna-subscriptions.json"
        self._node_id = node_id
        self._subscriptions: dict[str, DNATopicSubscription] = {}
        self._active_id: str | None = None

        if self._state_path.exists():
            self._load()
        else:
            self._save()

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def active_id(self) -> str | None:
        return self._active_id

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._subscriptions))

    def get(self, subscription_id: str) -> DNATopicSubscription:
        try:
            return self._subscriptions[subscription_id]
        except KeyError as exc:
            raise LookupError("unknown DNA subscription") from exc

    def require_active(self) -> DNATopicSubscription:
        if self._active_id is None:
            raise LookupError("no active DNA subscription")
        return self.get(self._active_id)

    def upsert(self, subscription_id: str, subscription: DNATopicSubscription) -> None:
        self._validate_id(subscription_id)
        if not isinstance(subscription, DNATopicSubscription):
            raise TypeError("subscription must be DNATopicSubscription")
        self._subscriptions[subscription_id] = subscription
        self._save()

    def select(self, subscription_id: str) -> None:
        self.get(subscription_id)
        self._active_id = subscription_id
        self._save()

    def remove(self, subscription_id: str) -> None:
        self.get(subscription_id)
        del self._subscriptions[subscription_id]
        if self._active_id == subscription_id:
            self._active_id = None
        self._save()

    @staticmethod
    def _validate_id(subscription_id: str) -> None:
        if not isinstance(subscription_id, str) or not subscription_id:
            raise ValueError("subscription_id must be a non-empty string")
        if len(subscription_id.encode("utf-8")) > 128:
            raise ValueError("subscription_id exceeds 128 UTF-8 bytes")

    def _state_mapping(self) -> dict[str, object]:
        return {
            "schema": DNA_SUBSCRIPTION_STATE_SCHEMA,
            "node_id": self.node_id,
            "active_id": self.active_id,
            "subscriptions": [
                {
                    "id": subscription_id,
                    "domains": list(self._subscriptions[subscription_id].domains),
                    "intent_codes": list(self._subscriptions[subscription_id].intent_codes),
                }
                for subscription_id in sorted(self._subscriptions)
            ],
        }

    def _save(self) -> None:
        state = self._state_mapping()
        canonical = _canonical(state)
        envelope = {
            "schema": DNA_SUBSCRIPTION_STATE_SCHEMA,
            "state": state,
            "state_sha256": hashlib.sha256(canonical).hexdigest(),
        }
        encoded = (
            json.dumps(
                envelope,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            + "\n"
        ).encode("utf-8")
        _atomic_write(self._state_path, encoded)

    def _load(self) -> None:
        try:
            envelope = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("DNA subscription state is not valid UTF-8 JSON") from exc
        if not isinstance(envelope, Mapping):
            raise ValueError("DNA subscription state envelope must be an object")
        if envelope.get("schema") != DNA_SUBSCRIPTION_STATE_SCHEMA:
            raise ValueError("unsupported DNA subscription state schema")
        state = envelope.get("state")
        digest = envelope.get("state_sha256")
        if not isinstance(state, Mapping) or not isinstance(digest, str):
            raise ValueError("DNA subscription state envelope is incomplete")
        if hashlib.sha256(_canonical(state)).hexdigest() != digest:
            raise ValueError("DNA subscription state integrity check failed")
        if state.get("schema") != DNA_SUBSCRIPTION_STATE_SCHEMA:
            raise ValueError("unsupported DNA subscription state body schema")
        if state.get("node_id") != self.node_id:
            raise ValueError("DNA subscription state belongs to a different node")

        active_id = state.get("active_id")
        if active_id is not None and not isinstance(active_id, str):
            raise ValueError("active DNA subscription id is invalid")
        records = state.get("subscriptions")
        if not isinstance(records, list):
            raise ValueError("DNA subscription records must be an array")

        subscriptions: dict[str, DNATopicSubscription] = {}
        for record in records:
            if not isinstance(record, Mapping):
                raise ValueError("DNA subscription record must be an object")
            subscription_id = record.get("id")
            domains = record.get("domains")
            intent_codes = record.get("intent_codes")
            self._validate_id(subscription_id)
            if not isinstance(domains, list) or not all(isinstance(item, str) for item in domains):
                raise ValueError("DNA subscription domains are invalid")
            if not isinstance(intent_codes, list) or not all(isinstance(item, int) for item in intent_codes):
                raise ValueError("DNA subscription intent codes are invalid")
            if subscription_id in subscriptions:
                raise ValueError("duplicate DNA subscription id")
            subscriptions[subscription_id] = DNATopicSubscription(
                domains=tuple(domains),
                intent_codes=tuple(intent_codes),
            )

        if active_id is not None and active_id not in subscriptions:
            raise ValueError("active DNA subscription is missing")
        self._subscriptions = subscriptions
        self._active_id = active_id

from __future__ import annotations

from dataclasses import dataclass
import base64
import binascii
import calendar
from datetime import datetime, timezone
import json
import math
import struct
from typing import Any, Mapping

from pollicino.net import (
    ContentManifest,
    DiscoveryDescriptor,
    MAX_AUTH_BYTES,
    MAX_METADATA_BYTES,
    RetrievalSource,
    manifest_for_content,
)


DNA_SCHEMA_VERSION = "0.1"
DNA_TRACE_OBJECT_CLASS = 0xD1
DNA_FLAG_INLINE = 0x01
DNA_FLAG_REFERENCE = 0x02
DNA_INLINE_MAGIC = b"DNI1"
DNA_REFERENCE_META = b"DNR1"

DOMAIN_CODES = {
    "travel": 0,
    "shopping": 1,
    "social": 2,
    "mobility": 3,
    "local_services": 4,
}
RENDEZVOUS_CAPABILITY_CODES = {
    "internet": 0,
    "ble": 1,
    "nfc": 2,
    "wifi_aware": 3,
    "wifi_direct": 4,
    "lora": 5,
    "qr": 6,
}

_INLINE_FIXED = struct.Struct(">4sQBBBBB")


class DNAIntegrationError(ValueError):
    pass


class InlineDNATraceUnavailable(DNAIntegrationError):
    pass


def _ensure_string(name: str, value: Any, minimum: int, maximum: int) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise DNAIntegrationError(f"{name} must be a string with length {minimum}..{maximum}")
    return value


def _parse_datetime(name: str, value: str) -> datetime:
    if not isinstance(value, str):
        raise DNAIntegrationError(f"{name} must be an RFC3339/date-time string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DNAIntegrationError(f"{name} is not a valid date-time") from exc
    if parsed.tzinfo is None:
        raise DNAIntegrationError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _epoch_seconds(parsed: datetime) -> int:
    if parsed.microsecond:
        raise InlineDNATraceUnavailable("inline DNA profile requires whole-second timestamps")
    return calendar.timegm(parsed.utctimetuple())


def _canonical_timestamp(epoch_seconds: int) -> str:
    return datetime.fromtimestamp(epoch_seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ttl_seconds(trace: DNATraceV01) -> int:
    issued = _parse_datetime("issuedAt", trace.issued_at)
    expires = _parse_datetime("expiresAt", trace.expires_at)
    delta = (expires - issued).total_seconds()
    if delta < 0:
        raise DNAIntegrationError("expiresAt must not precede issuedAt")
    ttl = math.ceil(delta)
    if ttl > 0xFFFFFFFF:
        raise DNAIntegrationError("DNA trace lifetime exceeds PND1 TTL range")
    return ttl


def _unique_known_tuple(name: str, value: Any, codes: Mapping[str, int], *, minimum: int, maximum: int) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise DNAIntegrationError(f"{name} must be an array")
    items = tuple(value)
    if not minimum <= len(items) <= maximum:
        raise DNAIntegrationError(f"{name} must contain {minimum}..{maximum} items")
    if any(not isinstance(item, str) or item not in codes for item in items):
        raise DNAIntegrationError(f"{name} contains an unsupported value")
    if len(set(items)) != len(items):
        raise DNAIntegrationError(f"{name} must contain unique values")
    return items


def _is_code_ordered(items: tuple[str, ...], codes: Mapping[str, int]) -> bool:
    """Return whether a sequence already matches the deterministic code order.

    PND1 inline mode stores DNA domains/capabilities as bit masks. A bit mask
    preserves membership but not the JSON array order. Therefore inline mode is
    safe only when decoding the mask recreates exactly the original ordering;
    otherwise the authoritative trace is carried by reference instead.
    """

    return items == tuple(sorted(items, key=codes.__getitem__))


@dataclass(frozen=True, slots=True)
class DNATraceV01:
    trace_id: str
    ephemeral_sender_id: str
    domains: tuple[str, ...]
    intent_codes: tuple[int, ...]
    rendezvous_capabilities: tuple[str, ...]
    issued_at: str
    expires_at: str
    nonce: int
    authenticator: bytes
    coarse_geo_cell: str | None = None

    def __post_init__(self) -> None:
        _ensure_string("trace_id", self.trace_id, 1, 128)
        _ensure_string("ephemeral_sender_id", self.ephemeral_sender_id, 8, 128)
        _unique_known_tuple("domains", self.domains, DOMAIN_CODES, minimum=1, maximum=8)
        _unique_known_tuple(
            "rendezvous_capabilities",
            self.rendezvous_capabilities,
            RENDEZVOUS_CAPABILITY_CODES,
            minimum=1,
            maximum=8,
        )
        if not isinstance(self.intent_codes, tuple) or len(self.intent_codes) > 16:
            raise DNAIntegrationError("intent_codes must be a tuple with at most 16 entries")
        if any(not isinstance(code, int) or not 0 <= code <= 0xFFFF for code in self.intent_codes):
            raise DNAIntegrationError("intent_codes must contain unsigned 16-bit integers")
        if len(set(self.intent_codes)) != len(self.intent_codes):
            raise DNAIntegrationError("intent_codes must contain unique values")
        if self.coarse_geo_cell is not None:
            _ensure_string("coarse_geo_cell", self.coarse_geo_cell, 1, 32)
        issued = _parse_datetime("issued_at", self.issued_at)
        expires = _parse_datetime("expires_at", self.expires_at)
        if expires < issued:
            raise DNAIntegrationError("expires_at must not precede issued_at")
        if not isinstance(self.nonce, int) or not 0 <= self.nonce <= 0xFFFFFFFFFFFFFFFF:
            raise DNAIntegrationError("nonce must fit the PND1 unsigned 64-bit field")
        if not isinstance(self.authenticator, bytes):
            raise DNAIntegrationError("authenticator must be bytes")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DNATraceV01:
        if not isinstance(value, Mapping):
            raise DNAIntegrationError("DNATrace must be a mapping")
        required = {
            "schemaVersion",
            "traceId",
            "ephemeralSenderId",
            "domains",
            "intentCodes",
            "rendezvousCapabilities",
            "issuedAt",
            "expiresAt",
            "nonce",
            "authenticator",
        }
        allowed = required | {"coarseGeoCell"}
        missing = required - set(value)
        extra = set(value) - allowed
        if missing:
            raise DNAIntegrationError(f"DNATrace is missing required fields: {sorted(missing)}")
        if extra:
            raise DNAIntegrationError(f"DNATrace has unsupported fields: {sorted(extra)}")
        if value["schemaVersion"] != DNA_SCHEMA_VERSION:
            raise DNAIntegrationError("unsupported DNATrace schemaVersion")

        trace_id = _ensure_string("traceId", value["traceId"], 1, 128)
        sender = _ensure_string("ephemeralSenderId", value["ephemeralSenderId"], 8, 128)
        domains = _unique_known_tuple("domains", value["domains"], DOMAIN_CODES, minimum=1, maximum=8)
        caps = _unique_known_tuple(
            "rendezvousCapabilities",
            value["rendezvousCapabilities"],
            RENDEZVOUS_CAPABILITY_CODES,
            minimum=1,
            maximum=8,
        )
        intent_value = value["intentCodes"]
        if not isinstance(intent_value, (list, tuple)) or len(intent_value) > 16:
            raise DNAIntegrationError("intentCodes must be an array with at most 16 entries")
        intents = tuple(intent_value)
        if any(not isinstance(code, int) or not 0 <= code <= 0xFFFF for code in intents):
            raise DNAIntegrationError("intentCodes must contain unsigned 16-bit integers")
        if len(set(intents)) != len(intents):
            raise DNAIntegrationError("intentCodes must contain unique values")

        coarse = value.get("coarseGeoCell")
        if coarse is not None:
            coarse = _ensure_string("coarseGeoCell", coarse, 1, 32)

        nonce = value["nonce"]
        if not isinstance(nonce, int) or nonce < 0:
            raise DNAIntegrationError("nonce must be a non-negative integer")

        auth_text = value["authenticator"]
        if not isinstance(auth_text, str) or len(auth_text) > 128:
            raise DNAIntegrationError("authenticator must be a base64 string no longer than 128 characters")
        try:
            authenticator = base64.b64decode(auth_text, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise DNAIntegrationError("authenticator is not valid base64") from exc

        return cls(
            trace_id=trace_id,
            ephemeral_sender_id=sender,
            domains=domains,
            intent_codes=intents,
            rendezvous_capabilities=caps,
            issued_at=value["issuedAt"],
            expires_at=value["expiresAt"],
            nonce=nonce,
            authenticator=authenticator,
            coarse_geo_cell=coarse,
        )

    def to_mapping(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schemaVersion": DNA_SCHEMA_VERSION,
            "traceId": self.trace_id,
            "ephemeralSenderId": self.ephemeral_sender_id,
            "domains": list(self.domains),
            "intentCodes": list(self.intent_codes),
            "rendezvousCapabilities": list(self.rendezvous_capabilities),
            "issuedAt": self.issued_at,
            "expiresAt": self.expires_at,
            "nonce": self.nonce,
            "authenticator": base64.b64encode(self.authenticator).decode("ascii"),
        }
        if self.coarse_geo_cell is not None:
            result["coarseGeoCell"] = self.coarse_geo_cell
        return result

    def canonical_json(self) -> bytes:
        return json.dumps(
            self.to_mapping(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")


def dna_trace_from_canonical_json(data: bytes) -> DNATraceV01:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DNAIntegrationError("DNA trace JSON is invalid") from exc
    return DNATraceV01.from_mapping(value)


def _domain_mask(domains: tuple[str, ...]) -> int:
    mask = 0
    for domain in domains:
        mask |= 1 << DOMAIN_CODES[domain]
    return mask


def _capability_mask(capabilities: tuple[str, ...]) -> int:
    mask = 0
    for capability in capabilities:
        mask |= 1 << RENDEZVOUS_CAPABILITY_CODES[capability]
    return mask


def _decode_mask(mask: int, codes: Mapping[str, int], name: str) -> tuple[str, ...]:
    known_mask = sum(1 << bit for bit in codes.values())
    if mask & ~known_mask:
        raise DNAIntegrationError(f"{name} contains unknown bits")
    return tuple(name_value for name_value, bit in codes.items() if mask & (1 << bit))


def _encode_inline_metadata(trace: DNATraceV01) -> tuple[bytes, int]:
    issued = _parse_datetime("issuedAt", trace.issued_at)
    expires = _parse_datetime("expiresAt", trace.expires_at)
    issued_epoch = _epoch_seconds(issued)
    expires_epoch = _epoch_seconds(expires)
    if trace.issued_at != _canonical_timestamp(issued_epoch) or trace.expires_at != _canonical_timestamp(expires_epoch):
        raise InlineDNATraceUnavailable(
            "inline DNA profile requires canonical UTC timestamps ending in Z"
        )
    if not _is_code_ordered(trace.domains, DOMAIN_CODES) or not _is_code_ordered(
        trace.rendezvous_capabilities,
        RENDEZVOUS_CAPABILITY_CODES,
    ):
        raise InlineDNATraceUnavailable(
            "inline DNA profile requires canonical domain/capability ordering"
        )
    ttl = expires_epoch - issued_epoch
    if ttl < 0 or ttl > 0xFFFFFFFF:
        raise InlineDNATraceUnavailable("inline DNA lifetime is outside PND1 range")
    if len(trace.authenticator) > MAX_AUTH_BYTES:
        raise InlineDNATraceUnavailable("inline DNA authenticator exceeds PND1 limit")

    trace_id = trace.trace_id.encode("utf-8")
    sender = trace.ephemeral_sender_id.encode("utf-8")
    geo = b"" if trace.coarse_geo_cell is None else trace.coarse_geo_cell.encode("utf-8")
    if any(len(value) > 0xFF for value in (trace_id, sender, geo)):
        raise InlineDNATraceUnavailable("inline DNA UTF-8 field exceeds one-byte length")

    body = bytearray(
        _INLINE_FIXED.pack(
            DNA_INLINE_MAGIC,
            issued_epoch,
            _domain_mask(trace.domains),
            len(trace.intent_codes),
            len(trace_id),
            len(sender),
            len(geo),
        )
    )
    for code in trace.intent_codes:
        body += struct.pack(">H", code)
    body += trace_id
    body += sender
    body += geo
    if len(body) > MAX_METADATA_BYTES:
        raise InlineDNATraceUnavailable(
            f"inline DNA metadata requires {len(body)} bytes, limit is {MAX_METADATA_BYTES}"
        )
    return bytes(body), ttl


def dna_trace_to_descriptor(
    trace: DNATraceV01,
    *,
    coordinate: bytes,
    prefer_inline: bool = True,
    radio_authenticator: bytes | None = None,
    hop_limit: int = 0,
) -> DiscoveryDescriptor:
    """Map a DNA trace to generic PND1 without adding DNA to the core.

    Inline mode reconstructs the normalized DNA trace directly from PND1 and
    therefore uses the trace authenticator as the descriptor authenticator.
    Reference mode carries only a DNA integration marker and an opaque
    coordinate; the authoritative canonical DNATrace is retrieved as exact
    content through the generic PNM1 resolver/provider path.
    """

    if not isinstance(trace, DNATraceV01):
        raise TypeError("trace must be DNATraceV01")
    if radio_authenticator is not None:
        if not isinstance(radio_authenticator, bytes) or len(radio_authenticator) > MAX_AUTH_BYTES:
            raise DNAIntegrationError("radio_authenticator exceeds PND1 authenticator limit")

    if prefer_inline and (radio_authenticator is None or radio_authenticator == trace.authenticator):
        try:
            metadata, ttl = _encode_inline_metadata(trace)
        except InlineDNATraceUnavailable:
            pass
        else:
            return DiscoveryDescriptor(
                object_class=DNA_TRACE_OBJECT_CLASS,
                flags=DNA_FLAG_INLINE,
                capability_mask=_capability_mask(trace.rendezvous_capabilities),
                ttl_seconds=ttl,
                hop_limit=hop_limit,
                nonce=trace.nonce,
                rendezvous_key=coordinate,
                metadata=metadata,
                authenticator=trace.authenticator,
            )

    ttl = _ttl_seconds(trace)
    if radio_authenticator is None:
        if len(trace.authenticator) > MAX_AUTH_BYTES:
            raise DNAIntegrationError(
                "reference DNA descriptor needs an explicit compact radio_authenticator "
                "when the trace authenticator exceeds the PND1 limit"
            )
        radio_authenticator = trace.authenticator

    return DiscoveryDescriptor(
        object_class=DNA_TRACE_OBJECT_CLASS,
        flags=DNA_FLAG_REFERENCE,
        capability_mask=_capability_mask(trace.rendezvous_capabilities),
        ttl_seconds=ttl,
        hop_limit=hop_limit,
        nonce=trace.nonce,
        rendezvous_key=coordinate,
        metadata=DNA_REFERENCE_META,
        authenticator=radio_authenticator,
    )


def dna_trace_from_inline_descriptor(descriptor: DiscoveryDescriptor) -> DNATraceV01:
    if descriptor.object_class != DNA_TRACE_OBJECT_CLASS or descriptor.flags != DNA_FLAG_INLINE:
        raise DNAIntegrationError("descriptor is not an inline DNA trace")
    data = descriptor.metadata
    if len(data) < _INLINE_FIXED.size:
        raise DNAIntegrationError("inline DNA metadata is truncated")
    magic, issued_epoch, domain_mask, intent_count, trace_len, sender_len, geo_len = _INLINE_FIXED.unpack_from(data)
    if magic != DNA_INLINE_MAGIC:
        raise DNAIntegrationError("invalid inline DNA metadata magic")

    cursor = _INLINE_FIXED.size
    intents_end = cursor + intent_count * 2
    fields_end = intents_end + trace_len + sender_len + geo_len
    if fields_end != len(data):
        raise DNAIntegrationError("inline DNA metadata length mismatch")

    intents = []
    for _ in range(intent_count):
        intents.append(struct.unpack_from(">H", data, cursor)[0])
        cursor += 2
    try:
        trace_id = data[cursor : cursor + trace_len].decode("utf-8")
        cursor += trace_len
        sender = data[cursor : cursor + sender_len].decode("utf-8")
        cursor += sender_len
        geo_bytes = data[cursor : cursor + geo_len]
        geo = geo_bytes.decode("utf-8") if geo_bytes else None
    except UnicodeDecodeError as exc:
        raise DNAIntegrationError("inline DNA text field is not valid UTF-8") from exc

    domains = _decode_mask(domain_mask, DOMAIN_CODES, "DNA domain mask")
    capabilities = _decode_mask(
        descriptor.capability_mask,
        RENDEZVOUS_CAPABILITY_CODES,
        "DNA rendezvous capability mask",
    )
    if not domains or not capabilities:
        raise DNAIntegrationError("inline DNA descriptor must contain domain and capability bits")

    return DNATraceV01(
        trace_id=trace_id,
        ephemeral_sender_id=sender,
        domains=domains,
        intent_codes=tuple(intents),
        rendezvous_capabilities=capabilities,
        issued_at=_canonical_timestamp(issued_epoch),
        expires_at=_canonical_timestamp(issued_epoch + descriptor.ttl_seconds),
        nonce=descriptor.nonce,
        authenticator=descriptor.authenticator,
        coarse_geo_cell=geo,
    )


def is_dna_reference_descriptor(descriptor: DiscoveryDescriptor) -> bool:
    return (
        descriptor.object_class == DNA_TRACE_OBJECT_CLASS
        and descriptor.flags == DNA_FLAG_REFERENCE
        and descriptor.metadata == DNA_REFERENCE_META
    )


def dna_trace_manifest(
    trace: DNATraceV01,
    *,
    provider_id: str,
    locator: bytes,
) -> ContentManifest:
    """Wrap canonical DNATrace bytes in the generic exact-content manifest."""

    return manifest_for_content(
        trace.canonical_json(),
        object_class=DNA_TRACE_OBJECT_CLASS,
        sources=(RetrievalSource(provider_id=provider_id, locator=locator),),
    )

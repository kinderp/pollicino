from __future__ import annotations

import base64
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

pytest.importorskip("faro_profiles.async_query")

from faro_profiles.async_query import FAROPollicinoAsyncQuerySource
from faro_profiles.contracts import canonical_json
from faro_profiles.import_transaction import logical_store_digest
from faro_profiles.local_store import LocalKnowledgeStore
from faro_profiles.pollicino_adapter import FAROPollicinoAdapter, FAROPollicinoError
from faro_profiles.publisher import initialize_publisher, signing_key
from faro_profiles.registry_protocol import build_registry_query
from faro_profiles.store import ROOT, load_json
from faro_profiles.trust import (
    LocalTrustStore,
    import_transfer_artifact,
    sign_package,
    trust_decision,
    verify_envelope,
    write_signed_envelope,
)

from pollicino.net import (
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    RetrievalSource,
    manifest_for_content,
    retrieve_exact,
)
from pollicino.net.contact import (
    MAX_CONTACT_BYTES,
    MAX_CONTACT_ITEMS,
    ContactBudget,
    ContactNode,
    ContactSelection,
    run_contact,
)
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore


AUTO_PATH = ROOT / "artifacts" / "r2_auto_reference.faro.json"


class StaticRegistry:
    def __init__(self, package_ids: tuple[str, ...]) -> None:
        self.package_ids = package_ids
        self.calls = 0

    def search(self, _query: dict) -> dict:
        self.calls += 1
        return {
            "schema_version": "faro.registry-search-result.v0",
            "results": [{"package_id": value} for value in self.package_ids],
            "complete_global_search": False,
            "search_result_is_recommendation": False,
        }


def budget() -> ContactBudget:
    return ContactBudget(MAX_CONTACT_ITEMS, MAX_CONTACT_BYTES)


def faro_node(source: FAROPollicinoAsyncQuerySource, label: str) -> ContactNode:
    return ContactNode(
        source.discovery_source.native_catalog,
        source.native_query_store,
        label,
    )


def generic_mule(root: Path, label: str = "C") -> ContactNode:
    root.mkdir(exist_ok=True)
    return ContactNode(
        PersistentBoundedReferenceCatalog(root / "catalog"),
        PersistentQueryResultStore(root / "queries"),
        label,
    )


def close_mule(node: ContactNode) -> None:
    node.catalog.close()  # type: ignore[attr-defined]
    node.query_results.close()  # type: ignore[attr-defined]


def signed_fixture(root: Path):
    publisher = root / "publisher"
    initialize_publisher(publisher, "PX8 publisher")
    private_key, _ = signing_key(publisher)
    package = load_json(AUTO_PATH)
    envelope = sign_package(package, private_key, publisher_label="PX8 fixture")
    artifact = root / "signed.faro.json"
    write_signed_envelope(envelope, artifact)
    return package, envelope, artifact, publisher


def test_exact_faro_px7_query_result_reference_px1_and_explicit_import_mule(
    tmp_path: Path,
) -> None:
    package, envelope, artifact, publisher = signed_fixture(tmp_path)
    transport = FAROPollicinoAdapter()
    reference = transport.publish_package(canonical_json(envelope).encode("utf-8"))
    a_root, b_root, c_root = tmp_path / "A", tmp_path / "B", tmp_path / "C"
    knowledge = LocalKnowledgeStore(tmp_path / "knowledge")
    knowledge.initialize()
    unknown = LocalTrustStore(tmp_path / "unknown-trust")
    blocked = LocalTrustStore(tmp_path / "blocked-trust")
    added = blocked.add(
        publisher / "publisher-public.pem", "blocked", trust_state="TRUSTED"
    )
    blocked.revoke(added["publisher"]["key_fingerprint"], "KEY_COMPROMISED")
    recommendation = {"schema_version": "faro.recommendation.v0", "result": "HOLD"}
    before = (
        logical_store_digest(knowledge),
        unknown.digest(),
        blocked.digest(),
        canonical_json(recommendation),
    )

    with FAROPollicinoAsyncQuerySource(a_root) as a, FAROPollicinoAsyncQuerySource(
        b_root
    ) as b:
        mule = generic_mule(c_root)
        b.discovery_source.advertise_reference(reference)
        a.submit_query(
            b"px8-query",
            build_registry_query(package_type=package["package_type"]),
        )

        q_to_c = run_contact(faro_node(a, "A"), mule, budget=budget())
        assert q_to_c.left_to_right.queries == 1
        assert b.native_query_store.query_count == 0
        close_mule(mule)

        mule = generic_mule(c_root, "C-after-query-restart")
        q_to_b = run_contact(mule, faro_node(b, "B"), budget=budget())
        assert q_to_b.left_to_right.queries == 1
        assert not b.evaluator_attached
        evaluator = StaticRegistry((reference.package_id,))
        b.attach_evaluator(evaluator)
        evaluation = b.evaluate_incoming_query(b"px8-query", result_ids=b"B-result")
        assert evaluation.emitted_package_ids == (reference.package_id,)
        assert evaluator.calls == 1

        r_to_c = run_contact(faro_node(b, "B"), mule, budget=budget())
        assert r_to_c.left_to_right.results == 1
        close_mule(mule)
        mule = generic_mule(c_root, "C-after-result-restart")
        r_to_a = run_contact(mule, faro_node(a, "A"), budget=budget())
        assert r_to_a.left_to_right.results == 1
        candidate = a.query_status(b"px8-query").candidates[0]
        assert candidate.package_id == reference.package_id
        assert a.discovery_source.item_count == 0

        # Candidate receipt never selects or pulls D2 state.
        assert logical_store_digest(knowledge) == before[0]
        assert unknown.digest() == before[1]
        assert blocked.digest() == before[2]
        assert canonical_json(recommendation) == before[3]

        # Selection is explicit independently at B->C and C->A.
        key = reference.package_id.encode("ascii")
        d2_to_c = run_contact(
            faro_node(b, "B"),
            mule,
            budget=budget(),
            selection=ContactSelection(right_wants_from_left=(key,)),
        )
        assert d2_to_c.left_to_right.references == 1
        close_mule(mule)
        mule = generic_mule(c_root, "C-after-reference-restart")
        d2_to_a = run_contact(
            mule,
            faro_node(a, "A"),
            budget=budget(),
            selection=ContactSelection(right_wants_from_left=(key,)),
        )
        assert d2_to_a.left_to_right.references == 1
        assert a.discovery_source.get_reference(reference.package_id).encode() == reference.encode()

        # PX1 remains an explicit operation after D2 arrival.
        fetched = transport.retrieve_package(reference)
        assert fetched.package_bytes == canonical_json(envelope).encode("utf-8")
        verification = verify_envelope(json.loads(fetched.package_bytes))
        assert verification["signature_status"] == "SIGNATURE_VALID"
        assert trust_decision(verification, unknown)["trust_status"] == "UNKNOWN"
        assert trust_decision(verification, blocked)["trust_status"] == "REVOKED"
        assert logical_store_digest(knowledge) == before[0]
        assert unknown.digest() == before[1]
        assert blocked.digest() == before[2]

        receipt = import_transfer_artifact(artifact, knowledge)
        assert receipt["result"] == "IMPORTED"
        assert logical_store_digest(knowledge) != before[0]
        close_mule(mule)


def test_faro_zero_match_result_survives_mule_and_is_not_global_completion(
    tmp_path: Path,
) -> None:
    with FAROPollicinoAsyncQuerySource(tmp_path / "A") as a, FAROPollicinoAsyncQuerySource(
        tmp_path / "B"
    ) as b:
        mule = generic_mule(tmp_path / "C")
        a.submit_query(b"zero", build_registry_query(package_type="not-present"))
        run_contact(faro_node(a, "A"), mule, budget=budget())
        run_contact(mule, faro_node(b, "B"), budget=budget())
        evaluator = StaticRegistry(())
        b.attach_evaluator(evaluator)
        b.evaluate_incoming_query(b"zero", result_ids=b"zero-result")
        run_contact(faro_node(b, "B"), mule, budget=budget())
        run_contact(mule, faro_node(a, "A"), budget=budget())
        status = a.query_status(b"zero")
        assert status.local_state == "ZERO_MATCH_RESULT_PRESENT"
        assert not status.global_complete
        assert status.candidates == ()
        close_mule(mule)


def test_invalid_signature_is_faro_failure_after_successful_contact_layers(
    tmp_path: Path,
) -> None:
    package, envelope, _, _ = signed_fixture(tmp_path)
    changed = copy.deepcopy(envelope)
    signature = bytearray(base64.b64decode(changed["signatures"][0]["signature_base64"]))
    signature[0] ^= 1
    changed["signatures"][0]["signature_base64"] = base64.b64encode(signature).decode()
    bad_bytes = canonical_json(changed).encode("utf-8")

    locator = hashlib.sha256(bad_bytes).digest()
    provider = InMemoryContentProvider()
    provider.put(locator, bad_bytes)
    manifest = manifest_for_content(
        bad_bytes,
        object_class=0xF4,
        sources=(RetrievalSource(provider_id="bad", locator=locator),),
    )
    coordinate = b"px8-invalid-signature"
    resolver = InMemoryResolver()
    resolver.register(coordinate, manifest)
    transport = FAROPollicinoAdapter()
    good = transport.publish_package(canonical_json(envelope).encode("utf-8"))
    bad_reference = replace(
        good,
        transport_sha256=hashlib.sha256(bad_bytes).hexdigest(),
        transport_manifest_sha256=hashlib.sha256(manifest.encode()).hexdigest(),
        rendezvous_key=coordinate,
        size_bytes=len(bad_bytes),
        retrieval_hints=("bad",),
    )

    with FAROPollicinoAsyncQuerySource(tmp_path / "A") as a, FAROPollicinoAsyncQuerySource(
        tmp_path / "B"
    ) as b:
        mule = generic_mule(tmp_path / "C")
        b.discovery_source.advertise_reference(bad_reference)
        a.submit_query(b"bad", build_registry_query(package_type=package["package_type"]))
        run_contact(faro_node(a, "A"), mule, budget=budget())
        run_contact(mule, faro_node(b, "B"), budget=budget())
        b.attach_evaluator(StaticRegistry((package["package_id"],)))
        b.evaluate_incoming_query(b"bad", result_ids=b"bad-result")
        run_contact(faro_node(b, "B"), mule, budget=budget())
        run_contact(mule, faro_node(a, "A"), budget=budget())
        key = package["package_id"].encode("ascii")
        run_contact(
            faro_node(b, "B"), mule, budget=budget(),
            selection=ContactSelection(right_wants_from_left=(key,)),
        )
        run_contact(
            mule, faro_node(a, "A"), budget=budget(),
            selection=ContactSelection(right_wants_from_left=(key,)),
        )
        reconstructed, report = retrieve_exact(
            DiscoveryDescriptor(
                object_class=0xF4,
                rendezvous_key=coordinate,
                ttl_seconds=0,
                nonce=0,
            ),
            resolver=resolver,
            providers={"bad": provider},
        )
        assert report.exact
        with pytest.raises(FAROPollicinoError) as raised:
            transport.verify_reconstructed_package(bad_reference, reconstructed)
        assert raised.value.code == "FARO_SIGNATURE_FAILURE"
        assert raised.value.layer == "FARO_AUTHENTICITY"
        close_mule(mule)


def test_faro_reference_variant_conflict_remains_faro_layered(tmp_path: Path) -> None:
    package, envelope, _, _ = signed_fixture(tmp_path)
    transport = FAROPollicinoAdapter()
    reference = transport.publish_package(canonical_json(envelope).encode("utf-8"))
    variant = replace(reference, retrieval_hints=("alternate",))
    with FAROPollicinoAsyncQuerySource(tmp_path / "A") as a:
        a.discovery_source.advertise_reference(reference)
        with pytest.raises(Exception) as raised:
            a.discovery_source.advertise_reference(variant)
        assert getattr(raised.value, "code", None) == "REFERENCE_VARIANT_CONFLICT"

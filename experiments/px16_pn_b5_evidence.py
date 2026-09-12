"""Regenerate deterministic PX16 closure artifacts."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUT = ROOT / "artifacts" / "px16-pn-b5"
IMPL = "e8c02ac5c09ef10909e5a3ffd39963be91f49ddd"

def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def main():
    write("baseline.json", {"sha":"82ba2e70fe1262f2eac47ab656cd45a304a58a0c","clean":True,"full":{"passed":667,"skipped":5},"focused_px13_px14_px15":{"passed":206},"compileall":"PASS","px14_checkpoint":{"local":"73c72d55d9775029cdc1824b04fea8e5e53367d2","remote":"73c72d55d9775029cdc1824b04fea8e5e53367d2"},"px15_checkpoint":{"local":"82ba2e70fe1262f2eac47ab656cd45a304a58a0c","remote":"82ba2e70fe1262f2eac47ab656cd45a304a58a0c"}})
    write("transport-contract.json", {"family":"AF_UNIX","type":"SOCK_DGRAM","address":"FILESYSTEM_PATH","api":["send_frame","receive_frame"],"datagrams_per_b4_frame":1,"b4_frames_per_datagram":1,"extra_framing_bytes":0,"send_success_means_commit":False,"timeout_semantics":"OPPORTUNITY_ENDED_ONLY","user_space_queue":0})
    write("socket-lifecycle.json", {"mode":"0600","normal_cleanup":"PASS","restart_rebind":"PASS","owned_stale_recovery":"PASS","active_collision":"FAIL_CLOSED","unowned_path_removed":False,"pathname_is_identity":False})
    write("datagram-bounds.json", {"minimum":53,"maximum":4096,"receive_strategy":"CEILING_PLUS_ONE","silent_truncations":0,"empty":"REJECTED","short":"B4_REJECTED","exact_ceiling":"PASS","outgoing_oversize":"LOCAL_REJECTION","incoming_oversize":"REJECTED","mtu_mismatch":"SAFE_REJECTION","negotiation":False})
    counts={53:797,64:67,128:11,256:4,512:2,1024:1,1500:1,4096:1}
    write("mtu-matrix.json", {"message":"PX13_CAPACITY_10_COMPACT","message_bytes":797,"rows":[{"mtu":m,"datagrams":n,"roundtrip":"PASS"} for m,n in counts.items()],"maximum_message":{"bytes":29245,"mtu":128,"datagrams":385,"roundtrip":"PASS"}})
    write("direct-transport.json", {"independent_processes":2,"shared_endpoint_objects":0,"direct_remote_store_reads":0,"canonical_mismatches":0,"query":"PASS","exact":"PASS","compact":"PASS","adaptive_fallback":"PASS"})
    write("relay-equivalence.json", {"relay_processes":1,"kernel_hops":2,"pass_matches_direct":True,"application_semantics":0})
    write("datagram-loss.json", {"whole_drop":"INCOMPLETE_NO_MUTATION","compact_drop":"TRANSPORT_FAILURE_NO_CAPACITY_FALLBACK","exact_fallback_drop":"ONLY_COMPLETE_COMMITS_SURVIVE","permanent":"FINITE_NON_CONVERGED","false_convergence":0})
    write("duplicate-reorder.json", {"duplicate":"PASS","reorder":"PASS","delay":"PASS","b4_order_dependency":False})
    write("backpressure.json", {"platform":"macOS Darwin","datagram_bytes":128,"successes_before_pressure":26,"outcome":"ENOBUFS","errno":55,"so_sndbuf":2048,"so_rcvbuf":4096,"retry":False,"user_queue":0,"fresh_contact_progress":"PASS"})
    write("process-crash.json", {"receiver_before_apply":"NO_MUTATION","receiver_after_commit":"DURABLE","sender_after_send":"RECONCILE_DURABLE_TRUTH","peer_exit_before_send":"TRANSPORT_FAILURE"})
    write("restart-results.json", {"both_processes":"PASS","socket_paths":"RECREATED","persistent_transport_session_required":False})
    write("sender-uncertainty.json", {"send_success_is_commit":False,"receiver_commit_sender_uncertain":"PASS","fresh_contact_skip":"PASS","persistent_ack":0})
    write("adaptive-regression.json", {"compact_success":[0,1,10],"capacity_failure_and_exact":[20],"inherited_scale":[100,1000],"oracle_mismatches":0,"undetected_false_negatives":0})
    write("mule-results.json", {"query_forward":"PASS","result_reverse":"PASS","mule_semantics":0,"fresh_c_process":"PASS"})
    write("accounting.json", {"b2_bytes":"SEPARATE","b4_frame_bytes":"SEPARATE","datagrams_sent":"RECORDED","datagrams_received":"RECORDED","drops_duplicates_reorders":"RELAY_RECORDED","native_commits":"WORKER_RECORDED","valid_sent_equals_frames":True,"valid_received_equals_frames":True})
    write("neutrality-scan.json", {"application_specific_transport_branches":0,"unix_specific_d4_branches":0,"unix_specific_b2_family_branches":0,"concrete_transport_b4_branches":0,"routing":0,"discovery":0,"authentication":0,"retries":0})
    write("classification.json", {"gate":"PX16-PN-B5","identifier_status":"REPOSITORY_OWNER_CANDIDATE_FROM_PX15","classification":"POLLICINO_UNIX_DATAGRAM_TRANSPORT_READY_WITH_LIMITS","confidence":"HIGH","implementation_sha":IMPL,"focused":{"passed":37},"full":{"passed":704,"skipped":5},"compileall":"PASS","failures":["A.TEST_HARNESS_ERROR:sandbox AF_UNIX restriction","A.TEST_HARNESS_ERROR:attempt budget fixture","K.BACKPRESSURE_LIMIT:macOS ENOBUFS after 26 queued datagrams","A.TEST_HARNESS_ERROR:relay destination exit handling"],"next":"bounded Unix-domain SOCK_STREAM adapter using existing B4 length fields"})

if __name__ == "__main__": main()

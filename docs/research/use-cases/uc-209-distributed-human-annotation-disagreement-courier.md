# UC-209 — Distributed Human Annotation Disagreement

**Problem:** Two disconnected groups may assign different labels to identical observations. Simple majority voting hides real ambiguity.

**Actors:** teacher, 2–3 student teams, independent reviewer, 4–6 relay boards.

**Why PollicinoNet:** Signed taxonomy version and item hashes identify differences without shipping all examples over LoRa.

**Bearers:** LoRa for disagreement summaries; BLE/Wi-Fi for selected examples; Internet optional; managed USB for large data.

**Software:** Simulate 100 public or synthetic items, label conflicts, missing replies and mismatched taxonomies. Keep an unresolved state.

**Hardware:** Label harmless object images in separate classrooms; exchange digests via real boards and contested examples via Wi-Fi.

**Privacy/security:** No identifying images or personal assessments; pseudonymous groups; preserve original signed labels.

**Difficulty:** Medium. UC-032 selects examples and UC-101 covers model disagreement; UC-209 addresses independent *human* adjudication. PHY unchanged.
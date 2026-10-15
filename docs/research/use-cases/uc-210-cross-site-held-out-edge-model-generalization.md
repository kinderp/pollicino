# UC-210 — Cross-Site Held-Out Edge Model Evaluation

**Problem:** A model validated in one lab may perform differently at another site.

**Actors:** teacher, several edge computers, model publisher and 4–6 relay boards.

**Why PollicinoNet:** Send a signed experiment plan and delayed aggregate results while source data stays local.

**Bearers:** LoRa for IDs and summaries; Wi-Fi/BLE for model files; Internet optional; USB for large artifacts.

**Software:** Evaluate a frozen model on three synthetic distributions. Compare random splits against site-held-out tests; reject mismatched versions.

**Hardware:** Use 3 laptops and 4–6 boards, then supervised regional sites. Record measured transport times separately from AI metrics.

**Privacy/security:** Check dataset licenses, release only approved aggregates, protect reserved answers.

**Difficulty:** High. Unlike UC-038 device tests, UC-210 tests out-of-site predictive behavior. No PHY changes.
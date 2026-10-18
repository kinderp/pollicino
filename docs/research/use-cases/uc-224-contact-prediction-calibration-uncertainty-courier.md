# UC-224 — Calibrating Contact Predictions, Not Just Routing Delivery

## Problem
A relay predicts a 70% chance of encountering a public checkpoint tomorrow. It may still make a sensible forwarding choice, but is **70% numerically trustworthy**? Persistent overconfidence wastes scarce capacity and makes field reports misleading. UC-224 evaluates probability calibration separately from packet delivery.

## Actors and Messina network
A small group of opt-in student relay boards, fixed supervised school/public checkpoint nodes in Messina–Villafranca–Rometta–Venetico, a privacy reviewer, and an offline evaluation PC. The experiment uses coarse checkpoint IDs and arranged supervised contacts. No student home commute or attendance logs.

## Why PollicinoNet and bearers
Forecasts are compact and naturally arrive asynchronously. Define the prediction before observing the outcome, bind to a versioned prediction-method ID, target checkpoint class, window ID, confidence, and observation completeness status. Late outcomes cannot be used to retroactively change the forecast.
- **LoRa:** bounded prediction commitment/ID, score digest and checkpoint-specific windows.
- **BLE:** exchange signed compact predictions and encounter confirmations locally.
- **Wi-Fi/LAN:** evaluation table, aggregate reliability bins and visual plots.
- **Internet:** optional sharing of synthetic or privacy-reviewed aggregate benchmark.
- **Physical USB/SD:** complete synthetic test traces or privately held, authorized evaluation log.
Explicitly distinguish no observed contact from incomplete logging; unknown outcomes are not automatic failures.

## Software-only trial (proposed, not executed)
Simulate 12 virtual relays and 100 expected windows with seeded, known encounter probabilities. Freeze forecasts before generating outcomes. Compare a calibrated baseline, overconfident model, always-50% model and stale predictor. Compute Brier score, per-bin reliability, coverage of complete observations, abstention rate and uncertainty bars. Inject delayed logs, missing receivers, duplicate contacts, clock drift, falsely elevated repeated encounters and data-leakage from training on evaluation windows. Report forecast quality on held-out periods only. Make routing performance a separate measurement; an accurate probability forecast need not imply good end-to-end delivery.

## Physical trial
Use 8–12 boards, at least two authorized fixed checkpoints, a controlled timetable of **voluntary** visits and independent TX/RX logging. Commit predicted contact windows before actual sessions; recover experiment data later by richer bearer. Evaluate only windows with defensible complete evidence. Record actual contacts, number of scored/unknown windows, forecast version and selection bias. More measurements will be needed before claiming improved network routing.

## Security, privacy, limitations and difficulty
**High.** Scope IDs to the experiment, avoid individual mobility scores or disciplinary uses, aggregate checkpoint statistics, separate opt-out from no-contact, protect prediction/truth join keys and define short deletion deadlines. Sign fixed forecasts to prevent after-the-fact editing. Never publish derived student movement histories or claim a generalizable model from short trials.

## Nonduplication check
UC-008 observes contact opportunities, UC-169 *uses* encounter history for forwarding, UC-183 compares routing policies under fair trials, UC-178 checks missing-denominator evidence and UC-216 releases synthetic traces. UC-224 exclusively measures whether predicted **contact probabilities themselves are calibrated**, even before a routing algorithm uses them.

Background: RFC 6693 PRoPHET, https://www.rfc-editor.org/rfc/rfc6693

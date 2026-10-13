# UC-200 — Controlled Emergency Drill Inject and After-Action Courier

## Problem to solve
Teams in a school-based emergency tabletop drill see messages in different orders. At the end, facilitators need evidence of what each team actually knew before it decided, not an invented global event order.

## Actors and practical Messina scenario
Teacher scenario controller, two mock school checkpoint teams, 6–10 relay boards, observer and after-action reviewer. No actual public warnings, impersonation of emergency authorities or active-incident deployment.

## Why PollicinoNet fits
EXERCISE_ONLY signed injects have scenario ID, issuer, audience, expiry, supersession and evidence hash. Each team returns authenticated seen/decision/unknown state. Later merge retains local timing uncertainty and human explanation.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: small exercise notice/ack/cancel; BLE/Wi-Fi: instructor media and logs; Internet: optional dashboard; paper cards/physical USB: exercise evidence.

## What can be tested immediately in software (proposed, not executed)
Three simulated islands; send out-of-order cancel/update, duplicates, fake inject, stale clock and missing contact. Evaluate correct state per team's evidence, unreachable participants, decision consistency and unknown fraction. Exercise outcome is not emergency-system certification.

## Physical hardware and required measurements
6–10 nodes at two controlled school stations; paper role cards and teacher-only gateway. Measure real inject delivery, receipt verification, and ability to reconstruct supported decisions. Avoid real alert channels.

## Privacy, security and implementation difficulty
MEDIUM–HIGH. Strong visible EXERCISE labels, distinct trust credentials, anti-replay, controlled audience, no actual personal casualty or location data, bounded storage.

## Difference from existing use cases
UC-002 issues signed bulletins, UC-097 campaigns, UC-132 alert supersession and UC-093 causal logs. UC-200 connects *exercise controller injects to team decisions and formal after-action evidence*.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.

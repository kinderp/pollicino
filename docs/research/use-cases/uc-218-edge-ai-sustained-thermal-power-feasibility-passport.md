# UC-218 — Sustained Edge-AI Thermal and Power Feasibility Passport

## Problem
A model may run successfully once on an edge computer, yet sustained inference can throttle, drain its battery or miss latency deadlines. UC-218 attaches a **verified operating-envelope passport** to an exact model/runtime/device/cooling configuration, separate from predictive accuracy.

## Actors, relevance and bearers
A model publisher, teacher/reviewer, a Pi or managed laptop, optional second host, and 2–4 student relay boards. At Messina and Rometta lab checkpoints, the worker can return a signed small feasibility result without moving full AI inputs. **LoRa:** job ID, hashes and compact status. **BLE/Wi-Fi:** model, logs, manifests and results. **Internet:** optional approved comparison. **Physical:** SD/SSD with public/synthetic workloads.

## Software now
Generate artificial runs with warming temperature, throttling, decreasing power and variable workload. Compare blind model-compatible admission with evidence-gated scheduling. Inject missing measurements, mislabelled variants and passport staleness. Maintain `tested`, `unknown` and `incompatible` explicitly; never treat simulation values as device measurements. Exact test manifest must bind model digest, quantization, runtime, firmware/OS, hardware, cooling, workload and ambient regime.

**Acceptance gate:** an obsolete or mismatched passport cannot silently certify task feasibility; all records mark simulated versus measured origin.

## Physical validation
Use one Pi, one school host and 2–4 LoRa boards; then repeat on a second host if available. With **safe manufacturer-recommended cooling**, public test inputs, fixed workloads and supervised power, measure temperatures, throttling flags, clock rate, tail latency and completion. Report joules/inference only with proper electrical instrumentation. Compare ambient/cooling conditions as distinct experiments; don't cause unsafe thermal or battery stress.

## Security, privacy, distinctness
No personal camera or audio data. Signed results, least-privileged jobs, bounded execution and no remote bypass of thermal protections. **Difficulty: medium-high.** Unlike UC-038 model evaluation, UC-085 variant compatibility or UC-210 cross-site generalization, this evaluates sustained energy/thermal viability.

Reference: https://www.mdpi.com/2079-9292/9/12/2106

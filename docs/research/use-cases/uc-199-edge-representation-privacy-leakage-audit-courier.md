# UC-199 — Edge-AI Representation Privacy-Leakage Audit Courier

## Problem to solve
A split-inference activation or embedding may reveal planted sensitive attributes despite not being raw data. We need an authorized controlled evaluation of leak-versus-utility before choosing a feature transport format.

## Actors and practical Messina scenario
Synthetic-dataset publisher, weak edge model, evaluation workstation, 4–6 student relay boards and privacy reviewer; no genuine student or patient records.

## Why PollicinoNet fits
Store-and-forward carries exact representation hash, model/cut version and authorized evaluation policy; a delayed review returns bounded leakage and utility measurements. No intermediate vector is assumed anonymous.

## Possible bearers (frozen LoRa PHY/MAC)
LoRa: test descriptor/decision only; BLE/Wi-Fi: synthetic embeddings and evaluation packs; Internet: optional public model baseline; physical SSD: bulk.

## What can be tested immediately in software (proposed, not executed)
Synthetic planted-label samples, raw-versus-feature-reduced-versus-quantized/noisy representations. Run permitted linkage and attribute-inference baselines within a closed lab; record attack-vs-baseline, usefulness, bytes, model compatibility and delayed-policy behavior. A failed attack is no proof of anonymity.

## Physical hardware and required measurements
4–6 LoRa boards plus weak computer and workstation; transfer only synthetic samples, measure real bytes/compute/time and exact version binding; privacy claims remain bounded to controlled dataset.

## Privacy, security and implementation difficulty
HIGH. No PII, no school-student profiling, controlled sandbox, encryption, short retention and no publication of real private activations or reusable personal-data attack artifacts.

## Difference from existing use cases
UC-164 transports split inference, UC-111 local redaction and UC-189 radio *metadata* exposure. UC-199 inspects the *semantic leakage of learned intermediate features*.

## Context and constraints
Reference DTN store-carry-forward model: https://www.rfc-editor.org/rfc/rfc9171 . Before physical radio trials verify local frequency, sub-band, power, antenna and airtime limits for the exact device. No simulated coverage/PDR/energy figures are real measurements.

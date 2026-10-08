# POLLICINO instructions for AI coding agents

This file defines the operating rules for AI coding agents working in this repository.
It applies to the whole repository unless a more specific AGENTS.md exists deeper in the tree.

POLLICINO is both a research project and a teaching project. Work must therefore remain:
small, reproducible, evidence-driven, understandable to contributors, and explainable to motivated students.

## 1. Always orient before changing anything

Before modifying code, documentation, experiments, issues, ADRs, or GitHub state:

1. Read this AGENTS.md.
2. Read the top-level README.md.
3. Read the current research map when present (planned: docs/research/INDEX.md).
4. Identify the active track:
   - Learned Compression
   - PollicinoNet
   - Course
   - Documentation / shared infrastructure
5. Read only the documents relevant to the current task.
6. Verify:
   - current branch;
   - current HEAD;
   - clean or dirty worktree;
   - expected predecessor or baseline commit;
   - linked approved issue, when the task is issue-driven.
7. Distinguish clearly between:
   - CURRENT CONTRACT: what is valid today;
   - HISTORICAL EVIDENCE: what happened in a past experiment;
   - ROADMAP / FUTURE: what may be investigated later.

Do not read every Markdown file blindly. Large context can mix current contracts, historical evidence, and speculative future work.

A future-roadmap document does not authorize implementation.
A historical experiment report must not be rewritten to match current understanding.

If branch, baseline, or repository state differs from the expected state, stop and report it instead of silently repairing history.

## 2. Work in small, verifiable steps

- Proceed in small, testable, reviewable steps.
- Discuss strategy, semantics, assumptions, and trade-offs before non-trivial implementation.
- Modify code or documentation only after explicit agreement on the step when the change is not already fully authorized by the current task.
- Do not anticipate large refactors.
- Do not perform unrelated cleanup while working on another task.
- Touch only files that are necessary for the approved step.
- Every changed line should be explainable by the current request, a test, a bug, an experiment, or a required documentation update.
- Prefer the minimum mechanism that can answer the current question.
- If a useful improvement is discovered outside scope, report it as a possible future task; do not implement it automatically.

After every gate, substantial child issue, experiment, or important architectural decision:
- stop;
- explain the result;
- propose the next question;
- do not automatically begin the next piece of work.

## 3. Functional explanation is mandatory at the end of work

When a task is completed, do not report only files, commits, SHAs, or test counts.

Always explain in simple, clear language:
- what worked before;
- what changed;
- what the system can do now;
- what limitations remain;
- what evidence demonstrates the result.

The explanation should be understandable to a motivated student who has not followed the implementation step by step.

Technical metadata is still required when relevant, but it must not replace the functional explanation.

## 4. Maintainer approval is required for issues

Issue creation and material issue mutation require explicit maintainer approval.

An agent MUST NOT create, open, edit, close, split, rename, or materially rewrite a GitHub issue unless the issue has first been discussed with Antonio and the proposed text has been explicitly approved.

At minimum, before creating an issue:
1. discuss the purpose;
2. present the complete proposed issue text;
3. receive explicit approval;
4. only then create it.

Silence, a roadmap entry, an experiment recommendation, a parent issue, or a previous similar issue does not count as approval.

A parent issue does not authorize automatic creation of child issues.
Every child issue requires its own discussion and approved text.

Agents may always propose draft issue text in chat or documentation without creating the issue.

## 5. Maintainer approval is required for ADRs

A new ADR or a material rewrite of an existing ADR must be discussed with Antonio first.

Before creating or materially changing an ADR:
1. explain the architectural decision;
2. show the proposed ADR text or a sufficiently complete draft;
3. receive explicit approval;
4. only then persist the ADR.

Do not create an ADR for every experiment.
Create an ADR only when evidence leads to a durable architectural decision that future work should preserve.

## 6. GitHub coordination model

For non-trivial work, prefer this conceptual trace:

Research track or milestone
  -> parent issue
     -> approved child issue / experiment issue
        -> dedicated branch
           -> commits / preregistration / implementation
              -> result report
                 -> ADR only when a durable decision emerges

GitHub Milestones are optional and should be used only when they add real coordination value.

Parent issues should explain context, not merely list paths.

A good parent issue should include:
- goal;
- why the work matters now;
- primary roadmap or research-map reference;
- short explanations of linked documents;
- current scope;
- out-of-scope items;
- implementation / experiment traceability.

For substantial work, maintain an Implementation traceability table linking steps to:
- status;
- child issues;
- branches;
- commits;
- pull requests when used;
- reports;
- ADRs when applicable.

Keep summary checklists and traceability tables synchronized.

## 7. Bidirectional traceability

Important work must be navigable in both directions.

When applicable, link:
- parent issue <-> child issue;
- issue <-> branch;
- issue <-> PR;
- issue <-> report;
- report <-> issue;
- ADR <-> supporting experiments;
- experiment report <-> preregistration / execution / result commits.

For scientific experiments, preserve at least:
- predecessor or baseline;
- branch;
- preregistration SHA when used;
- frozen execution or implementation SHA;
- results SHA;
- final report / documentation SHA.

Do not leave an important decision or result isolated in chat.

## 8. Labels

Use labels only when they help filtering, understanding, or ordering work.

Preferred area families:
- area:learned-compression
- area:pollicinonet
- area:docs
- area:course
- area:shared
- add area:hardware or area:benchmark only when they become operationally useful

Preferred kind families:
- kind:experiment
- kind:architecture
- kind:docs
- kind:bug
- kind:test
- kind:audit
- kind:engineering

Preferred status families:
- status:needs-discussion
- status:needs-approval
- status:ready
- status:blocked
- status:needs-docs

Optional priority:
- priority:p0 for critical integrity / correctness blockers;
- priority:p1 for active next work;
- priority:p2 for important but non-immediate work.

Every issue should normally have at least one area and one kind.
Status and priority are optional and should represent a real operational condition.

Do not create decorative labels.
If a needed label does not exist, propose it; do not create repository taxonomy silently.

## 9. Branch discipline

Use a dedicated branch for non-trivial work.

Do not perform scientific experiments, architectural changes, or substantial feature work directly on main.

Branch names should identify the work clearly, for example:
- agent/train-001-step-scaling
- pollicino/px19-pn-b8-real-lan
- docs/research-map-audit

The branch should be linked from the approved issue when an issue exists.

Do not merge to main without explicit maintainer approval.

## 10. Commit discipline

Commits should be small and single-purpose.

Use English for commit subjects and bodies.

A non-trivial commit should explain:
- what changed;
- why it changed;
- important functional, scientific, or architectural consequences.

When relevant, identify the experiment and evidence role, for example:
- preregistration;
- implementation / frozen harness;
- scientific execution;
- persisted results;
- documentation / closure.

Prefer a final section:

Modified files:
- path/one
- path/two

Do not commit unrelated local files, generated logs, secrets, or experiments outside the current task.

For research work, keep logically distinct stages in separate commits when practical:
- preregistration;
- implementation / frozen harness;
- execution-support fixes;
- persisted results;
- interpretation / closure.

## 11. Published scientific history is immutable

Once scientific evidence has been published, do not rewrite history.

After a preregistration, scientific execution, persisted result, or closure has become part of the evidence:
- no force-push;
- no destructive rebase;
- no retroactive preregistration edits;
- no silent replacement of results;
- no rewriting old reports to hide a discovered mistake.

If an error is discovered:
1. record the problem;
2. classify it;
3. add a corrective commit / erratum;
4. rerun only when scientifically justified;
5. preserve the original historical evidence and explain its validity or invalidity.

Historical discrepancies are evidence and must remain visible.

## 12. Push policy

Supervised operation is the default.

If the current approved task explicitly authorizes commit and push, the agent may perform the authorized pushes without asking again at every mechanical step.

If push was not explicitly authorized, stop before pushing and ask for approval.

Never force-push scientific history.

Never merge to main without explicit maintainer approval.

## 13. Pull requests and review

Use pull requests when they add review and integration value.

For significant changes to:
- architecture;
- public contracts;
- persistent formats;
- codec semantics;
- network protocol boundaries;
- shared scientific harnesses;
- core reusable infrastructure;

prefer:
1. draft PR;
2. review;
3. fixes;
4. a second consecutive clean review;
5. ready/merge decision by the maintainer.

Two clean reviews are not required for trivial documentation fixes, typo-only changes, or small metadata corrections unless requested.

Merge is never automatic.

When a review finding is fixed, explain:
- the risk;
- what changed;
- why the fix closes the finding;
- what test or contract prevents regression.

## 14. Documentation is part of the implementation

Documentation must be detailed, didactic, and contributor-friendly.

Write so that motivated secondary-school students can follow the reasoning without already knowing advanced networking, machine learning, information theory, or distributed systems.

Do not simplify away technical truth.
Instead, introduce concepts progressively.

Whenever a technical concept is first meaningfully used, prefer this structure:
1. intuitive explanation;
2. technical definition;
3. concrete example;
4. why it matters in POLLICINO;
5. diagram when it meaningfully reduces cognitive load.

Important PollicinoNet concepts such as datagram, socket, MTU, fragmentation, reconciliation, store-and-forward, durable state, backpressure, connected UDP, and path MTU must not be assumed knowledge in student-oriented or contributor-orientation documents.

A glossary is useful for recurring terms, but it does not replace an explanation at first meaningful use.

## 15. Guided code reading

Documentation about code should not be only an API list.

Prefer guided flows such as:

Learned Compression:
input bytes
  -> predictor
  -> probabilities
  -> integer CDF
  -> range coder
  -> exact decoder

PollicinoNet:
application
  -> D2 / D3 / D4
  -> B2 family
  -> B4
  -> transport adapter
  -> peer

Explain:
- entry points;
- important helpers;
- responsibilities;
- data structures;
- state transitions;
- ownership;
- persistence;
- reasons for the design.

## 16. Diagrams

Use diagrams when they make a complex flow substantially easier to understand.

Prefer:
1. Mermaid or simple ASCII inside Markdown;
2. static images when diagrams need richer visual explanation;
3. animation only when motion / sequencing adds real educational value.

Good candidates for diagrams:
- multi-layer architecture;
- peer exchanges;
- encoder/decoder flow;
- routing decisions;
- lifecycle;
- volatile versus durable state;
- failure/recovery sequences.

Do not add decorative diagrams.

## 17. Documentation impact check

Every non-trivial code or contract change requires a documentation-impact check.

If behavior or a contract changes:
- inspect the authoritative document that describes it;
- update it in the same task when necessary.

If no documentation change is needed, be able to explain briefly why.

A non-trivial change should leave an orientation trace through at least one of:
- test;
- experiment report;
- architecture documentation;
- API / protocol contract;
- diagram;
- ADR;
- approved issue traceability.

## 18. Keep chat knowledge from disappearing

If a discussion with Antonio or students reveals that an architectural choice, code path, or concept is unclear:
- check the relevant documentation before closing the task;
- if the explanation is missing or too weak, add a didactic explanation to the appropriate stable document after approval where required;
- if the explanation already exists, point to the file and section rather than duplicating it unnecessarily.

If an important design explanation exists only in chat, move its stable conclusion into the appropriate repository document.

## 19. Verification criteria must be explicit

Every technical step should define:
- what changes;
- how the result is verified;
- what counts as failure.

Do not continue blindly after a prerequisite verification fails.

If a prerequisite test, provenance check, baseline reproduction, or firewall check fails:
- stop;
- understand and classify the failure;
- repair only within approved scope;
- rerun affected evidence when necessary.

## 20. Test type must match the contract

Do not confuse types of evidence.

Use:
- unit tests for local functions and invariants;
- focused integration tests for module boundaries;
- end-to-end tests for observable system behavior;
- scientific experiments for research hypotheses.

A green test suite proves technical correctness relative to tested contracts.
It does not prove that a scientific hypothesis succeeded.

Reports must distinguish:
- technical success / failure;
- scientific success / failure.

## 21. Scientific preregistration

For research experiments where tuning or fresh evaluation data could bias conclusions, preregister before accessing the decisive data.

Freeze as applicable:
- hypothesis;
- independent variable;
- frozen components;
- dataset / provenance;
- candidate grid;
- selection rule;
- success threshold;
- failure taxonomy;
- compute / byte budget;
- holdout rules.

Commit the preregistration before scientific execution.

Do not change the registered rule after observing the fresh holdout.

If a preregistration assumption is wrong, stop and document the correction. Preserve the old record.

## 22. Holdout firewall

A fresh holdout must not become development data inside the same experiment.

Do not:
- inspect fresh metrics;
- tune;
- rerun with a better threshold;
- call the second attempt the same untouched holdout result.

If the holdout is contaminated:
- invalidate it;
- document why;
- create a new preregistration;
- select genuinely fresh evidence.

## 23. Negative results are first-class results

Do not rescue a failed hypothesis by silently changing the experiment.

A technically correct experiment may close with a failed scientific hypothesis.

Preserve and explain negative results.

Examples of valid conclusions include:
- selector signal insufficient;
- admission delay negates signal gain;
- compact method loses in a high-difference regime;
- generalization fails out of domain.

A negative result is knowledge and may legitimately close the issue.

## 24. Evidence drives the next question

The next experiment should follow from evidence, not from the most interesting implementation idea.

After an experiment:
1. close the current question;
2. explain what was learned;
3. identify the smallest remaining uncertainty;
4. propose, but do not automatically create, the next issue / experiment.

Do not automatically escalate:
- model size;
- context;
- neural budget;
- protocol complexity;
- reliability mechanisms;
- security mechanisms;
- abstraction layers;

just to make a result positive.

## 25. Architecture must pay rent

Every architectural abstraction must justify its cost.

New adapters, routers, registries, capability layers, caches, selectors, expert managers, protocol layers, persistent state, or configuration surfaces must buy at least one real benefit:
- clarity;
- testability;
- separation of responsibilities;
- necessary extensibility;
- reliability;
- security;
- performance;
- operability;
- scientific reproducibility.

Measure or account for cost when possible:
- CPU;
- memory;
- bytes transmitted;
- persistent state;
- training compute;
- inference compute;
- complexity;
- operational burden.

Future vision may influence boundaries, but it does not authorize implementation today.

Future-compatible does not mean future-preimplemented.

Do not promote a local mechanism to a generic architecture after a single example.
Generalize only when multiple pieces of evidence justify it.

## 26. Separate refactors from experiments

If a scientific experiment requires a substantial refactor:
- isolate the refactor when practical;
- test and document the refactor separately;
- freeze the infrastructure before measuring the scientific variable.

Avoid changing trainer, data loader, checkpoint format, model, and research variable in one experiment unless the experiment explicitly studies those changes.

## 27. Review dimensions

Before considering substantial work complete, review at least:

Functional correctness
- Does the implementation match the approved functional goal?

Contract clarity
- Are responsibilities, lifecycle, ownership, persistence, error semantics, and public boundaries still clear?

Test fitness
- Is the right kind of test protecting the right contract?

Simplicity
- Did the task add unnecessary classes, layers, configuration, state, or branches?

Failure modes
- Crash, restart, timeout, corruption, partial state, duplicate, loss, unexpected input, boundary conditions.

Reproducibility
- Can a contributor reconstruct commit, branch, dataset, hashes, seeds, runtime, configuration, command, and artifact when required?

Documentation coherence
- Do code, tests, report, research map, issue, and ADR tell the same story?

Scientific interpretation
- Are technical correctness and scientific outcome clearly separated?

## 28. Issue closure

An issue should close only when its result is traceable.

When applicable, closure should include:
- branch;
- important commits;
- tests / verification;
- report or updated docs;
- final classification;
- parent issue link;
- preregistration / execution / result SHAs for experiments.

Before closing an issue, leave a final plain-language comment explaining:
- what was done;
- functional result;
- what was learned;
- remaining limits;
- important links;
- whether a new question emerged.

Do not close with only "Done in abc123".

A negative experiment may close an issue if the research question has been answered.

## 29. Parent issue closure

Do not close a parent issue merely because the currently known child issues are closed.

Check:
- was the original goal achieved?
- are contracts and documentation aligned?
- is deferred work stated?
- are new questions separated correctly?

If work remains outside current scope, say so explicitly.

## 30. Next issues are not automatic

A report may recommend a next experiment.
That recommendation is not authorization to create an issue.

The agent may:
- explain the next question;
- draft the issue text;
- discuss alternatives.

Creation requires explicit maintainer approval of the issue text.

## 31. Document roles

Keep document responsibilities separate.

Top-level README.md
- quick orientation;
- what POLLICINO is;
- major tracks;
- headline results;
- current high-level status;
- where to read next.

Research Map (planned docs/research/INDEX.md)
- authoritative current map of the research;
- how tracks relate;
- what is established;
- experiment families;
- current open questions;
- reading paths.

ROADMAP.md
- future direction;
- done / current / next / future distinction;
- no stale TODOs for already completed work.

Issue
- concrete work and coordination.

Experiment report
- evidence: question, setup, method, result, classification, limits, learned outcome.

ADR
- durable architectural decision: context, decision, evidence, consequences, alternatives, status.

Theory / glossary documents
- explanation of concepts.

Do not make every document repeat the same detailed metrics.

## 32. One authoritative source for current state

The planned Research Map should become the authoritative current-state document for research.

README should summarize it.
ROADMAP should look forward.
Experiment reports should remain historical evidence.

Until the Research Map exists, agents must be explicit about which branch/report provides the newest evidence.

## 33. Preserve history, update interpretation

Do not rewrite historical reports to make them agree with current understanding.

Instead:
- keep historical report unchanged;
- update current Research Map / docs with what is now believed;
- link back to the evidence.

Each important fact should have a primary source.
Other documents should summarize and link instead of duplicating all details.

## 34. Data minimization and secrets

Collect, store, and publish only information necessary to reproduce or understand the result.

Do not commit:
- passwords;
- API keys;
- private keys;
- access tokens;
- cookies;
- secrets;
- unnecessary personal data;
- generated logs containing sensitive information.

Prefer environment metadata such as:
- OS;
- architecture;
- Python;
- framework versions;
- commit;
- device;
when relevant.

Run secret scanning for important closures when available.

## 35. Dataset provenance and licensing

For every research dataset, record as applicable:
- origin;
- project/repository;
- version/tag/commit;
- file path;
- license / usage conditions where relevant;
- size;
- SHA-256;
- Git blob/object when available;
- role: train / validation / test / diagnostic.

A public URL is not sufficient proof of reproducibility.

Public does not mean immutable.

Prefer immutable provenance plus hashes and manifests.

## 36. Dependencies

Add dependencies only when justified.

For a new dependency, consider:
- why it is needed;
- what incorrect or excessive custom implementation it avoids;
- maintenance status;
- weight / runtime cost;
- security surface;
- license.

Do not add a heavy framework for a small local task.

## 37. Security and reliability claims require evidence

Do not claim that a component or protocol is:
- secure;
- authenticated;
- private;
- anonymous;
- reliable;
- tamper-proof;
unless a dedicated contract and evidence support the claim.

Keep these dimensions separate:
- compression;
- corruption detection;
- authentication;
- encryption;
- identity;
- privacy;
- transport delivery;
- reliability.

For example:
- B4 CRC/digest can detect corruption;
- that is not authentication.
- Connected UDP source filtering constrains the socket peer;
- that is not peer identity or cryptographic trust.

## 38. Track isolation

Learned Compression experiments should not modify PollicinoNet files unless explicitly required and approved.

PollicinoNet experiments should not modify Learned Compression research unless explicitly required and approved.

Course material should consume consolidated results; do not edit the course opportunistically during an experiment unless the task explicitly includes it.

When a task crosses tracks, explain why before modifying shared boundaries.

## 39. Final checklist for agents

Before starting:
- [ ] Read AGENTS.md.
- [ ] Identify the track.
- [ ] Verify branch / HEAD / worktree.
- [ ] Verify approved issue and baseline when applicable.
- [ ] Read only relevant current docs and supporting historical evidence.
- [ ] State scope and out-of-scope work.

Before changing:
- [ ] Explain non-trivial assumptions and trade-offs.
- [ ] Confirm the step is authorized.
- [ ] Define how success and failure are verified.
- [ ] Check whether documentation / ADR / issue approval is required.

Before committing:
- [ ] Run relevant tests / validations.
- [ ] Perform documentation-impact check.
- [ ] Keep commit single-purpose.
- [ ] Exclude unrelated files and secrets.
- [ ] Preserve scientific history.

Before closing:
- [ ] Verify functional behavior.
- [ ] Verify scientific result separately when applicable.
- [ ] Verify reproducibility metadata.
- [ ] Update or link appropriate stable docs.
- [ ] Explain the result in simple functional language.
- [ ] State remaining limits.
- [ ] Propose, but do not automatically start or create, the next task.

## 40. Core principle

POLLICINO should remain:

small enough to understand,
rigorous enough to reproduce,
modular enough to extend,
honest enough to preserve negative results,
and clear enough that students and external contributors can learn from it.

Do not optimize only for code completion.
Optimize for understanding, evidence, traceability, and durable knowledge.

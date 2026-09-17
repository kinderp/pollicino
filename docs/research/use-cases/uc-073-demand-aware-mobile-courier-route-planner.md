# UC-073 — Demand-Aware Mobile Courier Route Planner

## Idea

Let a mobile PollicinoNet courier decide **where to go next** using compact information about pending needs, backlog urgency, cache availability and expected contact opportunities.

UC-005 establishes the generic mobile gateway/data-mule role. UC-045 decides **what to collect first once a short contact already exists**. UC-073 asks a different question:

> if the courier has several possible next checkpoints, which visit is currently most useful?

The first courier should be a walking student or teacher on a controlled route. Bicycle, car or UAV variants belong only to later experiments after the routing logic works and after the relevant safety/legal constraints are handled.

## Problem solved

A fixed route is simple but can waste scarce mobility.

Example:

- node A has a nearly full sensor buffer;
- node B has one urgent pending `ContentNeed`;
- node C has no urgent work today;
- a school cache holds the object requested by B;
- the courier can visit only two of the three nodes before returning.

A static `A -> B -> C` tour may be much worse than a route that reacts to current queue pressure, deadlines and expected future contacts.

The route planner must not assume perfect knowledge. Backlog summaries can be stale, contacts may fail and a student may not follow an exact trajectory.

## Actors / nodes

- fixed sensor/cache/service nodes;
- one or more walking student/teacher couriers;
- optional school sink/server;
- optional scheduled-mobility information from UC-025;
- optional privacy-safe contact statistics from UC-008;
- optional UC-045 harvester deciding what to transfer once a visit occurs;
- later, a vehicle or UAV under separate operational constraints.

## Why PollicinoNet fits

The route decision can be driven by **small control summaries** rather than by moving the payload itself.

- **DISCOVERY:** backlog pressure, pending need count, urgent-class hint, service/cache availability, coarse rendezvous checkpoint;
- **EXACT:** queue-summary version, requested object IDs, deadlines/expiry, route-plan ID and visited-checkpoint receipts;
- **SEMANTIC:** labels such as `urgent-sensor-backlog`, `course-pack-needed`, `repair-needed`, used only for ranking and never as authoritative object identity.

PollicinoNet is useful because the courier can carry both data and the next routing state between disconnected islands. The plan may be recomputed opportunistically whenever fresh information arrives.

Nothing changes the frozen LoRa PHY.

## Possible bearers

- **LoRa:** compact backlog/need summaries, checkpoint availability, route-plan digest, visit acknowledgements and replanning triggers;
- **BLE:** nearby inventory exchange and route-plan handoff;
- **Wi-Fi/LAN:** bulk payload transfer during a selected stop;
- **Internet:** optional authoritative data or map retrieval when available;
- **physical transport:** the person/device itself realizes the chosen route and carries stored objects between contacts.

## What we can test now in software

Extend the existing contact/mobility simulator with a controllable courier and several candidate checkpoints.

Compare simple routing policies before trying sophisticated optimization:

- fixed cyclic route;
- nearest-next checkpoint;
- highest backlog pressure;
- earliest deadline/expiry;
- highest expected value per estimated travel/contact cost;
- fairness-constrained routing so one remote node is not starved;
- contact-history-aware routing using privacy-safe UC-008 statistics;
- two-stage planning: UC-073 chooses **where to go**, UC-045 chooses **what to transfer there**.

Inject realistic uncertainty:

- stale backlog summaries;
- a checkpoint that becomes unavailable;
- a contact shorter than expected;
- a route segment that cannot be used;
- one urgent request appearing after the courier has departed;
- conflicting summaries from different relays;
- limited courier storage/battery/time budget;
- multiple couriers that should avoid needless duplication.

Useful metrics include:

- completed high-priority objects;
- deadline/expiry misses;
- mean and tail data age;
- queue overflow avoided;
- travel/checkpoint count;
- fairness across nodes;
- wasted visits caused by stale information;
- improvement over the same fixed-route baseline on the same trace.

A key invariant is:

> software planning may recommend a route, but only measured encounters establish what the physical network actually delivered.

## What requires real hardware

First field stage:

- 4–6 fixed PollicinoNet nodes with deliberately different backlogs/needs;
- one student/teacher courier;
- 3 or more controlled checkpoints;
- at least two alternative safe walking routes;
- repeat the same experiment with a fixed route and one demand-aware policy;
- measure actual contact duration, completed transfers, packet delivery and route/visit timing.

Only later:

- bicycle or vehicle experiments on safe/legal routes;
- UAV experiments only with applicable flight permissions and independent safety planning.

Do not infer route superiority from simulator travel times if the real radio/contact windows have not been measured.

## Messina teaching scenario

Create controlled teaching islands representing coarse zones such as `school/Messina`, `Villafranca`, `Rometta/Venetico` and `Spadafora` without recording home addresses.

Several nodes accumulate synthetic workloads:

- one sensor backlog close to overflow;
- one pending Raiatea/course-pack request;
- one routine backup chunk request;
- one node with nothing urgent.

A student courier receives only compact summaries and chooses the next controlled checkpoint. At each stop the richer bearer transfers the selected payload, while LoRa carries route/control state.

A later exercise can replay the exact measured UC-008 contact data and ask whether the route policy learned from historical contacts still behaves sensibly when one expected contact fails.

## Privacy / security

Route planning can easily become student tracking if designed badly.

- use named/coarse checkpoints instead of home coordinates;
- do not build a continuous personal mobility history;
- keep UC-008 encounter statistics pseudonymous and aggregated;
- authenticate backlog/priority summaries so a malicious node cannot always claim maximum urgency;
- rate-limit and quota high-priority requests;
- avoid exposing sensitive content names in public route advertisements;
- treat route recommendations as advisory to a human participant, never as an instruction that overrides safety or personal choice;
- for minors, keep experiments inside supervised, pre-approved routes and synthetic workloads.

## Difficulty

**High.** The first heuristic is easy to implement, but meaningful evaluation requires combining uncertain mobility, stale state, queue pressure and real contact measurements without turning the experiment into location tracking.

## Why this is distinct from UC-005 and UC-045

- **UC-005:** can a moving gateway bridge disconnected nodes at all?
- **UC-045:** once a contact exists and not everything fits, what data should be collected first?
- **UC-073:** before the next contact exists, **which checkpoint should the courier visit next?**

Together they form a clean hierarchy: `route choice -> encounter scheduling -> exact transfer`.

## Research signal

Recent 2026 work continues to treat mobile-collector path planning and resource-constrained data collection as active problems. One study proposes intent-driven path planning for mobile data collectors with objectives such as latency, energy balance and coverage; another models UAV-assisted IoT collection as a multi-objective scheduling problem balancing data value and quantity under resource limits. PollicinoNet should start with simple walking routes and its own measured contact traces rather than importing their performance claims.

References:

- https://onlinelibrary.wiley.com/doi/10.1002/itl2.70285
- https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/wss2.70024

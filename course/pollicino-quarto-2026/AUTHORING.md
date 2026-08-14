# POLLICINO course authoring contract

This file defines how the school track and the scientific track stay synchronized.

## Core rule

A lesson is authored **once conceptually and twice editorially**.

For every lesson we maintain:

1. a student handout in `handouts/`;
2. a teacher/scientific note in `materials/`;
3. a TheBitLab activity descriptor in `activities/` when the lesson includes a tracked activity.

The two theory documents must share the same conceptual target. The teacher version may go deeper, but it must not silently change notation, assumptions or conclusions.

## Student handout contract

Each student handout should contain, where appropriate:

- a guiding question;
- observable learning objectives;
- intuitive explanation before formalism;
- one or more worked examples;
- a small Python or data experiment;
- exercises or guided questions;
- an exit ticket;
- a bridge to the next lesson.

Mathematics is introduced when it answers a concrete computing question.

## Teacher/scientific material contract

Each teacher material should contain, where appropriate:

- the formal definition or derivation;
- notation used in the research track;
- the connection to the final POLLICINO architecture;
- distinctions and caveats that are intentionally simplified for students;
- common misconceptions;
- suggested classroom strategy;
- solutions or expected answers;
- a bridge to PyTorch/MLX or the next scientific concept;
- references to papers/books when the lesson reaches research-level material.

## UDA design

The `bundle.json` unit is the UDA boundary. Stable IDs use:

```text
uda-NN-topic
```

Activities additionally declare the same ID in:

```json
{
  "contesto": {
    "uda": "uda-NN-topic"
  }
}
```

This avoids a second, incompatible UDA representation.

## Synchronization checklist

Before considering a lesson complete:

- [ ] student and teacher versions target the same concept;
- [ ] notation agrees across both versions;
- [ ] examples do not contradict the scientific treatment;
- [ ] the activity points to the correct UDA;
- [ ] all paths referenced by `bundle.json` exist inside the bundle;
- [ ] lossless/reproducibility claims are testable;
- [ ] the teacher version identifies simplifications made for the classroom.

## Progression rule

We do not introduce a framework abstraction before its conceptual predecessor.

For example:

```text
frequency -> probability -> information -> entropy
-> n-gram prediction -> neural prediction -> attention
-> Transformer -> cross-entropy training -> entropy coding
```

PyTorch and MLX appear after the students and teacher have already seen the mathematical object they implement.

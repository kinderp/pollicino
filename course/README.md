# POLLICINO — Course Track

**Target:** fourth-year secondary-school computer-science students.

The course is built around one question that grows with the students:

> *How can we send fewer bits and still recover exactly the same file?*

The story of Pollicino supplies the metaphor: the goal is not to leave no trace, but to leave the **smallest useful trail**.

## Authoritative 2cornot2c bundle

The school-year course is maintained as a self-contained TheBitLab / `2cornot2c` bundle in:

```text
course/pollicino-quarto-2026/
```

Its `bundle.json` is the machine-readable course manifest. Each populated UDA keeps three synchronized views:

```text
activities/  -> TheBitLab activity metadata and metrics
handouts/    -> student-facing theory, examples and exercises
materials/   -> teacher/scientific theory, derivations and teaching notes
```

See [`pollicino-quarto-2026/AUTHORING.md`](pollicino-quarto-2026/AUTHORING.md) for the synchronization rules.

## Course sequence

1. **Files are bits** — bytes, hexadecimal representation, file size.
2. **Can an hash contain a file?** — SHA, collisions, pigeonhole principle.
3. **Find repetition** — RLE and the first compressor.
4. **Give short codes to common things** — Huffman coding.
5. **Probability is prediction** — frequency tables and next-symbol guesses.
6. **How surprising is a byte?** — `-log2(p)` and Shannon entropy.
7. **Context helps** — bigrams, n-grams and Markov models.
8. **A neuron from scratch** — weighted sums and an error function.
9. **Learning** — gradient descent and why weights change.
10. **Vectors and embeddings** — representing symbols numerically.
11. **Attention** — deciding which previous symbols matter.
12. **A tiny Transformer** — causal next-byte prediction.
13. **Training an LLM-like model** — dataset, batches, loss, validation, overfitting.
14. **Cross-entropy becomes bits** — prediction quality becomes compression cost.
15. **Arithmetic/range coding** — turn probabilities into a real lossless stream.
16. **POLLICINO Challenge** — beat the baselines under size, memory and time constraints.

## Classroom principle

Every mathematical idea must answer a concrete programming question. Every major abstraction is first implemented in a simplified form before using the framework implementation.

The scientific implementation lives in `src/`; the course bundle translates the same concepts into classroom-ready lessons without changing the underlying mathematics.

# POLLICINO Experiments

Each experiment gets an immutable directory such as:

```text
experiments/exp0001_uniform/
experiments/exp0002_byte_frequency/
experiments/exp0003_bigram/
experiments/exp0004_tiny_transformer/
```

A directory should contain configuration, dataset manifest/hash, environment metadata, metrics and a short conclusion. Large datasets and checkpoints are not committed directly.

The experiment number identifies the protocol, not merely one training run. Repeated seeds/hardware runs should be nested or referenced consistently rather than silently overwriting results.

# UDA 6 — dal modello ai bit reali

1. intervalli arithmetic/range coding; 2. codec `.pol` deterministico con CDF intere e SHA-256; 3. benchmark reale con overhead; 4. ablation e riproducibilità; 5. POLLICINO Challenge.

Un risultato non è valido se `decode(encode(x)) != x`. Nei file `.pol` il controllo finale usa anche SHA-256.

`shared-model` trasporta il fingerprint ma non i pesi: decoder ed encoder devono rigenerare la stessa CDF intera a ogni posizione. La parità PyTorch/MLX cross-device resta una domanda di ricerca.

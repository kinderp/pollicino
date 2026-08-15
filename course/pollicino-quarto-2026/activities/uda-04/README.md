# UDA 4 — Laboratori Transformer da zero

Questa UDA costruisce un Transformer byte-level senza framework ML.

1. `l01` — sequenze, posizione e matrice causale;
2. `l02` — Q/K/V e scaled dot-product attention;
3. `l03` — causal mask e test esplicito contro il future leakage;
4. `l04` — multi-head attention, RMSNorm, residual e feed-forward;
5. `l05` — Tiny Byte Transformer completo in forward pass.

La UDA 4 **non addestra ancora il Transformer**: il training completo viene spostato alla UDA 5, dove gli stessi oggetti saranno implementati in PyTorch e MLX. Qui l'obiettivo è capire l'architettura e verificarne la causalità.

Tutti i laboratori usano la sola libreria standard Python.

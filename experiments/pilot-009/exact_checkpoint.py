from __future__ import annotations

import hashlib
import io
import os
import urllib.error
import urllib.request
import zipfile

import torch

from pollicino.backends.pytorch.model import ByteTransformer
from pollicino.model_spec import ModelSpec

ARTIFACT_ID = 9243314314
ARTIFACT_DIGEST = "72a2f5c06088401f64d06f2aaead014a55015715b5dc1abb1b787567750d11b5"
EXPECTED_MODEL_FINGERPRINT = "354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117"
REPOSITORY = "kinderp/pollicino"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download_artifact(token: str) -> bytes:
    url = f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{ARTIFACT_ID}/zip"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "POLLICINO-PILOT-009/1.0",
        },
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(request, timeout=120)
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers.get("Location")
        if not location:
            raise RuntimeError("GitHub artifact redirect had no Location header") from exc
    else:
        raise RuntimeError("GitHub artifact download unexpectedly returned without redirect")

    storage_request = urllib.request.Request(
        location,
        headers={"User-Agent": "POLLICINO-PILOT-009/1.0"},
    )
    with urllib.request.urlopen(storage_request, timeout=120) as response:
        return response.read()


def load_exact_checkpoint():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required to retrieve the frozen PILOT-003 artifact")

    archive_bytes = _download_artifact(token)
    archive_sha = sha256(archive_bytes)
    if archive_sha != ARTIFACT_DIGEST:
        raise RuntimeError(f"PILOT-003 artifact digest mismatch: {archive_sha}")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = archive.namelist()
        if "winner.pt" not in names:
            raise RuntimeError(f"PILOT-003 artifact has no winner.pt: {names}")
        checkpoint_bytes = archive.read("winner.pt")

    state = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    spec = ModelSpec(
        vocab_size=256,
        context_length=32,
        d_model=80,
        n_heads=4,
        n_layers=2,
        d_ff=160,
        layer_norm_eps=1e-5,
    )
    model = ByteTransformer(spec)
    model.load_state_dict(state)
    model.eval()
    return model, spec, {
        "artifact_id": ARTIFACT_ID,
        "artifact_sha256": archive_sha,
        "checkpoint_bytes": len(checkpoint_bytes),
        "checkpoint_sha256": sha256(checkpoint_bytes),
    }

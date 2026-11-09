#!/usr/bin/env python3
"""Build a reusable CRC SPECTRA candidate table from public CRC parquet data.

This script intentionally computes only prospective image/source features. It
does not load CONCH, predictions, confidences, or target-model errors.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from PIL import Image


LABEL_NAMES = {
    0: "ADI",
    1: "BACK",
    2: "DEB",
    3: "LYM",
    4: "MUC",
    5: "MUS",
    6: "NORM",
    7: "STR",
    8: "TUM",
}

HF_BASE = "https://huggingface.co/datasets/1aurent/NCT-CRC-HE/resolve/main/"
NCT_REFERENCE_SHARDS = {
    2: "data/NCT_CRC_HE_100K-00000-of-00031-9780c9afe3d80c58.parquet",
    7: "data/NCT_CRC_HE_100K-00004-of-00031-04197e7c2252e508.parquet",
    0: "data/NCT_CRC_HE_100K-00007-of-00031-7240d4f64e3ab056.parquet",
    3: "data/NCT_CRC_HE_100K-00011-of-00031-9586fd31243bcf81.parquet",
    6: "data/NCT_CRC_HE_100K-00014-of-00031-a59185824004206f.parquet",
    8: "data/NCT_CRC_HE_100K-00017-of-00031-240fc2989151d739.parquet",
    1: "data/NCT_CRC_HE_100K-00021-of-00031-e828a2a9aff921c7.parquet",
    4: "data/NCT_CRC_HE_100K-00025-of-00031-06d3e29beab848cc.parquet",
    5: "data/NCT_CRC_HE_100K-00027-of-00031-76ba1a4a6d60e4bf.parquet",
}


def rgb_to_hsv(arr: np.ndarray) -> np.ndarray:
    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    diff = mx - mn

    h = np.zeros_like(mx)
    mask = diff > 1e-8
    rmask = mask & (mx == r)
    gmask = mask & (mx == g)
    bmask = mask & (mx == b)
    h[rmask] = ((g[rmask] - b[rmask]) / diff[rmask]) % 6.0
    h[gmask] = ((b[gmask] - r[gmask]) / diff[gmask]) + 2.0
    h[bmask] = ((r[bmask] - g[bmask]) / diff[bmask]) + 4.0
    h /= 6.0

    s = np.zeros_like(mx)
    nonzero = mx > 1e-8
    s[nonzero] = diff[nonzero] / mx[nonzero]
    v = mx
    return np.stack([h, s, v], axis=-1)


def normalized_hist(values: np.ndarray, bins: int, value_range: tuple[float, float]) -> np.ndarray:
    hist, _ = np.histogram(values.reshape(-1), bins=bins, range=value_range)
    hist = hist.astype(np.float32)
    total = float(hist.sum())
    if total > 0:
        hist /= total
    return hist


def dhash64(gray: np.ndarray) -> str:
    pil = Image.fromarray(np.uint8(np.clip(gray * 255.0, 0, 255)))
    small = pil.resize((9, 8), Image.Resampling.BILINEAR)
    vals = np.asarray(small, dtype=np.int16)
    bits = vals[:, 1:] > vals[:, :-1]
    out = 0
    for bit in bits.reshape(-1):
        out = (out << 1) | int(bit)
    return f"{out:016x}"


def image_features(image: Image.Image, raw_bytes: bytes | None = None) -> dict[str, float | str]:
    img = image.convert("RGB")
    if img.size != (224, 224):
        img = img.resize((224, 224), Image.Resampling.BICUBIC)
    arr_u8 = np.asarray(img, dtype=np.uint8)
    arr = arr_u8.astype(np.float32) / 255.0
    hsv = rgb_to_hsv(arr)
    gray = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    sat = hsv[..., 1]
    value = hsv[..., 2]

    dx = np.diff(gray, axis=1)
    dy = np.diff(gray, axis=0)
    edge = np.sqrt(dx[:-1, :] ** 2 + dy[:, :-1] ** 2)

    gray_hist = normalized_hist(gray, 16, (0.0, 1.0))
    entropy = -float(np.sum(gray_hist * np.log2(gray_hist + 1e-12)))

    feats: dict[str, float | str] = {}
    if raw_bytes is None:
        raw_bytes = arr_u8.tobytes()
    feats["image_md5"] = hashlib.md5(raw_bytes).hexdigest()
    feats["dhash64"] = dhash64(gray)

    for i, name in enumerate(("r", "g", "b")):
        channel = arr[..., i]
        feats[f"{name}_mean"] = float(channel.mean())
        feats[f"{name}_std"] = float(channel.std())
        feats[f"{name}_p05"] = float(np.quantile(channel, 0.05))
        feats[f"{name}_p95"] = float(np.quantile(channel, 0.95))
    for i, name in enumerate(("h", "s", "v")):
        channel = hsv[..., i]
        feats[f"{name}_mean"] = float(channel.mean())
        feats[f"{name}_std"] = float(channel.std())
    for i, val in enumerate(normalized_hist(hsv[..., 0], 8, (0.0, 1.0))):
        feats[f"h_hist_{i:02d}"] = float(val)
    for i, val in enumerate(normalized_hist(sat, 8, (0.0, 1.0))):
        feats[f"s_hist_{i:02d}"] = float(val)
    for i, val in enumerate(normalized_hist(value, 8, (0.0, 1.0))):
        feats[f"v_hist_{i:02d}"] = float(val)
    for i, val in enumerate(gray_hist):
        feats[f"gray_hist_{i:02d}"] = float(val)

    feats["gray_mean"] = float(gray.mean())
    feats["gray_std"] = float(gray.std())
    feats["gray_entropy"] = entropy
    feats["edge_mean"] = float(edge.mean())
    feats["edge_std"] = float(edge.std())
    feats["tissue_fraction"] = float(((gray < 0.90) & (sat > 0.05)).mean())
    feats["white_fraction"] = float(((gray > 0.90) & (sat < 0.15)).mean())
    feats["dark_fraction"] = float((gray < 0.20).mean())
    feats["saturation_high_fraction"] = float((sat > 0.50).mean())
    return feats


def iter_crc_val(parquet_dir: Path):
    idx = 0
    for parquet_path in sorted(parquet_dir.glob("CRC_VAL_HE_7K-*.parquet")):
        pf = pq.ParquetFile(parquet_path)
        for rg in range(pf.num_row_groups):
            table = pf.read_row_group(rg, columns=["image", "label"])
            labels = table["label"].to_pylist()
            images = table["image"].to_pylist()
            for label, img_struct in zip(labels, images):
                raw = img_struct["bytes"]
                path = img_struct.get("path") or ""
                image = Image.open(io.BytesIO(raw))
                yield {
                    "source_split": "CRC_VAL_HE_7K",
                    "source_record_index": idx,
                    "sample_id": f"crcval_{idx:05d}",
                    "image_path": path,
                    "label": int(label),
                    "label_name": LABEL_NAMES[int(label)],
                    "image": image,
                    "raw_bytes": raw,
                }
                idx += 1


def build_crc_features(parquet_dir: Path) -> pd.DataFrame:
    rows = []
    for rec in iter_crc_val(parquet_dir):
        feats = image_features(rec["image"], rec["raw_bytes"])
        rows.append({k: v for k, v in rec.items() if k not in {"image", "raw_bytes"}} | feats)
    return pd.DataFrame(rows)


def build_nct_reference_features(n_per_label: int) -> pd.DataFrame:
    from datasets import load_dataset

    rows = []
    for label, shard in sorted(NCT_REFERENCE_SHARDS.items()):
        url = HF_BASE + shard
        ds = load_dataset("parquet", data_files=url, split="train", streaming=True)
        taken = 0
        for ex in ds:
            if int(ex["label"]) != int(label):
                continue
            image = ex["image"]
            feats = image_features(image)
            rows.append(
                {
                    "source_split": "NCT_CRC_HE_100K_reference",
                    "source_record_index": taken,
                    "sample_id": f"nctref_{LABEL_NAMES[label]}_{taken:04d}",
                    "image_path": "",
                    "label": int(label),
                    "label_name": LABEL_NAMES[int(label)],
                    "reference_shard": shard,
                }
                | feats
            )
            taken += 1
            if taken >= n_per_label:
                break
        if taken < n_per_label:
            raise RuntimeError(f"Only collected {taken} examples for label {label} from {shard}")
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet-dir", type=Path, default=Path("data_cache/parquets"))
    ap.add_argument("--out-dir", type=Path, default=Path("spectra_ready_dataset"))
    ap.add_argument("--nct-per-label", type=int, default=200)
    ap.add_argument("--force-exit", action="store_true")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    crc = build_crc_features(args.parquet_dir)
    nct = build_nct_reference_features(args.nct_per_label)
    combined = pd.concat([crc, nct], ignore_index=True)

    crc_path = args.out_dir / "crc_val_candidate_features.csv"
    nct_path = args.out_dir / "nct_reference_features.csv"
    combined_path = args.out_dir / "candidate_features.csv"
    crc.to_csv(crc_path, index=False)
    nct.to_csv(nct_path, index=False)
    combined.to_csv(combined_path, index=False)

    diagnostics = {
        "crc_val_rows": int(len(crc)),
        "nct_reference_rows": int(len(nct)),
        "nct_per_label": int(args.nct_per_label),
        "crc_val_label_counts": {LABEL_NAMES[k]: int(v) for k, v in sorted(Counter(crc["label"]).items())},
        "nct_reference_label_counts": {LABEL_NAMES[k]: int(v) for k, v in sorted(Counter(nct["label"]).items())},
        "crc_val_exact_md5_duplicates": int(crc["image_md5"].duplicated().sum()),
        "crc_val_dhash64_duplicates": int(crc["dhash64"].duplicated().sum()),
        "nct_reference_shards": {LABEL_NAMES[k]: v for k, v in sorted(NCT_REFERENCE_SHARDS.items())},
    }
    with (args.out_dir / "dataset_diagnostics.json").open("w") as f:
        json.dump(diagnostics, f, indent=2)
    print(json.dumps(diagnostics, indent=2), flush=True)
    if args.force_exit:
        os._exit(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

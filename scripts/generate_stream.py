# -*- coding: utf-8 -*-
import argparse, sys, time, hashlib
from zyntalic_core import generate_entry, load_projection

def _h64(s: str) -> int:
    return int(hashlib.blake2b(s.encode('utf-8'), digest_size=8).hexdigest(), 16)

def stream_generate(n: int, out_path: str, use_projection: bool = True, dedupe: bool = True):
    W = load_projection("models/W.npy") if use_projection else None
    seen = set()
    t0 = time.time()
    with open(out_path, "w", encoding="utf-8") as f:
        for i in range(n):
            seed = f"stream::{i}"
            e = generate_entry(seed, W=W)
            if dedupe:
                h = _h64(e["word"])
                if h in seen:
                    continue
                seen.add(h)
            anchors_str = ";".join(f"{a}:{w:.3f}" for a, w in e["anchors"])
            emb_str = ",".join(f"{v:.6f}" for v in e["embedding"])
            f.write(f"{e['word']}\t{e['meaning']}\t{e['sentence']}\t{anchors_str}\t{emb_str}\n")
            if (i+1) % 10000 == 0:
                dt = time.time() - t0
                print(f"[{i+1}/{n}] {i+1:.0f} rows in {dt:.1f}s", file=sys.stderr)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--out", default="zyntalic_words.txt")
    ap.add_argument("--no-proj", action="store_true")
    args = ap.parse_args()
    stream_generate(args.n, args.out, use_projection=not args.no_proj)
    print(f"Wrote {args.out}")

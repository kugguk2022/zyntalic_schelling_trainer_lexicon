# -*- coding: utf-8 -*-
"""
Train thin projection W mapping Base -> Anchor centroids.
Outputs: models/W.npy, models/meta.json
"""
import argparse, os, json, random, numpy as np
from collections import defaultdict
import hashlib

ANCHORS = [
    "Homer_Iliad", "Homer_Odyssey", "Plato_Republic",
    "Aristotle_Organon", "Virgil_Aeneid", "Dante_DivineComedy",
    "Shakespeare_Sonnets", "Goethe_Faust", "Cervantes_DonQuixote",
    "Milton_ParadiseLost", "Melville_MobyDick", "Darwin_OriginOfSpecies",
    "Austen_PridePrejudice", "Tolstoy_WarPeace", "Dostoevsky_BrothersKaramazov",
    "Laozi_TaoTeChing", "Sunzi_ArtOfWar", "Descartes_Meditations",
    "Bacon_NovumOrganum", "Spinoza_Ethics"
]

def det_seed(text: str) -> int:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def base_embedding(key: str, dim=300):
    rng = random.Random(det_seed(key))
    return np.array([rng.random() for _ in range(dim)], dtype=np.float32)

def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v) or 1.0; return v / n

def anchor_vec(tag: str, dim=300):
    rng = random.Random(det_seed(tag)); 
    return np.array([rng.random() for _ in range(dim)], dtype=np.float32)

def load_anchors_tsv(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): 
                continue
            parts = line.split("\t")
            if len(parts) < 2: 
                continue
            rows.append((parts[0], parts[1]))
    return rows

def split_train_test(rows, test_ratio=0.25, seed=41):
    rng = random.Random(seed)
    by_anchor = defaultdict(list)
    for a, t in rows:
        by_anchor[a].append(t)
    train, test = [], []
    for a, lst in by_anchor.items():
        rng.shuffle(lst)
        k = max(1, int(len(lst)*test_ratio))
        test.extend([(a,x) for x in lst[:k]])
        train.extend([(a,x) for x in lst[k:]])
    return train, test

def compute_centroids(pairs, dim=300):
    X, Y, names = [], [], []
    by_anchor = defaultdict(list)
    for a, txt in pairs:
        by_anchor[a].append(normalize(base_embedding(txt, dim)))
    for a in ANCHORS:
        if a in by_anchor and len(by_anchor[a]) > 0:
            X.append(np.mean(np.vstack(by_anchor[a]), axis=0))
            Y.append(normalize(anchor_vec(a, dim)))
            names.append(a)
    X = np.vstack(X) if X else np.zeros((0,dim), dtype=np.float32)
    Y = np.vstack(Y) if Y else np.zeros((0,dim), dtype=np.float32)
    return X, Y, names

def train_procrustes(X, Y):
    M = X.T @ Y
    U, _, Vt = np.linalg.svd(M, full_matrices=False)
    W = U @ Vt
    return W

def train_ridge(X, Y, lam=1e-3):
    d = X.shape[1]
    A = X.T @ X + lam*np.eye(d, dtype=np.float32)
    B = X.T @ Y
    W = np.linalg.solve(A, B)
    return W

def top1_accuracy(W, test_pairs, dim=300):
    A = np.vstack([normalize(anchor_vec(a, dim)) for a in ANCHORS])
    correct, total = 0, 0
    for a, txt in test_pairs:
        vb = normalize(base_embedding(txt, dim))
        vproj = (vb.reshape(1,-1) @ W).flatten()
        vproj = normalize(vproj)
        sims = A @ vproj
        pred = ANCHORS[int(np.argmax(sims))]
        correct += int(pred == a); total += 1
    return (correct/total) if total else 0.0, total

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--anchors", default="anchors.tsv")
    p.add_argument("--method", choices=["procrustes","ridge"], default="procrustes")
    p.add_argument("--ridge_lam", type=float, default=1e-3)
    p.add_argument("--dim", type=int, default=300)
    p.add_argument("--out_dir", default="models")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    rows = load_anchors_tsv(args.anchors)
    if not rows:
        raise SystemExit("No rows found in anchors.tsv")

    train_pairs, test_pairs = split_train_test(rows, test_ratio=0.25, seed=41)
    X, Y, names = compute_centroids(train_pairs, dim=args.dim)
    if X.shape[0] == 0:
        raise SystemExit("Not enough data to train.")

    W = train_procrustes(X, Y) if args.method=="procrustes" else train_ridge(X, Y, lam=args.ridge_lam)
    acc, total = top1_accuracy(W, test_pairs, dim=args.dim)

    np.save(os.path.join(args.out_dir, "W.npy"), W)
    meta = {"dim":args.dim, "method":args.method, "ridge_lam":args.ridge_lam if args.method=="ridge" else None,
            "anchors_in_training": names, "test_examples": total, "top1_accuracy": acc}
    with open(os.path.join(args.out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Saved {args.out_dir}/W.npy; top-1={acc:.3f} (n={total})")

if __name__ == "__main__":
    main()

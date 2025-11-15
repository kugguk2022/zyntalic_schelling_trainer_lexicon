# -*- coding: utf-8 -*-
import argparse, os, re, json
from collections import Counter, defaultdict

DEFAULT_STOPWORDS = set("""
a an and are as at be by for from has he her his i in is it its of on or she that the their them they this to was were will with you your yours our us we
am been being but not so if then there here into out up down over under again further once only same too very
""".split())

DEFAULT_MOTIF_PAIRS = [
    ("honor","shame"), ("wrath","mercy"), ("fate","choice"), ("camp","field"),
    ("home","exile"), ("cunning","force"), ("sea","shore"), ("trial","rest"),
    ("justice","power"), ("reason","desire"), ("order","chaos"), ("truth","appearance"),
    ("sin","grace"), ("error","path"), ("descent","ascent"), ("shadow","light"),
    ("obsession","rest"), ("hunt","escape"), ("storm","calm"),
    ("error","truth"), ("idol","method"), ("experiment","theory"), ("use","speculation"),
    ("doubt","certainty"), ("mind","body"), ("cause","effect"), ("clear","confused")
]

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ']+")

def tokenize(text: str):
    return [t.lower() for t in TOKEN_RE.findall(text)]

def is_adj(tok: str):
    return tok.endswith(("ous","ful","ive","al","able","less","ic","ish","ent","ant","ate","ory","ile","ern","arian","esque","ean"))

def is_verb(tok: str):
    if tok.endswith(("ing","ed","en","ify","ise","ize","ate")): return True
    return False

def is_noun(tok: str):
    if tok.endswith(("tion","sion","ment","ness","ity","ship","dom","ance","ence","or","er","ism","ist","acy","age","ure","hood","ward","ry")): return True
    return False

def bucketize(tokens, topk=24):
    freq = Counter(tokens)
    cand = [w for w,c in freq.most_common(4*topk) if len(w) > 2 and w not in DEFAULT_STOPWORDS]
    adjs, nouns, verbs = [], [], []
    for w in cand:
        if is_adj(w): adjs.append(w)
        elif is_verb(w): verbs.append(w)
        elif is_noun(w): nouns.append(w)
        else:
            nouns.append(w)
    def cap(lst):
        seen=set(); out=[]
        for x in lst:
            if x not in seen:
                seen.add(x); out.append(x)
            if len(out) >= topk:
                break
        return out
    return cap(adjs), cap(nouns), cap(verbs)

def mine_motifs(tokens):
    s = set(tokens)
    motifs = []
    for a,b in DEFAULT_MOTIF_PAIRS:
        if a in s or b in s:
            motifs.append([a,b])
    if not motifs:
        motifs = [["order","chaos"], ["shadow","light"]]
    return motifs[:8]

def read_tsv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                rows.append((parts[0], parts[1]))
    return rows

def merge_existing(out_path, new_data):
    if not os.path.exists(out_path):
        return new_data
    try:
        with open(out_path, "r", encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        return new_data
    for k in ["adjectives","nouns","verbs"]:
        oldset = set(old.get(k, []))
        for x in new_data.get(k, []):
            if x not in oldset:
                oldset.add(x)
        old[k] = sorted(oldset)
    old_m = [tuple(p) for p in old.get("motifs", []) if isinstance(p, list) and len(p)==2]
    new_m = [tuple(p) for p in new_data.get("motifs", []) if isinstance(p, list) and len(p)==2]
    mset = []
    seen = set()
    for p in old_m + new_m:
        if p not in seen:
            seen.add(p); mset.append(list(p))
    old["motifs"] = mset[:16]
    return old

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", default="anchors.tsv")
    ap.add_argument("--out", default="lexicon")
    ap.add_argument("--topk", type=int, default=24)
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()

    rows = read_tsv(args.anchors)
    by_anchor = {}
    for aid, txt in rows:
        by_anchor.setdefault(aid, []).append(txt)

    os.makedirs(args.out, exist_ok=True)
    for aid, texts in by_anchor.items():
        tokens = []
        for t in texts:
            tokens.extend(tokenize(t))
        adjs, nouns, verbs = bucketize(tokens, topk=args.topk)
        motifs = mine_motifs(tokens)
        data = {"adjectives": adjs, "nouns": nouns, "verbs": verbs, "motifs": motifs}
        out_path = os.path.join(args.out, f"{aid}.json")
        if args.merge:
            data = merge_existing(out_path, data)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[ok] {out_path}  (adj={len(adjs)}, noun={len(nouns)}, verb={len(verbs)}, motifs={len(motifs)})")

if __name__ == "__main__":
    main()

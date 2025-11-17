# -*- coding: utf-8 -*-
import argparse, sys, subprocess, os

def _py(cmd):
    return subprocess.call([sys.executable] + cmd, env=os.environ.copy())

def main():
    ap = argparse.ArgumentParser(prog="zyntalic", description="Zyntalic CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_lex = sub.add_parser("lexicon", help="build/merge lexicons from anchors.tsv")
    p_lex.add_argument("--anchors", default="anchors.tsv")
    p_lex.add_argument("--out", default="lexicon")
    p_lex.add_argument("--topk", type=int, default=24)
    p_lex.add_argument("--merge", action="store_true")

    p_train = sub.add_parser("train", help="train projection W from anchors.tsv")
    p_train.add_argument("--anchors", default="anchors.tsv")
    p_train.add_argument("--method", choices=["procrustes","ridge"], default="procrustes")
    p_train.add_argument("--ridge_lam", type=float, default=1e-3)

    p_gen = sub.add_parser("generate", help="generate words (streaming)")
    p_gen.add_argument("--n", type=int, default=10000)
    p_gen.add_argument("--out", default="zyntalic_words.txt")
    p_gen.add_argument("--no-proj", action="store_true", help="ignore models/W.npy if present")

    args = ap.parse_args()

    if args.cmd == "lexicon":
        code = _py(["lexicon_from_tsv.py", "--anchors", args.anchors, "--out", args.out,
                    "--topk", str(args.topk)] + (["--merge"] if args.merge else []))
        sys.exit(code)

    if args.cmd == "train":
        code = _py(["train_projection.py", "--anchors", args.anchors, "--method", args.method,
                    "--ridge_lam", str(args.ridge_lam)])
        sys.exit(code)

    if args.cmd == "generate":
        code = _py(["scripts/generate_stream.py", "--n", str(args.n), "--out", args.out] +
                   (["--no-proj"] if args.no_proj else []))
        sys.exit(code)

if __name__ == "__main__":
    main()

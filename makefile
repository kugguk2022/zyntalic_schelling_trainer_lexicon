PY?=python3

.PHONY: all anchors lexicon train gen ci format test

all: anchors lexicon train gen

anchors:
	@echo ">> Expect anchors.tsv in repo root (or create it)."

lexicon:
	$(PY) lexicon_from_tsv.py --anchors anchors.tsv --out lexicon --topk 24 --merge

train:
	$(PY) train_projection.py --anchors anchors.tsv --method procrustes

gen:
	$(PY) scripts/generate_stream.py --n 100000 --out zyntalic_words.txt

ci: format test

format:
	ruff check --fix .

test:
	pytest -q

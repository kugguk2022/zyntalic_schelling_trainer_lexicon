PY?=python3

serve:
\tuvicorn webapp.app:app --reload

convert-single:
\t$(PY) tools/parallel_to_single.py $(FILE)

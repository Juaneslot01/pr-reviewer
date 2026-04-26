PYTHON := python3

.PHONY: install run test

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest -q

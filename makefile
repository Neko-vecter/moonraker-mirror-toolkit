# makefile config 
VENV := venv
PYTHON := $(VENV)/bin/python3

# default target
.PHONY: init

# init venv
init:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	@echo "python venv init in $(VENV)"

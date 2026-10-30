# TDD / BDD Product Catalog Final Project

A Flask and PostgreSQL product catalog with unit tests and Selenium/Behave acceptance tests.

## Implemented

- Fake product factory covering all product attributes.
- Model tests for CRUD, listing, name/category/availability/price queries, and validation.
- REST API for create, retrieve, update, delete, and filtered product lists.
- BDD background data loading through the REST API.
- Nine browser scenarios covering service health, create, read, update, delete, listing, and three searches.
- Browser steps with explicit waits and reproducible Chrome for Testing setup.

## Run in the Skills Network Cloud IDE

    bash bin/setup.sh
    exit

Open a new terminal, change into this repository, then run:

    nosetests
    make lint
    honcho start

In a second terminal:

    behave

The setup script installs official Chrome for Testing and its matching driver in ~/.cache/tdd-bdd-browser.
If the lab's preinstalled browser or driver is incomplete, run python bin/setup_browser.py after installing dependencies.
Optional overrides are CHROME_BIN, CHROMEDRIVER_PATH, DRIVER, BASE_URL, and WAIT_SECONDS.

Search scenarios clear the form before choosing a filter because the starter UI initially selects availability and category values.

## Verified in the lab

- 32 unit tests passed; 97% service coverage.
- make lint passed; pylint 10.00/10.
- 9 Behave scenarios and 110 steps passed.

Based on the IBM Developer Skills Network final-project template, licensed under Apache 2.0.

.PHONY: run test docker-build docker-run clean

run:
	python main.py

test:
	python -m pytest -q

docker-build:
	docker compose build

docker-run:
	docker compose run --rm self-healer

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete

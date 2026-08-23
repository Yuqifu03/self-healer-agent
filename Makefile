.PHONY: run test benchmark docker-build docker-run clean

run:
	python -m autofix

test:
	python -m pytest -q

benchmark:
	python benchmarks/benchmark.py --smoke

docker-build:
	docker compose build

docker-run:
	docker compose run --rm self-healer

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete

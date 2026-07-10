# Convenience wrappers around plain python/docker commands — every target here is a
# one-liner around a command that works identically without make. On Windows (no GNU
# Make by default), run the wrapped command directly, or use these targets from Git
# Bash / WSL. See README "How to Use".

.PHONY: run-game run-server docker-up docker-up-postgres docker-down test lint format check clean

run-game:
	./scripts/run_game.sh

run-server:
	./scripts/run_server.sh

docker-up:
	docker compose up

docker-up-postgres:
	docker compose --profile postgres up

docker-down:
	docker compose --profile postgres down

test:
	env KIVY_NO_ARGS=1 KIVY_WINDOW=mock venv/bin/pytest -v

lint:
	venv/bin/ruff check .
	venv/bin/ruff format --check .
	venv/bin/mypy

format:
	venv/bin/ruff check --fix .
	venv/bin/ruff format .

check: lint test
	@echo "All checks passed — matches what the pre-push hook runs."

clean:
	find . -type d -name __pycache__ -not -path "./venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache

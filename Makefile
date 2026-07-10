# Convenience wrappers around plain python/docker commands — every target here is a
# one-liner around a command that works identically without make. On Windows (no GNU
# Make by default), run the wrapped command directly, or use these targets from Git
# Bash / WSL. See README "How to Use".

.PHONY: run-game run-server docker-up docker-up-postgres docker-down test lint format check clean migrate upgrade

run-game:
	./scripts/run_game.sh

run-server:
	./scripts/run_server.sh

# ใช้เมื่อแก้ server/models.py แล้วต้องการ migration ใหม่ (msg="what changed")
migrate:
	FLASK_APP=server venv/bin/flask db migrate -m "$(msg)"

# รันกับ DB ที่มีข้อมูลจริงอยู่แล้ว (production/Postgres) — DB ใหม่เอี่ยม (dev/test) ใช้
# db.create_all() อัตโนมัติอยู่แล้ว ไม่ต้องรัน target นี้
upgrade:
	FLASK_APP=server venv/bin/flask db upgrade

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

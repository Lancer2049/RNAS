.PHONY: dev api frontend test lint deploy clean

# ── Development ───────────────────────────────────────────────────

dev: api frontend
	@echo "API: http://localhost:8099 | Frontend: http://localhost:5173"

api:
	cd web/api && PYTHONPATH=".:.." uvicorn main:app --host 0.0.0.0 --port 8099 --reload

frontend:
	cd web/frontend && npm run dev

# ── Testing ──────────────────────────────────────────────────────

test:
	cd cmd/rnas-config && PYTHONPATH=. pytest -v
	cd web/api && PYTHONPATH=".:.." pytest -v

test-e2e:
	cd web/frontend && npx playwright test --reporter=line

lint:
	ruff check web/ cmd/
	ruff format --check web/ cmd/

# ── Build ────────────────────────────────────────────────────────

build:
	cd web/frontend && npm run build

# ── Deploy ───────────────────────────────────────────────────────

deploy:
	bash scripts/deploy-to-vm3.sh

# ── Clean ────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf web/frontend/dist web/frontend/node_modules/.vite

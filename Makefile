data:
	python scripts/fetch_data.py
test:
	python -m pytest -q
backend:
	uvicorn backend.app.main:app --reload --port 8000
frontend:
	cd frontend && npm install && npm run dev

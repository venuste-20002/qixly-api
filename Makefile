migrate:
	source .venv/bin/activate && \
	alembic revision --autogenerate  -m "New migration" && \
	alembic upgrade head 
run: 
	poetry run python3 -m uvicorn main:app --reload --port 4001
setup:
	./setup.sh

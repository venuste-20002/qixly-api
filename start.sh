!/bin/bash

#migrations
alembic init migrations
alembic stamp head
alembic revision --autogenerate  -m "Add changes"
alembic upgrade head


#Start server
exec uvicorn  main:app --host 0.0.0.0 --port 8000
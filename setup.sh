#!/bin/bash

# creates the env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created";
else 
    echo ".env file already exists";
fi

# creates virtual environments
if [ ! -d .venv ]; then
    python3 -m venv .venv && \
    source .venv/bin/activate && \
    echo "Virtual environment created and activated"
else
    echo ".venv directory already exists"
fi

# creates the versions alembic
if [ ! -d ./alembic/versions ]; then
   mkdir ./alembic/versions/;
   echo "Alembic versions Created";
else
    echo "Version already exists";
fi

#check if logs directory exists
if [ ! -d ./logs ]; then
    mkdir ./logs;
    echo "Logs directory created";
else
    echo "Logs directory already exists";
fi

# installs dependencies
poetry lock
poetry install;

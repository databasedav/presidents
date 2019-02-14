#!/bin/bash
source venv/bin/activate
exec gunicorn -b :5000 --worker-class eventlet -w 1 --access-logfile - --error-logfile - src.back.presidents:app
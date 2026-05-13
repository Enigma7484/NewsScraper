web: gunicorn -w 4 -b 0.0.0.0:$PORT sentiment_api:app
worker: celery -A celery_worker worker --loglevel=info

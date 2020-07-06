release: python manage.py migrate --no-input
web: gunicorn -w ${WEB_CONCURRENCY:-5} --max-requests ${MAX_REQUESTS:-1200} oraaange.wsgi --log-file -
worker: REMAP_SIGTERM=SIGQUIT DEBUG=False celery -l info -A api worker -Q default,pushes -c ${WORKER_PROCESSES:-4} --without-gossip --without-mingle --without-heartbeat

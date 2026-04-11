# Railway: `release:` is not like Heroku — migrations belong in railway.toml preDeployCommand.
# Static files: baked in via railway.toml [build] buildCommand; collectstatic below is a fallback.
web: python manage.py collectstatic --noinput --settings=communisante.settings.build_static && python -m gunicorn communisante.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120

# Railway: `release:` is not like Heroku — migrations belong in railway.toml preDeployCommand.
# Static files: produced during image build (see railway.toml). Avoid collectstatic on every boot — it slows healthchecks.
web: python -m gunicorn communisante.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --preload

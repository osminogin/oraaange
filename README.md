# Oraaange

[![Tests](https://github.com/osminogin/oraaange/workflows/Tests/badge.svg)](https://github.com/osminogin/oraaange/actions?query=workflow%3ATests) [![Flake8](https://github.com/osminogin/oraaange/workflows/Flake8/badge.svg)](https://github.com/osminogin/oraaange/actions?query=workflow%3AFlake8) [![License: Apache 2.0](https://img.shields.io/badge/License-AGPLv3-black.svg)](https://github.com/osminogin/oraaange/blob/master/COPYING)

## Requirements

* Python 3.x / Pipenv
* Django LTS / Django REST Framework
* Celery
* PostgreSQL (with PostGIS plugin)

## Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/osminogin/oraaange)


## Getting started

```bash
sudo pip install pipenv
pipenv install
make run
# or
docker-compose up postgres rabbit
cp .env-example .env
pipenv run ./manage.py runserver
```

### First start
```bash
pipenv run manage.py createsuperuser
pipenv run manage.py initapp
```

### Test running
```bash
pipenv run pytest 
```

## Docker composes

```bash
docker-compose up
```

## ChangeLog

[CHANGELOG.md](https://github.com/osminogin/oraaange/blob/master/CHANGELOG.md)

## License

See [COPYING](https://github.com/osminogin/oraaange/blob/master/COPYING)

# Metadata Server

## Description

This is an metadata server implementing the [IIIF Presentation API (version 1.0)](http://iiif.io/api/metadata/1.0/).

## Dependencies

This is intended to be a complete and up-to-date list of the project's dependencies; versions in [requirements.txt](requirements.txt) reflect what's currently deployed at Harvard.  Use of virtualenv is recommended.

* Web server (Tested with Apache2 and mod_wsgi)
* git
* Elasticsearch
* Libraries (with their associated development packages)
  * bzip2
  * libxml2
  * libxslt
  * openssl
  * sqlite
* Python 2.7
* Python packages (Install with pip)
  * django
  * elasticsearch
  * firebase-token-generator
  * lxml
  * pysqlite
  * python-dotenv

Additionally, sample deployment files for [Capistrano](http://capistranorb.com/) and [capistrano-django](https://github.com/mattjmorrison/capistrano-django) are provided, which depend on:

* Ruby 2.x
* Bundler

These are NOT a requirement for running the app.

## Configuration

This application uses python-dotenv to load environment variables from a .env file, which you must provide for the application to run.  An example with all possible settings is provided below:

```Shell
SECRET_KEY=thirtyPlusRandomCharactersUsedToSignSession  # Must be set
ALLOWED_HOSTS=example.com;otherexamplehost.org          # semicolon separated list of hosts
DEBUG=True                                              # Only in development - DO NOT SET IN PRODUCTION
ELASTICSEARCH_URL=localhost:9200                        # omit for default
ELASTICSEARCH_INDEX=manifests                           # omit for default
```

## Refreshing Manifests

A Django manage.py task has been provided to recreate a manifest that is loaded into the system (say, because the parser changed).  To use it, run the following from inside the application's virtualenv:

```Shell
manage.py refresh_manifests $SOURCE(:$IDENTIFIER)
```

If an $IDENTIFIER isn't provided, it will refresh all manifests of $SOURCE.

This task can be run from a remote host via capistrano, e.g.:

```Shell
cap $STAGE manage:refresh $SOURCE(:$IDENTIFIER)
```

## Dev Notes

Additional notes of interest to developers located [here](DEV_NOTES.md).

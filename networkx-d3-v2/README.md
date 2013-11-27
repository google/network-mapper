# Network Mapper using D3 v2

## Setting up a local environment

Network Mapper runs on [Google App Engine](https://developers.google.com/appengine/downloads). You can run it locally, or setup a public instance.

This project uses [the NDB API](https://developers.google.com/appengine/docs/python/ndb/) to store information in App Engine's datastore, and [Django](https://www.djangoproject.com/) as web framework for handling everything else (process requests, template rendering, etc.)

There are more dependencies included inside `lib` folder.


## OAuth2 Settings

Network Mapper uses [OAuth2](http://en.wikipedia.org/wiki/OAuth#OAuth_2.0)
to access data from a Google spreadsheet. You'll need to register your application with the APIs Console and generate `client_id` and `client_secret` keys. See [Using OAuth 2.0 to Access Google APIs](https://developers.google.com/accounts/docs/OAuth2#basicsteps>)

Once you've generated those keys, add them to your your configuration file copied and filled out from the template in `networkx/conf/conf_template.py` (follow the instructions in the template).


## Running the AppEngine server locally

The process for running the server is the standard one for any Google App Engine application. Inside the project folder run:

    $ dev_appserver.py .

And you will have your server running at http://localhost:8080


## Test suite

For running the test suite included within this project, you'll need to install
the python package `Mock <http://www.voidspace.org.uk/python/mock/>`_. There
are several options for installing it, but the easiest way is to use
`easy_install`::

    $ easy_install mock

Once you have mock installed in your system, you can run the test suite just
by executing::

    $ python manage.py test --settings=networkx.conf.tests auth clients core graph


## Deploying on a public AppEngine instance

To deploying the application on a public app-engine you just need to follow [Google App Engine's instructions for deploying applications](https://developers.google.com/web-toolkit/doc/latest/tutorial/appengine)

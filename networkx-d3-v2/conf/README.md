For running locally, i.e. on localhost (not on appspot or a corperate appengine), make a copy of the file `conf_template.py` file and put it in the `localhost` directory called `dev.py`. It will only be used when running locally.

For an appspot domain, put a copy in the `appsport` directory and name it after the application id, keeping the postfix `.py`. i.e. if the application field of `app.yaml` is `application_id`, the configuration file should be `appspot/application_id.py`.

For a corperate domain (i.e. the application field of `app.yaml` is of the form `corperate_domain.com:application_id`), make a directory `coperate_domain.com`, and copy the template file to `coperate_domain.com/application_id.py`.

For all the above, enter in the template file the client id and client secret from your appengine APIs account. Network Mapper uses [OAuth2](http://en.wikipedia.org/wiki/OAuth#OAuth_2.0) to access data from a Google spreadsheet. So if you don't already have one, you'll need to register your application with the APIs Console and generate `client_id` and `client_secret` keys. See [Using OAuth 2.0 to Access Google APIs](https://developers.google.com/accounts/docs/OAuth2#basicsteps).

from google.appengine.ext import ndb

class Session(ndb.Model):
    session_key = ndb.StringProperty()
    session_data = ndb.TextProperty()
    expire_date = ndb.DateTimeProperty()

# The code below is causing a circular import error when running in appengine
# Checked the django code and this method is only used in the tests.
# Have changed the appengine_sessions tests to not use it.
# Will cause the actual django session tests to fail if ran using the appengine_sessions cache_db session engine
#    def get_decoded(self):
#        return SessionStore().decode(self.session_data)

# At the bottom to win against circular imports
#from appengine_sessions.backends.db import SessionStore

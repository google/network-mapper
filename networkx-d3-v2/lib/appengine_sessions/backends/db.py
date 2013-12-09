""" Fix Django's 'write-through' (cache and datastore storage) session
backend to work with Appengine's datastore, along with whatever cache
backend is in settings.

Basically a reworking of django.contrib.sessions.backends.db, so have
a look there for definitive docs.
"""

from google.appengine.ext import ndb
from appengine_sessions.models import Session

from django.contrib.sessions.backends.base import CreateError
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.core.exceptions import SuspiciousOperation
from django.utils.encoding import force_unicode
from django.conf import settings
from datetime import datetime, timedelta


class SessionStore(DBStore):
    """Implements a session store using Appengine's datastore API instead
    of Django's abstracted DB API (since we no longer have nonrel -- just
    vanilla Django)
    """
    def __init__(self, session_key=None):
        super(SessionStore, self).__init__(session_key)

    def get_ndb_session_key(self,session_key=None):
        return ndb.Key(Session, session_key and session_key or self._get_or_create_session_key())


    """
      Session Date related methods overridden to handle the NDB DateTimeProperty
          get_expiry_age
          get_expiry_date
          set_expiry
      
      Making sure session dates always use UTC datetimes with no tzinfo
    """

    def get_expiry_age(self):
        """Get the number of seconds until the session expires."""
        expiry = self.get('_session_expiry')
        if not expiry:   # Checks both None and 0 cases
            return settings.SESSION_COOKIE_AGE
        if not isinstance(expiry, datetime):
            return expiry
        delta = expiry - datetime.utcnow()
        return delta.days * 86400 + delta.seconds

    def get_expiry_date(self):
        """Get session the expiry date (as a datetime object).

            Overridden to make sure that UTC time is used for NDB datetime
            properties """
        expiry = self.get('_session_expiry')
        if isinstance(expiry, datetime):
            return expiry
        if not expiry:   # Checks both None and 0 cases
            expiry = settings.SESSION_COOKIE_AGE
        return datetime.utcnow() + timedelta(seconds=expiry)

    def set_expiry(self, value):
        """
        Sets a custom expiration for the session. ``value`` can be an integer,
        a Python ``datetime`` or ``timedelta`` object or ``None``.

        If ``value`` is an integer, the session will expire after that many
        seconds of inactivity. If set to ``0`` then the session will expire on
        browser close.

        If ``value`` is a ``datetime`` or ``timedelta`` object, the session
        will expire at that specific future time.

        If ``value`` is ``None``, the session uses the global session expiry
        policy.
        """
        if value is None:
            # Remove any custom expiration for this session.
            try:
                del self['_session_expiry']
            except KeyError:
                pass
            return
        if isinstance(value, timedelta):
            value = datetime.utcnow() + value
        self['_session_expiry'] = value

    def load(self):
        s = self.get_ndb_session_key().get()

        if s:  
            # Make sure you compare UTC datetime now for NDB.
            if s.expire_date > datetime.utcnow():
                try:
                    return self.decode(force_unicode(s.session_data))
                except SuspiciousOperation:
                    return {}
        self.create()
        return {}

    def exists(self, session_key):
        # If session key is None then False
        if session_key:
            ndb_session_key = ndb.Key(Session,session_key)
            s = ndb_session_key.get()
            return s is not None
        return False

    def save(self, must_create=False):
        """Create and save a Session object using db.run_in_transaction, with
        key_name = session_key, raising CreateError if
        unsuccessful.
        """
       
        if must_create:
            s = self.get_ndb_session_key().get()
            if s:
                raise CreateError()

        session_data = self._get_session(no_load=must_create)
        #ed = self.get_expiry_date()
        #print datetime.datetime.utcoffset(ed)
        def txn():
            s = Session(
                id=self._get_or_create_session_key(),
                session_key=self.session_key,
                session_data=self.encode(session_data),
                expire_date=self.get_expiry_date()
            )
            s.put()

        # This is tricky and probably needs some sanity checking, because
        # TransactionFailedError can be raised, but the transaction can still
        # go on to be committed to the datastore. As far as I can see there's
        # no way to manually roll it back at that point. No idea how to test
        # this either.
        try:
            ndb.transaction(txn)
        except (ndb.Rollback):
            raise CreateError()

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._get_or_create_session_key()
        self.get_ndb_session_key(session_key).delete()
#        db.delete(db.Key.from_path('Session', session_key))


# Again, circular import fix

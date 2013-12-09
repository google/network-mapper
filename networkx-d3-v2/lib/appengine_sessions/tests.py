from appengine_sessions.backends import cached_db
from appengine_sessions.backends.cached_db import SessionStore as CacheDBSession
from appengine_sessions.backends.db import SessionStore as DatabaseSession
from appengine_sessions.mapper import DeleteMapper
from appengine_sessions.middleware import SessionMiddleware
from appengine_sessions.models import Session
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import CacheKeyWarning
from django.http import HttpResponse
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import timezone
from google.appengine.ext import testbed, ndb
from subprocess import call
from unittest import TestCase

# Use normal unittest.TestCase as Django TestCase requires a Database
# These tests are using the stubbed appengine datastore 

class SessionTestsMixin(object):
    # This does not inherit from TestCase to avoid any tests being run with this
    # class, which wouldn't work, and to allow different TestCase subclasses to
    # be used.

    backend = None # subclasses must specify

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.session = self.backend()
        for s in Session.query().fetch():
            s.delete()
        
        # Make sure the default Use Timezone setting is False
        settings.USE_TZ=False

    def tearDown(self):
        # NB: be careful to delete any sessions created; stale sessions fill up
        # the /tmp (with some backends) and eventually overwhelm it after lots
        # of runs (think buildbots)
        self.session.delete()
        self.testbed.deactivate()

    def test_new_session(self):
        self.assertFalse(self.session.modified)
        self.assertFalse(self.session.accessed)

    def test_get_empty(self):
        self.assertEqual(self.session.get('cat'), None)

    def test_store(self):
        self.session['cat'] = "dog"
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.pop('cat'), 'dog')

    def test_pop(self):
        self.session['some key'] = 'exists'
        # Need to reset these to pretend we haven't accessed it:
        self.accessed = False
        self.modified = False

        self.assertEqual(self.session.pop('some key'), 'exists')
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.get('some key'), None)

    def test_pop_default(self):
        self.assertEqual(self.session.pop('some key', 'does not exist'),
                         'does not exist')
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_setdefault(self):
        self.assertEqual(self.session.setdefault('foo', 'bar'), 'bar')
        self.assertEqual(self.session.setdefault('foo', 'baz'), 'bar')
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)

    def test_update(self):
        self.session.update({'update key': 1})
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)
        self.assertEqual(self.session.get('update key', None), 1)

    def test_has_key(self):
        self.session['some key'] = 1
        self.session.modified = False
        self.session.accessed = False
        self.assertTrue(self.session.has_key('some key'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)

    def test_values(self):
        self.assertEqual(self.session.values(), [])
        self.assertTrue(self.session.accessed)
        self.session['some key'] = 1
        self.assertEqual(self.session.values(), [1])

    def test_iterkeys(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        i = self.session.iterkeys()
        self.assertTrue(hasattr(i, '__iter__'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)
        self.assertEqual(list(i), ['x'])

    def test_itervalues(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        i = self.session.itervalues()
        self.assertTrue(hasattr(i, '__iter__'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)
        self.assertEqual(list(i), [1])

    def test_iteritems(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        i = self.session.iteritems()
        self.assertTrue(hasattr(i, '__iter__'))
        self.assertTrue(self.session.accessed)
        self.assertFalse(self.session.modified)
        self.assertEqual(list(i), [('x',1)])

    def test_clear(self):
        self.session['x'] = 1
        self.session.modified = False
        self.session.accessed = False
        self.assertEqual(self.session.items(), [('x',1)])
        self.session.clear()
        self.assertEqual(self.session.items(), [])
        self.assertTrue(self.session.accessed)
        self.assertTrue(self.session.modified)

    def test_save(self):
        self.session.save()
        self.assertTrue(self.session.exists(self.session.session_key))

    def test_delete(self):
        self.session.save()
        self.session.delete(self.session.session_key)
        self.assertFalse(self.session.exists(self.session.session_key))

    def test_flush(self):
        self.session['foo'] = 'bar'
        self.session.save()
        prev_key = self.session.session_key
        self.session.flush()
        self.assertFalse(self.session.exists(prev_key))
        self.assertNotEqual(self.session.session_key, prev_key)
        self.assertTrue(self.session.modified)
        self.assertTrue(self.session.accessed)

    def test_cycle(self):
        self.session['a'], self.session['b'] = 'c', 'd'
        self.session.save()
        prev_key = self.session.session_key
        prev_data = self.session.items()
        self.session.cycle_key()
        self.assertNotEqual(self.session.session_key, prev_key)
        self.assertEqual(self.session.items(), prev_data)

    def test_invalid_key(self):
        # Submitting an invalid session key (either by guessing, or if the db has
        # removed the key) results in a new key being generated.
        try:
            session = self.backend('1')
            try:
                session.save()
            except AttributeError:
                self.fail("The session object did not save properly.  Middleware may be saving cache items without namespaces.")
            self.assertNotEqual(session.session_key, '1')
            self.assertEqual(session.get('cat'), None)
            session.delete()
        finally:
            # Some backends leave a stale cache entry for the invalid
            # session key; make sure that entry is manually deleted
            session.delete('1')

    def test_session_key_is_read_only(self):
        def set_session_key(session):
            session.session_key = session._get_new_session_key()
        self.assertRaises(AttributeError, set_session_key, self.session)

    # Custom session expiry
    def test_default_expiry(self):
        # A normal session has a max age equal to settings
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

        # So does a custom session with an idle expiration time of 0 (but it'll
        # expire at browser close)
        self.session.set_expiry(0)
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

    def test_custom_expiry_seconds(self):
        # Using seconds
        self.session.set_expiry(10)
        delta = self.session.get_expiry_date() - datetime.utcnow()
        self.assertTrue(delta.seconds in (9, 10))

        age = self.session.get_expiry_age()
        self.assertTrue(age in (9, 10))

    def test_custom_expiry_timedelta(self):
        # Using timedelta
        self.session.set_expiry(timedelta(seconds=10))
        delta = self.session.get_expiry_date() - datetime.utcnow()
        self.assertTrue(delta.seconds in (9, 10))

        age = self.session.get_expiry_age()
        self.assertTrue(age in (9, 10))

    def test_custom_expiry_datetime(self):
        # Using fixed datetime
        self.session.set_expiry(datetime.utcnow() + timedelta(seconds=10))
        delta = self.session.get_expiry_date() - datetime.utcnow()
        self.assertTrue(delta.seconds in (9, 10))

        age = self.session.get_expiry_age()
        self.assertTrue(age in (9, 10))

    def test_custom_expiry_reset(self):
        self.session.set_expiry(None)
        self.session.set_expiry(10)
        self.session.set_expiry(None)
        self.assertEqual(self.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

    def test_get_expire_at_browser_close(self):
        # Tests get_expire_at_browser_close with different settings and different
        # set_expiry calls
        with override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=False):
            self.session.set_expiry(10)
            self.assertFalse(self.session.get_expire_at_browser_close())

            self.session.set_expiry(0)
            self.assertTrue(self.session.get_expire_at_browser_close())

            self.session.set_expiry(None)
            self.assertFalse(self.session.get_expire_at_browser_close())

        with override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=True):
            self.session.set_expiry(10)
            self.assertFalse(self.session.get_expire_at_browser_close())

            self.session.set_expiry(0)
            self.assertTrue(self.session.get_expire_at_browser_close())

            self.session.set_expiry(None)
            self.assertTrue(self.session.get_expire_at_browser_close())

    def test_decode(self):
        # Ensure we can decode what we encode
        data = {'a test key': 'a test value'}
        encoded = self.session.encode(data)
        self.assertEqual(self.session.decode(encoded), data)


class DatabaseSessionTests(SessionTestsMixin, TestCase):

    backend = DatabaseSession
   
    def test_session_get_decoded(self):
        """
        Test we can use Session.get_decoded to retrieve data stored
        in normal way
        """
        self.session['x'] = 1
        self.session.save()

        ndb_session_key = ndb.Key(Session,self.session.session_key)
        ndb_s = ndb_session_key.get()
       
        self.assertEqual(DatabaseSession().decode(ndb_s.session_data), {'x': 1})
    
    def test_sessionmanager_save(self):
        """
        Test SessionManager.save method
        """
        # Create a session
        self.session['y'] = 1
        self.session.save()

        s = Session.query(Session.session_key==self.session.session_key).get()

        # Change it
        self.session['y'] = 2
        self.session.save()
        
        # Clear cache, so that it will be retrieved from DB
        del self.session._session_cache
        self.assertEqual(self.session['y'], 2)
        
    def test_sessionmanager_save_creates_key(self):
        """
        Test SessionManager.save method
        """
        # Create a session
        self.session['y'] = 1
        self.session.save()

        # Test the session creates a key
        self.assertTrue(self.session.session_key)

    def test_sessionmanager_load(self):
        """
        Test calling the Load method creates a valid
        session object with a Key
        """

        s = self.session.load()
        
        # Load creates a session key
        self.assertTrue(self.session.session_key)
        
        # Session data is empty
        self.assertEquals(s,{})
        
        self.session['z'] = 1
        self.session.save()
        
        s = self.session.load()

        # Loading Session data is now not empty
        self.assertEquals(s,{'z':1})
        
        # Test the session object is in the datastore
        ndb_session_key = ndb.Key(Session,self.session.session_key)
        ndb_s = ndb_session_key.get()
        
        self.assertEquals(ndb_s.session_key,self.session.session_key)
        self.assertEquals(DatabaseSession().decode(ndb_s.session_data), {'z': 1})
        
    def test_session_expiry_date(self):
        """ Test the expiry date is set correct """
        
        self.session.load()
        
        ndb_session_key = ndb.Key(Session,self.session.session_key)
        s = ndb_session_key.get()
        
        now = datetime.utcnow()
        timedelta = s.expire_date - now

        self.assertTrue((settings.SESSION_COOKIE_AGE - timedelta.total_seconds()) < 1)
        
    def test_expired_session(self):
        """ Test a session with an expiry date that has the same creation date
            gets recreated as a new session when re-loaded """
            
        old_cookie_age = settings.SESSION_COOKIE_AGE
        
        settings.SESSION_COOKIE_AGE=0    
    
        self.session.load()
        
        old_session_key = self.session._session_key
    
        self.session.load()

        self.assertNotEquals(self.session._session_key,old_session_key)
        settings.SESSION_COOKIE_AGE=old_cookie_age
        
                
class DatabaseSessionWithTimeZoneTests(DatabaseSessionTests):
    """ Test the database session tests with USE TZ set to True to make 
        they all still work when this setting is set """
    
    def setUp(self):
        super(DatabaseSessionWithTimeZoneTests,self).setUp()
        settings.USE_TZ=True


class CacheDBSessionTests(SessionTestsMixin, TestCase):

    backend = CacheDBSession

    def test_sessionmanager_load(self):
        """
            Test calling the Load method creates a valid
            session object with a Key and adds to the cache
        """

        s = self.session.load()
        
        # Load creates a session key
        self.assertTrue(self.session.session_key)
        
        # Test the cache key is the same as session key with a prefix
        self.assertEquals(self.session.cache_key,'%s%s' % (cached_db.KEY_PREFIX,self.session.session_key))
        
        # Test the session is the same in memcahce        
        self.assertEquals(cache.get(self.session.cache_key),s)
        
        # Session data is empty
        self.assertEquals(s,{})
        
    def test_sessionmanager_save(self):
        """
            Test calling the Save method creates a valid
            session object with a Key and adds to the cache
        """
        self.session['z'] = 1
        self.session.save()
        
        # Save creates a session key
        self.assertTrue(self.session.session_key)
        
        # Test the cache key is the same as session key with a prefix
        self.assertEquals(self.session.cache_key,'%s%s' % (cached_db.KEY_PREFIX,self.session.session_key))
        
        # Test the session is the same in memcahce        
        self.assertEquals(cache.get(self.session.cache_key),{'z':1})
        

class CacheDBSessionWithTimeZoneTests(CacheDBSessionTests):
    """ Test the cache DB session tests with USE TZ set to True to make 
        they all still work when this setting is set """
    
    
    def setUp(self):
        super(CacheDBSessionWithTimeZoneTests,self).setUp()
        settings.USE_TZ=True

        
class FakeRequest(object):
    def __init__(self):
        self.COOKIES = {}

class SessionMiddlewareTests(TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.old_SESSION_COOKIE_SECURE = settings.SESSION_COOKIE_SECURE

    def tearDown(self):
        self.testbed.deactivate()
        settings.SESSION_COOKIE_SECURE = self.old_SESSION_COOKIE_SECURE

    def test_secure_session_cookie(self):
        settings.SESSION_COOKIE_SECURE = True

        request = FakeRequest()
        response = HttpResponse('Session test')
        middleware = SessionMiddleware()

        # Simulate a request the modifies the session
        middleware.process_request(request)
        request.session['hello'] = 'world'

        # Handle the response through the middleware
        response = middleware.process_response(request, response)
        self.assertTrue(response.cookies[settings.SESSION_COOKIE_NAME]['secure'])
        
        
class SessionCleanUpTest(TestCase):
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub(enable=True)
        
    def tearDown(self):
        self.testbed.deactivate()
         
    def test_mapper(self):
        """
            Test a session gets deleted and another
            one has been put on as a task to be deleted
        """
        for i in range(0,2):
            s = Session(session_key='%s' % i, expire_date=datetime.utcnow())
            s.put()

        mapper = DeleteMapper(Session, filters = {'lt': ('expire_date', datetime.utcnow())}, deferred_batch_size=1)
        mapper.transaction()
        
        taskqueue = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        
        # One expired session left
        self.assertEquals(Session.query().count(), 1)
        
        tasks=taskqueue.GetTasks(mapper.queue)
                                 
        # Another deferred task in the queue to remove the next expired session
        self.assertEquals(len(tasks),1)

    def test_mapper_session_data(self):
        """
            Test the mapper only deletes the expired session and
            doesn't create a new task on queue
        """
        
        s1 = Session(session_key='1', expire_date=datetime.utcnow() + timedelta(seconds=3600))
        s1.put()
        s2 = Session(session_key='2', expire_date=datetime.utcnow())
        s2.put()
        
        mapper = DeleteMapper(Session, filters = {'lt': ('expire_date', datetime.utcnow())}, deferred_batch_size=1)
        mapper.transaction()
        taskqueue = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        
        tasks=taskqueue.GetTasks(mapper.queue)
        
        # Should be no task in the queue as
        # no more sessions to delete.
        self.assertEquals(len(tasks),0)
        
        # Should be 1 valid session left
        self.assertEquals(Session.query().count(), 1)
        self.assertEquals(Session.query().get().session_key,'1')

    def test_view(self):
        """
            Test the cron view sets a deferred task
            onto the default task queue
        """
        
        c = Client()
        response = c.get('/appengine_sessions/clean-up/')
        
        taskqueue = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        self.assertEquals(response.status_code,200)
        self.assertEquals(len(taskqueue.GetTasks('default')),1)
        
    def test_mapper_batch_size(self):
        """
            Test the amount of sessions gets deleted is
            the same as the deferred_batch_size
        """
        for i in range(0,20):
            s = Session(session_key='%s' % i, expire_date=datetime.utcnow())
            s.put()

        mapper = DeleteMapper(Session, filters = {'lt': ('expire_date', datetime.utcnow())}, deferred_batch_size=10)
        mapper.transaction()
        
        taskqueue = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        
        # Should be 10 left
        self.assertEquals(Session.query().count(), 10)
        
        mapper.transaction()
        
        # Should be 0 session left
        self.assertEquals(Session.query().count(), 0)
        
        

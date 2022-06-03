"""
In this file you may place miscellaneous utility functions/classes that
don't really belong anywhere, or should be shared all over systest.
"""

import functools
import logging
import random
import string
import threading
import time

from vmware.mjolnir.constants import Constants as constants

log = logging.getLogger(__name__)
plugin_name = constants.PLUGIN_NAME


try:
    basestring
except NameError:  # py3
    basestring = unicode = str

log = logging.getLogger(__name__)


def poll(predicate, msg, timeout, sleep, *args, **kwargs):
    """
    Helper function to implement simple wait functions

    Poll <predicate> for maximum <timeout> s at <sleep> s intervals
    until it returns True, or raise a RuntimeError.

    If raise_ is False this function will return True/False instead of
    raising an error, indicating whether the wait was successful or not.

    Parameters
    ----------
    predicate: () -> Bool function
        The wait stops when the predicate function returns True
    msg: str
        A helpful message to display in the logs
    timeout: int
        How long before a RuntimeError is raised
    sleep: int
        How long to wait between calling predicate again
    raise_: bool
        If True, raise a RuntimeError on timeout. If False, return a bool
        indicating whether the predicate succeeded within the timeout
        (This argument is pulled from kwargs for backwards-compatibility)
    args: tuple
        Positional arguments passed to <predicate>
    kwargs: dict
        Keyword arguments passed to <predicate>
    """
    raise_ = kwargs.pop('raise_', True)
    log.debug('%s *** waiting maximum %d seconds for %s ***',
              plugin_name, timeout, msg)
    start = time.time()
    while time.time() < start + timeout:
        if predicate(*args, **kwargs):
            log.debug('%s *** Done waiting for %s after %d seconds ***',
                      plugin_name, msg, int(time.time() - start))
            return None if raise_ else True
        time.sleep(sleep)

    if raise_:
        raise RuntimeError('%s timeout exceeded while waiting for %s',
                           plugin_name, msg)
    return False


def retry(exceptions, retries=None, timeout=None, sleep=0):
    """
    Catch <exceptions> and call the decorated function up to <retries> times,
    or until <timeout> seconds have passed.

    usage:
    >>>@retry(urllib.URLError, timeout=60, sleep=3)
    ...def my_func():
    ...    pass
    >>>@retry(urllib.URLError, retries=12, sleep=5)
    ...def my_func():
    ...    pass

    Parameters
    ----------
    exceptions: Exception OR (Exception1, Exception2, ...)
        The exceptions to catch, prefer not to include 'Exception'
    retries: (optional) int
        Number of retries, required if timeout is None.
    timeout: (optional) int
        max-elapsed seconds to wait, required if retries is None,
    sleep: int
        Number of seconds to sleep between retries
    """
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)
    if Exception in exceptions:
        log.warning("'%s Exception' as a catch-all in retry not"
                    " recommended", plugin_name)

    assert retries or timeout, "must set retries or timeout"
    assert not (retries and timeout), "cannot set both retries and timeout"
    assert all(issubclass(e, Exception) for e in exceptions)
    assert sleep >= 0

    unit = "attempt(s)" if retries else "second(s)"

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            remaining = retries if retries else timeout
            endtime = None if retries else time.time() + timeout
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if not retries:
                        remaining = endtime - time.time()
                    if remaining <= 0:
                        log.debug('%s *** caught exception in retry '
                                  'decorator, re-raising now. ***',
                                  plugin_name)
                        raise
                    log.warn('%s *** caught exception in retry '
                             'decorator, re-raising in %d %s. traceback: ***',
                             plugin_name, remaining, unit, exc_info=True)
                    if retries:
                        remaining -= 1
                    time.sleep(sleep)
        return wrapper
    return decorator


class ThreadSafeIter(object):
    """
    Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.it)

    next = __next__  # py2


def retry_if_false(retries, interval, raise_on_error=True):
    """Annotation object, calls decorated method repeatedly if it returns
    False. Throws  TimeoutError if decorated method does not succeed
    after given number of attempts

    usage:
    >>>@retry_if_false(3, 10)
    ...def my_func():
    ...    pass

    Parameters
    ----------
    retries: (required) int
        Number of retries.
    interval: (required) int
        max-elapsed seconds to wait before retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            count = 0
            while count <= retries:
                ret = func(*args, **kwargs)
                if not ret:
                    log.debug("%s *** %s failed; Retry after an interval of"
                              " %s sec ***", plugin_name, func.__name__,
                              interval)
                    time.sleep(interval)
                else:
                    return ret
                count += 1
    return decorator


def get_random_string(length=6, prefix='', suffix='', chars=None, specialchars=False):
    """
    Return a random string

    Parameters
    ----------
    length: int
        The length of the random string, excluding any prefix/suffix
    prefix: str
        Optional, a prefix to prepend to the random string
    suffix: str
        Optional, a suffix to append to the random string
    chars: iterable of str
        Optional, may select which characters to limit the random string to
    specialchars: bool
        Optional, may select which if special characters to be included in string
    """
    if chars is None:
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        if specialchars:
            chars = chars + string.punctuation
    res = ''.join(random.choice(chars) for _ in range(length))
    return prefix + res + suffix

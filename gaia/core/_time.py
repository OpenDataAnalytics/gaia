"""Common date time representation for Gaia tasks."""

from datetime import datetime, date

import six
from dateutil.parser import parse
from dateutil.tz import gettz


class Time(datetime):

    """Subclass of the standard datetime for gaia tasks."""

    def __new__(cls, *arg, **kw):
        """Return a new datetime instance.

        This extends the standard datetime.__init__ method by interpreting
        a single argument provided:

            * string: use dateutil's parser
            * date: use the given date at midnight
            * datetime: copy constructor
            * number: interpret as milliseconds since January 1, 1970
            * *: passes the arguments to datetime.__init__

        If no arguments are supplied, this will return datetime.now().  All
        times provided are assumed to be UTC.

        (Consider adding time zone support in the future.)

        Examples:

        Get the current time
        >>> Time()  # doctest: +ELLIPSIS
        Time(...)

        Get time from a string
        >>> Time("2014-12-31")  # doctest: +ELLIPSIS
        Time(2014, 12, 31, ...)
        >>> Time("May 1, 2010")  # doctest: +ELLIPSIS
        Time(2010, 5, 1, ...)
        >>> Time("2011-04-05T08:15:00")  # doctest: +ELLIPSIS
        Time(2011, 4, 5, 8, 15, ...)
        >>> Time("1997-07-10_12:31:15")  # doctest: +ELLIPSIS
        Time(1997, 7, 10, 12, 31, 15, ...)

        Get time from a date or datetime object
        >>> Time(datetime(2014, 12, 31, 12, 30, 10))  # doctest: +ELLIPSIS
        Time(2014, 12, 31, 12, 30, 10, ...)
        >>> Time(date(2014, 11, 15))  # doctest: +ELLIPSIS
        Time(2014, 11, 15, ...)

        Get time from a javascript time stamp
        >>> Time(1428339281111)  # doctest: +ELLIPSIS
        Time(2015, 4, 6, 16, 54, 41, 111000, ...)

        Get time using the standard datetime constructor
        >>> Time(2014, 12, 15)  # doctest: +ELLIPSIS
        Time(2014, 12, 15, ...)

        Other types raise an error
        >>> Time(None)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: an integer is required...
        """
        tz = gettz('UTC')
        if len(arg) == 0:
            arg = (datetime.now(),)

        if len(arg) == 1:
            d = arg[0]

            if isinstance(d, six.string_types):
                d = parse(d.replace('_', ' '))
            elif isinstance(d, (float, int)):
                d = datetime.utcfromtimestamp(d / 1000.0)

            if isinstance(d, datetime):
                arg = (
                    d.year, d.month, d.day,
                    d.hour, d.minute, d.second,
                    d.microsecond, tz
                )
            elif isinstance(d, date):
                arg = (
                    d.year, d.month, d.day,
                    0, 0, 0,
                    0, tz
                )

        return datetime.__new__(cls, *arg, **kw)

    @classmethod
    def format(cls, time, fmt=None):
        """Return a date/time string given by fmt.

        Supports inputs accepted by Time.__init__ and format
        strings from datetime.strftime.  Defaults to output
        iso format.

        :param time: A datetime/string/number
        :param fmt str: strftime format string

        >>> Time.format('February 1, 2001', '%m/%d/%Y')
        '02/01/2001'
        >>> Time.format(981000000000)
        '2001-02-01T04:00:00+00:00'
        """
        t = cls(time)
        if fmt is None:
            return t.isoformat()
        else:
            return t.strftime(fmt)

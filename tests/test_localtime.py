""" Unit tests for the 'localtime' module.

There are separate test cases for Unix and Win32, only one of which will be
executed.

"""
import datetime
import itertools
import os
import os.path
import sys
from pathlib import Path

import pytest

from babel.localtime import LOCALTZ, _get_localzone, get_localzone

_timezones = {
    "Etc/UTC": "UTC",
    "America/New_York": "EDT",  # DST
    "Europe/Paris": "CEST",  # DST
}


@pytest.mark.skipif(sys.platform == "win32", reason="Unix tests")
class TestUnixLocaltime:
    """ Unit tests for the `localtime` module in a Unix environment.

    """
    @pytest.fixture
    def zoneinfo(self) -> Path:
        """ Get the system TZ info directory.

        :return: directory path
        """
        # This assumes the test system follows the convention of linking
        # `/etc/localtime` to the system's timezone info file somewhere in a
        # `zoneinfo/` hierarchy.
        # <https://www.unix.com/man-page/linux/4/zoneinfo>
        parts = list(Path("/etc/localtime").readlink().parts)
        while parts and parts[-1] != "zoneinfo":
            # Find the 'zoneinfo' root.
            del parts[-1]
        return Path(*parts)

    @pytest.fixture
    def environ(self):
        """ Restore os.environ after a test.

        """
        system_environ = dict(os.environ)
        yield
        os.environ.clear()
        os.environ.update(system_environ)
        return

    @pytest.mark.usefixtures("environ")
    @pytest.fixture(params=itertools.product(_timezones.items(), (True, False)))
    def timezone(self, tmp_path, request, zoneinfo):
        """ Set a test time zone via environment variable or file.

        :yield: time zone name, *i.e.* ZoneInfo.tzname()
        """
        (tzkey, tzname), use_tzenv = request.param
        if use_tzenv:
            # The `TZ` environment variable is prioritized over all other
            # methods of setting the time zone, so this should be sufficient to
            # override the system time zone regardless of /etc/localtime, etc.
            os.environ["TZ"] = tzkey
        else:
            # Set the timezone via an etc/localtime file. Note the double slash
            # in the symlink source. Because os.symlink() does not normalize
            # paths, this will appear on the file system itself, e.g.
            # `zoneinfo//Etc/UTC`. Although  irregular, this is a valid link
            # and has been observed in certain Ubuntu installations, so make
            # sure the 'localtime' module can handle them.
            # <https://github.com/python-babel/babel/issues/990>.
            try:
                del os.environ["TZ"]  # make sure /etc/localtime has priority
            except KeyError:
                pass
            etc = tmp_path.joinpath("etc")
            etc.mkdir(parents=True)
            os.symlink(f"{zoneinfo}//{tzkey}", etc.joinpath("localtime"))
        yield tzname
        return

    def test_get_localzone(self, tmp_path, timezone):
        """ Test the get_localzone() function.

        """
        # This actually tests _get_localzone(), which takes an optional root
        # path that is intended for use with tests. As of this writing, the
        # public get_localzone() function is a wrapper for _get_localzone('/').
        dst = datetime.datetime(2023, 7, 1)  # testing DST names
        assert _get_localzone(str(tmp_path)).tzname(dst) == timezone

    def test_localtz(self):
        """ Test the LOCALTZ module attribute.

        """
        assert get_localzone() == LOCALTZ
        return


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 tests")
class TestWin32Localtime:
    """ Tests for the `localtime` module in a Windows environment.

    """
    # This is just a placeholder and basic smoke test for now.
    # TODO: Add relevant tests.
    def test_localtz(self):
        """ Test the LOCALTZ module attribute.

        """
        assert get_localzone() == LOCALTZ
        return

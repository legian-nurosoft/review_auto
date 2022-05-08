from odoo import api, fields, models, _, SUPERUSER_ID, http, tools
from odoo.addons.base.models.res_users import Users as OriginalUsers
from odoo.http import request

import logging
import contextlib
import ipaddress
import datetime
import pytz

from odoo.http import SessionExpiredException
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from collections import defaultdict
from odoo.tools import collections
from os import utime
from os.path import getmtime
from time import time
_logger = logging.getLogger(__name__)


@classmethod
def _login(cls, db, login, password, user_agent_env):
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                # overide _assert_can_auth add login parameter (username)
                with self._assert_can_auth(login):
                    user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
                    if not user:
                        raise AccessDenied('test')
                    user = user.with_user(user)
                    user._check_credentials(password, user_agent_env)
                    tz = request.httprequest.cookies.get('tz') if request else None
                    if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                        # first login or missing tz -> set tz to browser tz
                        user.tz = tz
                    user._update_last_login()
        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
            raise 

        _logger.info("Login successful for db:%s login:%s from %s", db, login, ip)

        return user.id

OriginalUsers._login = _login
@contextlib.contextmanager
def _assert_can_auth(self,login ='otp'):
    # add login parameter for username check while login failed 
    # ban based username 
    """ Checks that the current environment even allows the current auth
    request to happen.

    The baseline implementation is a simple linear login cooldown: after
    a number of failures trying to log-in, the user (by login) is put on
    cooldown. During the cooldown period, login *attempts* are ignored
    and logged.

    .. warning::

        The login counter is not shared between workers and not
        specifically thread-safe, the feature exists mostly for
        rate-limiting on large number of login attempts (brute-forcing
        passwords) so that should not be much of an issue.

        For a more complex strategy (e.g. database or distribute storage)
        override this method. To simply change the cooldown criteria
        (configuration, ...) override _on_login_cooldown instead.

    .. note::

        This is a *context manager* so it can be called around the login
        procedure without having to call it itself.
    """
    # needs request for remote address
    if not request:
        yield
        return
    source = request.httprequest.remote_addr
    if login == 'otp':
        login = str(source)
    reg = self.env.registry
    failures_map = getattr(reg, '_login_failures', None)

    d= collections.defaultdict(list)
    # check if user baned is 0
    if failures_map is None:
        d[login].append(0)
        d[login].append(datetime.datetime.min)
        failures_map = reg._login_failures = d
    # check if user already get some failed login or not
    if login not in failures_map:
        reg._login_failures[login].append(0)
        reg._login_failures[login].append(datetime.datetime.min)
        
    cfg = self.env['ir.config_parameter'].sudo()
    # get cooldown time 
    delay = int(cfg.get_param('base.login_cooldown_duration', 60))
    cooldown_time = str(datetime.timedelta(seconds=delay))

   

    failures = failures_map[login][0]
    previous = failures_map[login][1]

    if self._on_login_cooldown(failures, previous):
        _logger.warning(
            "Login attempt ignored for %s on %s: "
            "%d failures since last success, last failure at %s. "
            "You can configure the number of login failures before a "
            "user is put on cooldown as well as the duration in the "
            "System Parameters. Disable this feature by setting "
            "\"base.login_cooldown_after\" to 0.",
            source, self.env.cr.dbname, failures, previous)
        if ipaddress.ip_address(source).is_private:
            _logger.warning(
                "The rate-limited IP address %s is classified as private "
                "and *might* be a proxy. If your Odoo is behind a proxy, "
                "it may be mis-configured. Check that you are running "
                "Odoo in Proxy Mode and that the proxy is properly configured, see "
                "https://www.odoo.com/documentation/14.0/setup/deploy.html#https for details.",
                source
            )
        raise AccessDenied(_("Your account has been locked for "+ cooldown_time +", please try again later. Or reset your password after your account is unlocked"))

    try:
        yield
    except AccessDenied:
        min_failures = int(cfg.get_param('base.login_cooldown_after', 5))
        failures = reg._login_failures[login][0]
        __  = reg._login_failures[login][1]
        # add fail count for user
        reg._login_failures[login][0] = failures + 1
        reg._login_failures[login][1] = datetime.datetime.now()

        raise AccessDenied('Wrong login/password. Attempts left:'+ str(min_failures - reg._login_failures[login][0]))
    else:
        reg._login_failures.pop(login, None)

OriginalUsers._assert_can_auth = _assert_can_auth

def _on_login_cooldown(self, failures, previous):
        """ Decides whether the user trying to log in is currently
        "on cooldown" and not even allowed to attempt logging in.

        The default cooldown function simply puts the user on cooldown for
        <login_cooldown_duration> seconds after each failure following the
        <login_cooldown_after>th (0 to disable).

        Can be overridden to implement more complex backoff strategies, or
        e.g. wind down or reset the cooldown period as the previous failure
        recedes into the far past.

        :param int failures: number of recorded failures (since last success)
        :param previous: timestamp of previous failure
        :type previous:  datetime.datetime
        :returns: whether the user is currently in cooldown phase (true if cooldown, false if no cooldown and login can continue)
        :rtype: bool
        """
        cfg = self.env['ir.config_parameter'].sudo()
        min_failures = int(cfg.get_param('base.login_cooldown_after', 5))
        if min_failures == 0:
            return False

        delay = int(cfg.get_param('base.login_cooldown_duration', 60))
        # add a count adjustment to check the number of failed logins
        return failures >= (min_failures - 1) and (datetime.datetime.now() - previous) < datetime.timedelta(seconds=delay)
OriginalUsers._on_login_cooldown = _on_login_cooldown

# class Users(models.Model):
#     _inherit ='res.users'
#
#     def action_disable_2fa(self):
#         """To Disable the two-factor authentication """
#         # current_status = self.totp_enabled
#         # if current_status:
#         #     self.write({'totp_enabled': False})
#         logins = ', '.join(map(repr, self.mapped('login')))
#         if not (self == self.env.user or self.env.user._is_admin() or self.env.su):
#             return False
#
#         self.revoke_all_devices()
#         self.sudo().write({'totp_secret': False})
#
#         if request and self == self.env.user:
#             self.flush()
#             # update session token so the user does not get logged out (cache cleared by change)
#             new_token = self.env.user._compute_session_token(request.session.sid)
#             request.session.session_token = new_token

class User(models.Model):
    _inherit = "res.users"

    @api.model
    def _idle_sessions_get_ignored_urls(self):
        """Pluggable method for calculating ignored urls
        Defaults to stored config param
        """
        params = self.env["ir.config_parameter"]
        return params.get_param('inactive_session_time_out_ignored_url', '').split(",")


    @api.model
    def _idle_sessions_deadline_calculate(self):
        params = self.env['ir.config_parameter'].sudo()
        delay = int(params.get_param('inactive_session_time_out_delay', 7200))
        if delay <= 0:
            return False
        return time() - delay

    @api.model
    def _idle_sessions_terminate(self, session):
        """Pluggable method for terminating a timed-out session

        This is a late stage where a session timeout can be aborted.
        Useful if you want to do some heavy checking, as it won't be
        called unless the session inactivity deadline has been reached.

        Return:
            True: session terminated
            False: session timeout cancelled
        """
        if session.db and session.uid:
            session.logout(keep_db=True)
        return True

    @api.model
    def _idle_sessions_check(self):
        """Perform session timeout validation and expire if needed."""

        if not http.request:
            return

        session = http.request.session

        # Calculate deadline
        deadline = self._idle_sessions_deadline_calculate()

        # Check if past deadline
        expired = False
        if deadline is not False:
            path = http.root.session_store.get_session_filename(session.sid)
            try:

                expired = getmtime(path) < deadline
            except OSError:
                _logger.exception(
                    "Exception reading session file modified time.",
                )
                # Force expire the session. Will be resolved with new session.
                expired = True

        # Try to terminate the session
        terminated = False
        if expired:
            terminated = self._idle_sessions_terminate(session)

        # If session terminated, all done
        if terminated:
            raise SessionExpiredException("Session expired")
        ignored_urls = self._idle_sessions_get_ignored_urls()

        if http.request.httprequest.path not in ignored_urls:
            if "path" not in locals():
                path = http.root.session_store.get_session_filename(
                    session.sid,
                )
            try:
                utime(path, None)
            except OSError:
                _logger.exception(
                    "Exception updating session file access/modified times.",
                )

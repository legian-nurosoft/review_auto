# -*- coding: utf-8 -*-

import werkzeug
import logging
import odoo
import odoo.exceptions
import werkzeug.exceptions
import traceback

from odoo.http import JsonRequest, AuthenticationError, SessionExpiredException, ustr
_logger = logging.getLogger(__name__)

def _handle_exception(self, exception):    
    """Called within an except block to allow converting exceptions
       to arbitrary responses. Anything returned (except None) will
       be used as response."""
    try:
        return super(JsonRequest, self)._handle_exception(exception)
    except Exception:
        if not isinstance(exception, SessionExpiredException):
                if exception.args and exception.args[0] == "bus.Bus not available in test mode":
                    _logger.info(exception)
                elif isinstance(exception, (odoo.exceptions.UserError,
                                            werkzeug.exceptions.NotFound)):
                    _logger.warning(exception)
                else:
                    _logger.exception("Exception during JSON request handling.")
        error = {
            'code': 200,
            'message': "Odoo Server Error",
            'data': serialize_exception(self,exception),
        }
        if isinstance(exception, werkzeug.exceptions.NotFound):
            error['http_status'] = 404
            error['code'] = 404
            error['message'] = "404: Not Found"
        if isinstance(exception, AuthenticationError):
            error['code'] = 100
            error['message'] = "Odoo Session Invalid"
        if isinstance(exception, SessionExpiredException):
            error['code'] = 100
            error['message'] = "Odoo Session Expired"
        return self._json_response(error=error)

setattr(JsonRequest,'_handle_exception',_handle_exception)

def serialize_exception(self,e):
    result = {
        "name": type(e).__module__ + "." + type(e).__name__ if type(e).__module__ else type(e).__name__,
        "debug": "",
        "message": ustr(e),
        "arguments": e.args,
        "context": getattr(e, 'context', {}),
    }
    user = self.env.user.has_group('base.group_user')
    if user :
        result['debug'] = traceback.format_exc()
    return result

setattr(JsonRequest,'serialize_exception',serialize_exception)

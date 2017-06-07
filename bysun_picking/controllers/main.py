# -*- coding: utf-8 -*-
import logging
import simplejson
import os
import openerp
import time
import random
import werkzeug.utils

from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import module_boot, login_redirect

_logger = logging.getLogger(__name__)

class PackController(http.Controller):

    @http.route(['/pack/web'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/pack/web')
            
        return request.render('bysun_picking.index')

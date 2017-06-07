# -*- encoding: utf-8 -*-

import logging
import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import openerp
from openerp import SUPERUSER_ID, api
from openerp import tools, exceptions
from openerp.osv import fields, osv, expression
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp import workflow
import re
_logger = logging.getLogger(__name__)

class ebiz_customer_complain(osv.osv):
    _inherit = "ebiz.customer.complain"

    _columns = {
        'seller_memo':fields.text(default='',string=u'卖家备注'),
    }



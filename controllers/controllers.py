# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import odoo

class Libbook(odoo.addons.web.controllers.main.Home):
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        odoo.addons.web.controllers.main.ensure_db()

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        if not redirect:
            redirect = '/web?' + str(request.httprequest.query_string,'utf-8')
        values['redirect'] = redirect

        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db,
                                               request.params['login'], request.params['password'])
            if uid is not False:
                self.save_session(request.cr, uid, request.context)
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = 'Login failed due to one of the following reasons:'
            values['reason1'] = '- Wrong login/password'
            values['reason2'] = '- User not allowed to have multiple logins.'
            values['reason3'] = '- User not allowed to login at this specific time or day'
        return request.render('web.login', values)
    
    def save_session(self, cr, uid, context=None):
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        sid = request.httprequest.session.sid
        uid = request.httprequest.session.uid
        session_obj = request.registry.get('ir.sessions')
        user_obj = request.registry.get('res.users')
        u_exp_date = user_obj.get_expiring_date(cr, request.uid,
                                                         uid, context)
        return session_obj.create(cr, SUPERUSER_ID, {'user_id': uid,
                                                     'session_id': sid,
                                                     'expiration_seconds': seconds,
                                                     'date_login': fields.datetime.now(),
                                                     'date_last_activity': fields.datetime.now(),
                                                     'logged_in': True},
                                  context=context)

#     @http.route('/libbook/libbook/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('libbook.listing', {
#             'root': '/libbook/libbook',
#             'objects': http.request.env['libbook.libbook'].search([]),
#         })

#     @http.route('/libbook/libbook/objects/<model("libbook.libbook"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('libbook.object', {
#             'object': obj
#         })
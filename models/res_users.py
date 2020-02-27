from odoo import models, fields, api, _

class lib_user(models.Model):
    _inherit = 'res.users'

      # get earlier expiring date
    def get_expiring_date(self, cr, uid, id, context):
        now = datetime.now()
        user_obj = request.registry.get('res.users')
        return user_obj
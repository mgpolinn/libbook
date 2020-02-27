from odoo import models, fields,api
from odoo.fields import Date as fDate
from datetime import timedelta
from odoo.addons import decimal_precision as dp
class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _rec_name = 'short_name'
    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date')
    _order = 'date_release desc, name'
    author_ids = fields.Many2many('res.partner',string='Authors')
    short_name = fields.Char(
            string='Short Title',
            size=100, # For Char only
            translate=False, # also for Text fields
            )
    notes = fields.Text('Internal Notes')
    state = fields.Selection(
        [('draft', 'Not Available'),
         ('available', 'Available'),
         ('lost', 'Lost')],'State'
    )
    description = fields.Html(
            string='Description',
            # optional:
            sanitize=True,
            strip_style=False,
            translate=False,)
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer(
            string='Number of Pages',
            default=0,
            help='Total book page count',
            groups='base.group_user',
            states={'lost': [('readonly', True)]},
            copy=True,
            index=False,
            readonly=False,
            required=False,
            company_dependent=False,
            )
    cost_price = fields.Float('Book Cost', dp.get_precision('Book Price'))
    reader_rating = fields.Float('Reader Average Rating', digits=(14,4))
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price', currency_field='currency_id')
    age_days = fields.Float(
            string='Days Since Release',
            compute='_compute_age',
            inverse='_inverse_age',
            search='_search_age',
            store=False,
            compute_sudo = False
    )
    publisher_id = fields.Many2one('res.partner',string='Publisher',ondelete='set null',context={},domain=[])
    publisher_city = fields.Char('Publisher City', related='publisher_id.city',readonly=True)
    
    ref_doc_id = fields.Reference(selection='_referencable_models',string="Reference Document")
    author_ids = fields.Many2many('res.partner', string='Authors')

    _sql_constraints = [('name_uniq','UNIQUE (name)','Book title must be unique.')]
    

    @api.constrains('date_release')
    def _check_release_date(self):
            for record in self:
                    if(record.date_release and record.date_release > fields.Date.today()):
                            raise models.ValidationError('Release date must be in the past.')

    @api.model
    def _referencable_models(self):
            models = self.env['res.request.link'].search([])
            return [(x.object, x.name) for x in models]

    @api.depends('date_release')
    def _compute_age(self):
            today = fDate.from_string(fDate.today())
            for book in self.filtered('date_release'):
                    delta = (today - fDate.from_string(book.date_release))
                    book.age_days = delta.days
    def _inverse_age(self):
            today = fDate.from_string(fDate.context_today(self))
            for book in self.filtered('date_release'):
                    d = today - timedelta(days=book.age_days)
                    book.date_release = fDate.to_string(d)
    
    @api.model
    def is_allowed_transition(self,old_state,new_state):
            allowed = [('draft', 'available'),
                        ('available','borrowed'),
                        ('borrowed','available'),
                        ('available','lost'),
                        ('borrowed', 'lost'),
                        ('lost', 'available')
                ]
            return (old_state,new_state) in allowed

    @api.multi
    def change_state(self,new_state):
            today_str = fields.Date.context_today(self)
            val1 = {'name': 'Eric Idle','email': 'eric.idle@example.com','date': today_str}
            val2 = {'name': 'John Cleese','email': 'john.cleese@example.com','date': today_str}
            id_list = [29,]
            partner_val = {
                    'name': 'Flying Circus2',
                    'email': 'm.python@example.com',
                    'date': today_str,
                    'is_company': True,
                    'child_ids': [
                            (6, 0, id_list)]
                            }
            record = self.env['res.partner'].create(partner_val)
            for book in self:
                    if book.is_allowed_transition(book.state,new_state):
                            book.state = new_state
                    else:
                            continue

    def _search_age(self, operator, value):
           today = fDate.from_string(fDate.context_today(self))
           value_days = timedelta(days=value)
           value_date = fDate.to_string(today - value_days)
           # convert the operator:
           # # book with age > value have a date < value_date
           operator_map = {'>': '<', '>=': '<=','<': '>', '<=': '>=',}
           new_op = operator_map.get(operator, operator)
           return [('date_release', new_op, value_date)]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id,"%s (%s)" % (record.name, record.date_release)))
        return result

class ResPartner(models.Model):
        _inherit = 'res.partner'
        _order = 'name'
        published_book_ids = fields.One2many('library.book','publisher_id',string='Published Books')
        authored_book_ids = fields.Many2many('library.book',string='Authored Books')
        count_books = fields.Integer('Number of Authored Books',compute='_compute_count_books')

        @api.depends('authored_book_ids')
        def _compute_count_books(self):
                for r in self:
                        r.count_books = len(r.authored_book_ids)


class LibraryMember(models.Model):
        _name = 'library.member'
        _inherits = {'res.partner': 'partner_id'}
        partner_id = fields.Many2one('res.partner',ondelete='cascade')
        date_start = fields.Date('Member Since')
        date_end = fields.Date('Termination Date')
        member_number = fields.Char()
        date_of_birth = fields.Date('Date of birth')
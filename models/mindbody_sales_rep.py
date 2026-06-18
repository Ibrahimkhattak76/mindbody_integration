import logging

_logger = logging.getLogger(__name__)
# mindbody_sales_rep.py
from odoo import models, fields


class MindbodySalesRep(models.Model):
    _name = 'mindbody.sales.rep'
    _description = 'Mindbody Sales Rep'

    client_id = fields.Many2one('mindbody.client', string='Client')
    staff_id = fields.Many2one('mindbody.staff', string='Staff')

    sales_rep_id = fields.Integer(string='Sales Rep ID')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    sales_rep_number = fields.Integer(string='Sales Rep Number')
    sales_rep_numbers = fields.Char(string='Sales Rep Numbers')  # JSON list

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_sales_rep.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_sales_rep(self, data):
        """
        Prepare sales rep values from API response.
        
        Args:
            data (dict): Sales rep data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.sales.rep create/write
        """
        self.ensure_one()

        sales_rep_vals = {
            'sales_rep_id': data.get('Id'),
            'first_name': data.get('FirstName'),
            'last_name': data.get('LastName'),
            'sales_rep_number': data.get('SalesRepNumber', 0),
            'sales_rep_numbers': str(data.get('SalesRepNumbers', [])),
        }

        # Remove None values
        sales_rep_vals = {k: v for k, v in sales_rep_vals.items() if v is not None and v is not False}

        return sales_rep_vals

    # mindbody_sales_rep.py

    def synchronize(self, from_date=None, to_date=None, limit=None, sales_rep_ids=None):
        """
        Synchronize sales reps from Mindbody to Odoo.
        Note: Sales reps are typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            sales_rep_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Sales reps are synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

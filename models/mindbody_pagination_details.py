# mindbody_pagination_details.py
from odoo import models, fields


class MindbodyPaginationDetails(models.Model):
    _name = 'mindbody.pagination.details'
    _description = 'Mindbody Pagination Details'

    page_number = fields.Integer(string='Page Number')
    page_size = fields.Integer(string='Page Size')
    total_result_count = fields.Integer(string='Total Result Count')
    total_page_count = fields.Integer(string='Total Page Count')

    # mindbody_pagination_details.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_pagination_details(self, data):
        """
        Prepare pagination details values from API response.
        
        Args:
            data (dict): Pagination details data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.pagination.details create/write
        """
        self.ensure_one()

        pagination_vals = {
            'page_number': data.get('PageNumber', 0),
            'page_size': data.get('PageSize', 0),
            'total_result_count': data.get('TotalResultCount', 0),
            'total_page_count': data.get('TotalPageCount', 0),
        }

        # Remove None values
        pagination_vals = {k: v for k, v in pagination_vals.items() if v is not None and v is not False}

        return pagination_vals

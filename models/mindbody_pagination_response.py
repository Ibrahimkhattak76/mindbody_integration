# mindbody_pagination_response.py
from odoo import models, fields


class MindbodyPaginationResponse(models.Model):
    _name = 'mindbody.pagination.response'
    _description = 'Mindbody Pagination Response'

    requested_limit = fields.Integer(string='Requested Limit')
    requested_offset = fields.Integer(string='Requested Offset')
    page_size = fields.Integer(string='Page Size')
    total_results = fields.Integer(string='Total Results')

    # mindbody_pagination_response.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_pagination_response(self, data):
        """
        Prepare pagination response values from API response.
        
        Args:
            data (dict): Pagination response data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.pagination.response create/write
        """

        pagination_vals = {
            'requested_limit': data.get('RequestedLimit', 0),
            'requested_offset': data.get('RequestedOffset', 0),
            'page_size': data.get('PageSize', 0),
            'total_results': data.get('TotalResults', 0),
        }

        # Remove None values
        pagination_vals = {k: v for k, v in pagination_vals.items() if v is not None and v is not False}

        return pagination_vals

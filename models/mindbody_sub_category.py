import logging

_logger = logging.getLogger(__name__)
# mindbody_sub_category.py
from odoo import models, fields


class MindbodySubCategory(models.Model):
    _name = 'mindbody.sub.category'
    _description = 'Mindbody Sub Category'

    category_id = fields.Many2one('mindbody.category', string='Category')

    sub_category_id = fields.Integer(string='Sub Category ID')
    sub_category_name = fields.Char(string='Sub Category Name')
    active = fields.Boolean(string='Active')

    # mindbody_sub_category.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_sub_category(self, data):
        """
        Prepare subcategory values from API response.
        
        Args:
            data (dict): Subcategory data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.sub.category create/write
        """
        self.ensure_one()

        sub_category_vals = {
            'sub_category_id': data.get('Id'),
            'sub_category_name': data.get('SubCategoryName') or data.get('Name'),
            'active': data.get('Active', True),
        }

        # Remove None values
        sub_category_vals = {k: v for k, v in sub_category_vals.items() if v is not None and v is not False}

        return sub_category_vals

    # mindbody_sub_category.py

    def synchronize(self, from_date=None, to_date=None, limit=None, sub_category_ids=None):
        """
        Synchronize sub categories from Mindbody to Odoo.
        Note: Sub categories are typically synced as part of category sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            sub_category_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Sub categories are synced automatically during category sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

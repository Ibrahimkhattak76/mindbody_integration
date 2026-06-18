# mindbody_class_level.py
from odoo import models, fields


class MindbodyClassLevel(models.Model):
    _name = 'mindbody.class.level'
    _description = 'Mindbody Class Level'

    level_id = fields.Integer(string='Level ID')
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_class_level(self, data):
        """
        Prepare class level values from API response.
        
        Args:
            data (dict): Class level data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.class.level create/write
        """
        self.ensure_one()

        level_vals = {
            'level_id': data.get('Id'),
            'name': data.get('Name'),
            'description': data.get('Description'),
        }

        # Remove None values
        level_vals = {k: v for k, v in level_vals.items() if v is not None and v is not False}

        return level_vals

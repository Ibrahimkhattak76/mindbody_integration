import logging

_logger = logging.getLogger(__name__)
# mindbody_membership_restriction.py
from odoo import models, fields


class MindbodyMembershipRestriction(models.Model):
    _name = 'mindbody.membership.restriction'
    _description = 'Mindbody Membership Restriction'

    contract_id = fields.Many2one('mindbody.contract', string='Contract')
    restriction_id = fields.Integer(string='Restriction ID')
    name = fields.Char(string='Name')

    # mindbody_membership_restriction.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_membership_restriction(self, data):
        """
        Prepare membership restriction values from API response.
        
        Args:
            data (dict): Membership restriction data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.membership.restriction create/write
        """
        self.ensure_one()

        restriction_vals = {
            'restriction_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        restriction_vals = {k: v for k, v in restriction_vals.items() if v is not None and v is not False}

        return restriction_vals

    # mindbody_membership_restriction.py

    def synchronize(self, from_date=None, to_date=None, limit=None, restriction_ids=None):
        """
        Synchronize membership restrictions from Mindbody to Odoo.
        Note: Membership restrictions are typically synced as part of contract sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            restriction_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Membership restrictions are synced automatically during contract sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

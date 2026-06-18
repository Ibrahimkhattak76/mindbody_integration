import logging

_logger = logging.getLogger(__name__)
# mindbody_lead_channel.py
from odoo import models, fields


class MindbodyLeadChannel(models.Model):
    _name = 'mindbody.lead.channel'
    _description = 'Mindbody Lead Channel'

    site_id = fields.Many2one('mindbody.site', string='Site')

    lead_channel_id = fields.Integer(string='Lead Channel ID')
    name = fields.Char(string='Name')
    salespipeline_id = fields.Integer(string='Sales Pipeline ID')
    universal_customer_id = fields.Char(string='Universal Customer ID')
    studio_id = fields.Integer(string='Studio ID')

    # mindbody_lead_channel.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_lead_channel(self, data):
        """
        Prepare lead channel values from API response.
        
        Args:
            data (dict): Lead channel data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.lead.channel create/write
        """
        self.ensure_one()

        lead_channel_vals = {
            'lead_channel_id': data.get('Id'),
            'name': data.get('Name'),
            'salespipeline_id': data.get('SalespipelineId'),
            'universal_customer_id': data.get('UniversalCustomerId'),
            'studio_id': data.get('StudioId'),
        }

        # Remove None values
        lead_channel_vals = {k: v for k, v in lead_channel_vals.items() if v is not None and v is not False}

        return lead_channel_vals

    # mindbody_lead_channel.py

    def synchronize(self, from_date=None, to_date=None, limit=None, lead_channel_ids=None):
        """
        Synchronize lead channels from Mindbody to Odoo.
        Note: Lead channels are typically synced as part of site sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            lead_channel_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Lead channels are synced automatically during site sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

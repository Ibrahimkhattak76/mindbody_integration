import logging

_logger = logging.getLogger(__name__)
# mindbody_prospect_stage_data.py
from odoo import models, fields


class MindbodyProspectStageData(models.Model):
    _name = 'mindbody.prospect.stage.data'
    _description = 'Mindbody Prospect Stage Data'

    client_id = fields.Many2one('mindbody.client', string='Client')

    stage_id = fields.Integer(string='Stage ID')
    active = fields.Boolean(string='Active')
    description = fields.Char(string='Description')

    # mindbody_prospect_stage_data.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_prospect_stage_data(self, data):
        """
        Prepare prospect stage data values from API response.
        
        Args:
            data (dict): Prospect stage data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.prospect.stage.data create/write
        """
        self.ensure_one()

        stage_data_vals = {
            'stage_id': data.get('Id'),
            'active': data.get('Active', True),
            'description': data.get('Description'),
        }

        # Remove None values
        stage_data_vals = {k: v for k, v in stage_data_vals.items() if v is not None and v is not False}

        return stage_data_vals

    # mindbody_prospect_stage_data.py

    def synchronize(self, from_date=None, to_date=None, limit=None, prospect_stage_data_ids=None):
        """
        Synchronize prospect stage data from Mindbody to Odoo.
        Note: Prospect stage data is typically synced as part of client sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            prospect_stage_data_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Prospect stage data is synced automatically during client sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

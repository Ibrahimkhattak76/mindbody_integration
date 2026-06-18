import logging

_logger = logging.getLogger(__name__)
# mindbody_client_arrival.py
from odoo import models, fields


class MindbodyClientArrival(models.Model):
    _name = 'mindbody.client.arrival'
    _description = 'Mindbody Client Arrival'

    client_id = fields.Many2one('mindbody.client', string='Client')

    arrival_program_id = fields.Integer(string='Arrival Program ID')
    arrival_program_name = fields.Char(string='Arrival Program Name')
    can_access = fields.Boolean(string='Can Access')
    locations_ids = fields.Char(string='Locations IDs')  # JSON list

    # For add arrival response
    arrival_added = fields.Boolean(string='Arrival Added')
    client_service_id_ref = fields.Many2one('mindbody.client.service', string='Client Service')

    # mindbody_client_arrival.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_arrival(self, data):
        """
        Prepare client arrival values from API response.
        
        Args:
            data (dict): Client arrival data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.client.arrival create/write
        """
        self.ensure_one()

        arrival_vals = {
            'arrival_program_id': data.get('ArrivalProgramID'),
            'arrival_program_name': data.get('ArrivalProgramName'),
            'can_access': data.get('CanAccess', False),
            'locations_ids': str(data.get('LocationsIDs', [])),
            'arrival_added': data.get('ArrivalAdded', False),
        }

        # Remove None values
        arrival_vals = {k: v for k, v in arrival_vals.items() if v is not None and v is not False}

        return arrival_vals

    # mindbody_client_arrival.py

    def synchronize(self, from_date=None, to_date=None, limit=None, arrival_ids=None):
        """
        Synchronize client arrivals from Mindbody to Odoo.
        Note: Client arrivals are typically recorded in real-time, not bulk synced.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            arrival_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Client arrivals should be recorded in real-time via webhook or API call")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

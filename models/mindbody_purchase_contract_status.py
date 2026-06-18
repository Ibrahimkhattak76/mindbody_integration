import logging

_logger = logging.getLogger(__name__)
# mindbody_purchase_contract_status.py
from odoo import models, fields


class MindbodyPurchaseContractStatus(models.Model):
    _name = 'mindbody.purchase.contract.status'
    _description = 'Mindbody Purchase Contract Status'

    client_id = fields.Char(string='Client ID')
    unique_client_id = fields.Integer(string='Unique Client ID')
    location_id = fields.Integer(string='Location ID')
    contract_id = fields.Integer(string='Contract ID')
    client_contract_id = fields.Integer(string='Client Contract ID')
    totals_id = fields.Many2one('mindbody.purchase.totals', string='Totals')
    payment_processing_failure_ids = fields.Many2many('mindbody.error.info', string='Payment Processing Failures')

    # mindbody_purchase_contract_status.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_purchase_contract_status(self, data):
        """
        Prepare purchase contract status values from API response.
        
        Args:
            data (dict): Purchase contract status data from Mindbody API (from /sale/purchasecontractstatus endpoint)
            
        Returns:
            dict: Values ready for mindbody.purchase.contract.status create/write
        """
        self.ensure_one()

        # Prepare totals (Many2one)
        totals_vals = None
        if data.get('Totals'):
            totals_vals = self.env['mindbody.purchase.totals']._prepare_purchase_totals(data['Totals'])

        # Prepare payment failures (Many2many)
        failure_commands = []
        for failure_data in data.get('PaymentProcessingFailures', []):
            failure_vals = self.env['mindbody.error.info']._prepare_error_info(failure_data)
            if failure_vals:
                failure_commands.append((0, 0, failure_vals))

        status_vals = {
            'client_id': data.get('ClientId'),
            'unique_client_id': data.get('UniqueClientId', 0),
            'location_id': data.get('LocationId'),
            'contract_id': data.get('ContractId'),
            'client_contract_id': data.get('ClientContractId'),

            # Many2many fields
            'payment_processing_failure_ids': failure_commands if failure_commands else [(5, 0, 0)],
        }

        # Add Many2one fields with create commands
        if totals_vals:
            status_vals['totals_id'] = (0, 0, totals_vals)

        # Remove None values
        status_vals = {k: v for k, v in status_vals.items() if v is not None and v is not False}

        return status_vals

    # mindbody_purchase_contract_status.py

    def synchronize(self, from_date=None, to_date=None, limit=None, status_ids=None):
        """
        Synchronize purchase contract status from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            status_ids (list, optional): Specific status IDs to sync
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            # Prepare parameters
            params = {}
            if limit:
                params['Limit'] = limit
            if status_ids:
                params['StatusIDs'] = ','.join(map(str, status_ids)) if isinstance(status_ids, list) else status_ids

            _logger.info(f"Starting purchase contract status sync with params: {params}")

            # Fetch purchase contract status from Mindbody API
            response = api.get_sale_purchasecontractstatus(params=params)

            # The response is a single object, not an array
            status_data = response if isinstance(response, dict) else {}

            if not status_data:
                _logger.info("No purchase contract status found to sync")
                return stats

            # Check if status already exists by client_id and contract_id
            client_id = status_data.get('ClientId')
            contract_id = status_data.get('ContractId')

            if client_id and contract_id:
                existing = self.search([
                    ('client_id', '=', client_id),
                    ('contract_id', '=', contract_id)
                ], limit=1)

                # Prepare status values
                status_vals = self._prepare_purchase_contract_status(status_data)

                if existing:
                    existing.write(status_vals)
                    stats['updated'] += 1
                    _logger.info(f"Updated purchase contract status for client {client_id}, contract {contract_id}")
                else:
                    self.create(status_vals)
                    stats['created'] += 1
                    _logger.info(f"Created purchase contract status for client {client_id}, contract {contract_id}")

            _logger.info(
                f"Purchase contract status sync completed: {stats['created']} created, {stats['updated']} updated, "
                f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync purchase contract status")
            stats['errors'] += 1
            raise UserError(f"Purchase contract status sync failed: {str(e)}")

        return stats

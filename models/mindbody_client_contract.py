import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from odoo import models, fields


class MindbodyClientContract(models.Model):
    _name = 'mindbody.client.contract'
    _description = 'Mindbody Client Contract'

    client_id = fields.Many2one('mindbody.client', string='Client')
    contract_id = fields.Many2one('mindbody.contract', string='Contract')

    payer_client_id = fields.Integer(string='Payer Client ID')
    agreement_date = fields.Datetime(string='Agreement Date')
    autopay_status = fields.Selection([
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Terminated', 'Terminated')
    ], string='Autopay Status', default='Active')
    auto_renewing = fields.Boolean(string='Auto Renewing')
    first_auto_pay = fields.Integer(string='First Auto Pay')
    last_auto_pay = fields.Integer(string='Last Auto Pay')
    normal_auto_pay = fields.Integer(string='Normal Auto Pay')
    is_month_to_month = fields.Boolean(string='Is Month To Month')
    auto_renew_client_contract_id = fields.Integer(string='Auto Renew Client Contract ID')
    contract_text = fields.Text(string='Contract Text')
    contract_auto_renewed = fields.Boolean(string='Contract Auto Renewed')
    contract_name = fields.Char(string='Contract Name')
    end_date = fields.Datetime(string='End Date')
    client_contract_id = fields.Integer(string='Client Contract ID')
    origination_location_id = fields.Integer(string='Origination Location ID')
    start_date = fields.Datetime(string='Start Date')
    site_id = fields.Integer(string='Site ID')
    upcoming_autopay_event_ids = fields.One2many('mindbody.upcoming.autopay.event', 'client_contract_id',
                                                 string='Upcoming Autopay Events')
    contract_id_int = fields.Integer(string='Contract ID Integer')
    termination_date = fields.Datetime(string='Termination Date')
    minimum_commitment_value = fields.Integer(string='Minimum Commitment Value')
    minimum_commitment_unit = fields.Selection([
        ('Weeks', 'Weeks'),
        ('Months', 'Months')
    ], string='Minimum Commitment Unit', default='Weeks')
    minimum_commitment_end_date = fields.Datetime(string='Minimum Commitment End Date')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_client_contract.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_contract(self, data):
        """
        Prepare client contract values from API response.
        
        Args:
            data (dict): Client contract data from Mindbody API (from /client/clientcontracts endpoint)
            
        Returns:
            dict: Values ready for mindbody.client.contract create/write
        """
        self.ensure_one()

        # Prepare upcoming autopay events (One2many)
        event_commands = []
        for event_data in data.get('UpcomingAutopayEvents', []):
            event_vals = self.env['mindbody.upcoming.autopay.event']._prepare_upcoming_autopay_event(event_data)
            if event_vals:
                event_commands.append((0, 0, event_vals))

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        client_contract_vals = {
            'payer_client_id': data.get('PayerClientId', 0),
            'agreement_date': data.get('AgreementDate'),
            'autopay_status': data.get('AutopayStatus', 'Active'),
            'auto_renewing': data.get('AutoRenewing', False),
            'first_auto_pay': data.get('FirstAutoPay', 0),
            'last_auto_pay': data.get('LastAutoPay', 0),
            'normal_auto_pay': data.get('NormalAutoPay', 0),
            'is_month_to_month': data.get('IsMonthToMonth', False),
            'auto_renew_client_contract_id': data.get('AutoRenewClientContractID', 0),
            'contract_text': data.get('ContractText'),
            'contract_auto_renewed': data.get('ContractAutoRenewed', False),
            'contract_name': data.get('ContractName'),
            'end_date': data.get('EndDate'),
            'client_contract_id': data.get('Id'),
            'origination_location_id': data.get('OriginationLocationId'),
            'start_date': data.get('StartDate'),
            'site_id': data.get('SiteId'),
            'contract_id_int': data.get('ContractID'),
            'termination_date': data.get('TerminationDate'),
            'minimum_commitment_value': data.get('MinimumCommitmentValue', 0),
            'minimum_commitment_unit': data.get('MinimumCommitmentUnit', 'Weeks'),
            'minimum_commitment_end_date': data.get('MinimumCommitmentEndDate'),

            # One2many fields
            'upcoming_autopay_event_ids': event_commands if event_commands else None,
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            client_contract_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        client_contract_vals = {k: v for k, v in client_contract_vals.items() if v is not None and v is not False}

        return client_contract_vals

    # mindbody_client_contract.py

    def synchronize(self, from_date=None, to_date=None, limit=None, client_contract_ids=None):
        """
        Synchronize client contracts from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified client contracts
            to_date (str, optional): End date for modified client contracts
            limit (int, optional): Maximum number of records to fetch
            client_contract_ids (list, optional): Specific client contract IDs to sync
            
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
            if client_contract_ids:
                params['ClientContractIDs'] = ','.join(map(str, client_contract_ids)) if isinstance(client_contract_ids,
                                                                                                    list) else client_contract_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting client contract sync with params: {params}")

            # Fetch client contracts from Mindbody API
            response = api.get_client_clientcontracts(params=params)
            contracts_data = response.get('Contracts', []) if isinstance(response, dict) else []

            if not contracts_data:
                _logger.info("No client contracts found to sync")
                return stats

            _logger.info(f"Fetched {len(contracts_data)} client contracts from Mindbody")

            # Process each client contract
            for contract_data in contracts_data:
                try:
                    contract_id = contract_data.get('Id')
                    if not contract_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping client contract without ID")
                        continue

                    # Check if client contract already exists
                    existing = self.search([('client_contract_id', '=', contract_id)], limit=1)

                    # Prepare client contract values
                    contract_vals = self._prepare_client_contract(contract_data)

                    if existing:
                        existing.write(contract_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated client contract {contract_id}")
                    else:
                        self.create(contract_vals)
                        stats['created'] += 1
                        _logger.info(f"Created client contract {contract_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing client contract {contract_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Client contract sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync client contracts")
            stats['errors'] += 1
            raise UserError(f"Client contract sync failed: {str(e)}")

        return stats

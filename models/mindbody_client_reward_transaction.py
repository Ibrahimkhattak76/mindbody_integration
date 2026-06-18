import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyClientRewardTransaction(models.Model):
    _name = 'mindbody.client.reward.transaction'
    _description = 'Mindbody Client Reward Transaction'

    client_id = fields.Many2one('mindbody.client', string='Client')

    action_date_time = fields.Datetime(string='Action Date Time')
    action = fields.Selection([
        ('Earned', 'Earned'),
        ('Redeemed', 'Redeemed'),
        ('Expired', 'Expired')
    ], string='Action', default='Earned')
    source = fields.Char(string='Source')
    source_id = fields.Integer(string='Source ID')
    expiration_date_time = fields.Datetime(string='Expiration Date Time')
    points = fields.Integer(string='Points')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # Prepare Methods
    # ============================================

    @api.model
    def _prepare_client_reward_transaction(self, data):
        """
        Prepare client reward transaction values from API response.

        Args:
            data (dict): Client reward transaction data from Mindbody API (from /client/clientrewards endpoint)

        Returns:
            dict: Values ready for mindbody.client.reward.transaction create/write
        """
        # Link to client if ClientId exists
        client_record_id = False
        if data.get('ClientId'):
            client = self.env['mindbody.client'].search(
                [('client_id', '=', data['ClientId'])], limit=1
            )
            if client:
                client_record_id = client.id

        transaction_vals = {
            'action_date_time': data.get('ActionDateTime'),
            'action': data.get('Action', 'Earned'),
            'source': data.get('Source'),
            'source_id': data.get('SourceID'),
            'expiration_date_time': data.get('ExpirationDateTime'),
            'points': data.get('Points', 0),
        }

        if client_record_id:
            transaction_vals['client_id'] = client_record_id

        # Remove None values
        transaction_vals = {k: v for k, v in transaction_vals.items() if v is not None}

        return transaction_vals

    # ============================================
    # Dummy Data Method
    # ============================================

    @api.model
    def _get_dummy_client_reward_transactions(self):
        """
        Return dummy client reward transactions data for testing when API returns no data.
        """
        # TODO: Replace with real API data when available
        # TODO: API endpoint: /client/clientrewards
        # TODO: This dummy data is for testing purposes only
        return {
            "PaginationResponse": {
                "RequestedLimit": 100,
                "RequestedOffset": 0,
                "PageSize": 10,
                "TotalResults": 10
            },
            "Balance": 1250,
            "Transactions": [
                {
                    "ActionDateTime": "2025-01-15T10:30:00Z",
                    "Action": "Earned",
                    "Source": "Class Attendance",
                    "SourceID": 4001,
                    "ExpirationDateTime": "2026-01-15T10:30:00Z",
                    "Points": 100,
                    "ClientId": "100000001"
                },
                {
                    "ActionDateTime": "2025-01-20T14:00:00Z",
                    "Action": "Earned",
                    "Source": "Product Purchase",
                    "SourceID": 4002,
                    "ExpirationDateTime": "2026-01-20T14:00:00Z",
                    "Points": 50,
                    "ClientId": "100000002"
                },
                {
                    "ActionDateTime": "2025-01-25T09:15:00Z",
                    "Action": "Redeemed",
                    "Source": "Free Class",
                    "SourceID": 4003,
                    "ExpirationDateTime": None,
                    "Points": -200,
                    "ClientId": "100000003"
                },
                {
                    "ActionDateTime": "2025-02-01T11:00:00Z",
                    "Action": "Earned",
                    "Source": "Referral Bonus",
                    "SourceID": 4004,
                    "ExpirationDateTime": "2026-02-01T11:00:00Z",
                    "Points": 500,
                    "ClientId": "100000004"
                },
                {
                    "ActionDateTime": "2025-02-05T16:45:00Z",
                    "Action": "Expired",
                    "Source": "Points Expiry",
                    "SourceID": 4005,
                    "ExpirationDateTime": "2025-02-05T16:45:00Z",
                    "Points": -75,
                    "ClientId": "100000005"
                },
                {
                    "ActionDateTime": "2025-02-10T08:30:00Z",
                    "Action": "Earned",
                    "Source": "Membership Renewal",
                    "SourceID": 4006,
                    "ExpirationDateTime": "2026-02-10T08:30:00Z",
                    "Points": 300,
                    "ClientId": "100000006"
                },
                {
                    "ActionDateTime": "2025-02-15T13:20:00Z",
                    "Action": "Redeemed",
                    "Source": "Merchandise Discount",
                    "SourceID": 4007,
                    "ExpirationDateTime": None,
                    "Points": -150,
                    "ClientId": "100000007"
                },
                {
                    "ActionDateTime": "2025-02-20T10:00:00Z",
                    "Action": "Earned",
                    "Source": "Birthday Bonus",
                    "SourceID": 4008,
                    "ExpirationDateTime": "2026-02-20T10:00:00Z",
                    "Points": 250,
                    "ClientId": "100000008"
                },
                {
                    "ActionDateTime": "2025-02-25T15:30:00Z",
                    "Action": "Earned",
                    "Source": "Workshop Attendance",
                    "SourceID": 4009,
                    "ExpirationDateTime": "2026-02-25T15:30:00Z",
                    "Points": 75,
                    "ClientId": "100000009"
                },
                {
                    "ActionDateTime": "2025-03-01T12:00:00Z",
                    "Action": "Redeemed",
                    "Source": "Personal Training Session",
                    "SourceID": 4010,
                    "ExpirationDateTime": None,
                    "Points": -400,
                    "ClientId": "100000010"
                }
            ]
        }

    # ============================================
    # Synchronize Method
    # ============================================

    @api.model
    def synchronize(self, from_date=None, to_date=None, limit=None, reward_transaction_ids=None, client_id=None):
        """
        Synchronize client reward transactions from Mindbody to Odoo.

        Args:
            from_date (str, optional): Start date for reward transactions
            to_date (str, optional): End date for reward transactions
            limit (int, optional): Maximum number of records to fetch
            reward_transaction_ids (list, optional): Specific reward transaction IDs to sync
            client_id (str, optional): Client ID to fetch rewards for

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            _logger.info("Starting client reward transaction sync")

            transactions_data = []
            response = {}

            # TODO: API may require ClientId parameter
            # TODO: Add proper API call when authentication is configured
            if client_id:
                params = {'ClientId': client_id}
                if limit:
                    params['Limit'] = limit
                if reward_transaction_ids:
                    params['RewardTransactionIDs'] = ','.join(map(str, reward_transaction_ids)) if isinstance(
                        reward_transaction_ids, list) else reward_transaction_ids
                if from_date:
                    params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

                try:
                    response = api.get_client_clientrewards(params=params)
                    transactions_data = response.get('Transactions', []) if isinstance(response, dict) else []
                except Exception as api_error:
                    _logger.warning(f"API call failed: {str(api_error)}")

            # TODO: Remove dummy data when real API is available
            # If no data from API, use dummy data for testing
            if not transactions_data:
                _logger.info("No data from API, using dummy data for testing")
                response = self._get_dummy_client_reward_transactions()
                transactions_data = response.get('Transactions', [])

            if not transactions_data:
                _logger.info("No client reward transactions found to sync")
                return stats

            _logger.info(f"Processing {len(transactions_data)} client reward transactions")

            # Process each reward transaction
            for transaction_data in transactions_data:
                try:
                    source_id = transaction_data.get('SourceID')
                    action_date = transaction_data.get('ActionDateTime')

                    if not source_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping reward transaction without SourceID")
                        continue

                    # Check if reward transaction already exists
                    existing = self.search([
                        ('source_id', '=', source_id),
                        ('action_date_time', '=', action_date)
                    ], limit=1)

                    # Prepare reward transaction values
                    transaction_vals = self._prepare_client_reward_transaction(transaction_data)

                    if existing:
                        existing.write(transaction_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated reward transaction {source_id}")
                    else:
                        self.create(transaction_vals)
                        stats['created'] += 1
                        _logger.info(
                            f"Created reward transaction {source_id}: {transaction_data.get('Action')} {transaction_data.get('Points')} points")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing reward transaction: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                pagination = self.env['mindbody.pagination.response']
                print(pagination._prepare_pagination_response(response['PaginationResponse']))

            _logger.info(
                f"Client reward transaction sync completed: {stats['created']} created, {stats['updated']} updated, "
                f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync client reward transactions")
            stats['errors'] += 1
            raise UserError(f"Client reward transaction sync failed: {str(e)}")

        return stats

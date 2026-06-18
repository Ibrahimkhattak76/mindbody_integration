import logging

_logger = logging.getLogger(__name__)
# mindbody_client_index.py
from odoo import models, fields


class MindbodyClientIndex(models.Model):
    _name = 'mindbody.client.index'
    _description = 'Mindbody Client Index'

    client_index_id = fields.Integer(string='Client Index ID')
    name = fields.Char(string='Name')
    required_business_mode = fields.Boolean(string='Required Business Mode')
    required_consumer_mode = fields.Boolean(string='Required Consumer Mode')
    value_ids = fields.One2many('mindbody.client.index.value', 'client_index_id', string='Values')
    action = fields.Selection([
        ('None', 'None'),
        ('Added', 'Added'),
        ('Updated', 'Updated'),
        ('Failed', 'Failed'),
        ('Removed', 'Removed')
    ], string='Action', default='None')

    # For add/update response
    show_on_new_client = fields.Boolean(string='Show On New Client')
    show_on_enrollment_roster = fields.Boolean(string='Show On Enrollment Roster')
    edit_on_enrollment_roster = fields.Boolean(string='Edit On Enrollment Roster')
    sort_order = fields.Integer(string='Sort Order')
    show_in_consumer_mode = fields.Boolean(string='Show In Consumer Mode')

    # mindbody_client_index.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_index(self, data):
        """
        Prepare client index values from API response.
        
        Args:
            data (dict): Client index data from Mindbody API (from /client/clientindexes endpoint)
            
        Returns:
            dict: Values ready for mindbody.client.index create/write
        """
        self.ensure_one()

        # Prepare values (One2many)
        value_commands = []
        for value_data in data.get('Values', []):
            value_vals = self.env['mindbody.client.index.value']._prepare_client_index_value(value_data)
            if value_vals:
                value_commands.append((0, 0, value_vals))

        client_index_vals = {
            'client_index_id': data.get('Id'),
            'name': data.get('Name'),
            'required_business_mode': data.get('RequiredBusinessMode', False),
            'required_consumer_mode': data.get('RequiredConsumerMode', False),
            'action': data.get('Action', 'None'),
            'show_on_new_client': data.get('ShowOnNewClient', False),
            'show_on_enrollment_roster': data.get('ShowOnEnrollmentRoster', False),
            'edit_on_enrollment_roster': data.get('EditOnEnrollmentRoster', False),
            'sort_order': data.get('SortOrder', 0),
            'show_in_consumer_mode': data.get('ShowInConsumerMode', False),

            # One2many fields
            'value_ids': value_commands if value_commands else None,
        }

        # Remove None values
        client_index_vals = {k: v for k, v in client_index_vals.items() if v is not None and v is not False}

        return client_index_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, client_index_ids=None):
        """
        Synchronize client indexes from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified client indexes
            to_date (str, optional): End date for modified client indexes
            limit (int, optional): Maximum number of records to fetch
            client_index_ids (list, optional): Specific client index IDs to sync
            
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
            if client_index_ids:
                params['ClientIndexIDs'] = ','.join(map(str, client_index_ids)) if isinstance(client_index_ids,
                                                                                              list) else client_index_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting client index sync with params: {params}")

            # Fetch client indexes from Mindbody API
            response = api.get_client_clientindexes(params=params)
            indexes_data = response.get('ClientIndexes', []) if isinstance(response, dict) else []

            if not indexes_data:
                _logger.info("No client indexes found to sync")
                return stats

            _logger.info(f"Fetched {len(indexes_data)} client indexes from Mindbody")

            # Process each client index
            for index_data in indexes_data:
                try:
                    index_id = index_data.get('Id')
                    if not index_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping client index without ID")
                        continue

                    # Check if client index already exists
                    existing = self.search([('client_index_id', '=', index_id)], limit=1)

                    # Prepare client index values
                    index_vals = self._prepare_client_index(index_data)

                    if existing:
                        existing.write(index_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated client index {index_id}: {index_data.get('Name')}")
                    else:
                        self.create(index_vals)
                        stats['created'] += 1
                        _logger.info(f"Created client index {index_id}: {index_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing client index {index_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            _logger.info(f"Client index sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync client indexes")
            stats['errors'] += 1
            raise UserError(f"Client index sync failed: {str(e)}")

        return stats

import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyClientDuplicate(models.Model):
    _name = 'mindbody.client.duplicate'
    _description = 'Mindbody Client Duplicate'

    client_id = fields.Char(string='Client ID')
    unique_id = fields.Integer(string='Unique ID')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    email = fields.Char(string='Email')

    # Link to the original client record
    original_client_id = fields.Many2one('mindbody.client', string='Original Client', index=True)
    duplicate_client_id = fields.Many2one('mindbody.client', string='Duplicate Client', index=True)

    # Match type and score
    match_type = fields.Selection([
        ('exact_email', 'Exact Email Match'),
        ('similar_name', 'Similar Name'),
        ('same_name_diff_email', 'Same Name Different Email'),
        ('similar_email', 'Similar Email'),
    ], string='Match Type')
    match_score = fields.Integer(string='Match Score')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # HELPER: Get client display name for logging
    # ============================================
    def _get_client_display_name(self, client):
        """
        Build a human-readable name for logging purposes.
        """
        if client.display_name:
            return client.display_name
        if client.first_name or client.last_name:
            parts = [p for p in [client.first_name, client.last_name] if p]
            return ' '.join(parts)
        return f"ID:{client.client_id}"

    # ============================================
    # Prepare Methods
    # ============================================

    @api.model
    def _prepare_client_duplicate(self, original_client, duplicate_client, match_type, match_score=0):
        """
        Prepare client duplicate values for Odoo create/write.
        """
        duplicate_vals = {
            'client_id': duplicate_client.client_id,
            'unique_id': duplicate_client.id,
            'first_name': duplicate_client.first_name,
            'last_name': duplicate_client.last_name,
            'email': duplicate_client.email,
            'original_client_id': original_client.id,
            'duplicate_client_id': duplicate_client.id,
            'match_type': match_type,
            'match_score': match_score,
        }

        # Remove None values
        duplicate_vals = {k: v for k, v in duplicate_vals.items() if v is not None}

        return duplicate_vals

    # ============================================
    # Synchronize Method - Find duplicates in Odoo
    # ============================================

    @api.model
    def synchronize(self, from_date=None, to_date=None, limit=None, duplicate_ids=None,
                    first_name=None, last_name=None, email=None, client_id=None, batch_size=50):
        """
        Find duplicate clients within Odoo's mindbody.client table.

        This method compares clients in the local database to find potential duplicates
        based on matching emails, similar names, etc.

        TWO MODES:
        1. MANUAL MODE: If first_name, last_name, email are provided,
           search for duplicates of that specific person.
        2. BATCH MODE (default): Scan all clients and find duplicates among them.

        DUPLICATE DETECTION RULES:
        - Exact email match (highest confidence)
        - Same first_name + last_name, different emails
        - Similar names (using fuzzy matching)

        Args:
            from_date (str, optional): Not used for local search
            to_date (str, optional): Not used for local search
            limit (int, optional): Maximum records to process
            duplicate_ids (list, optional): Not used
            first_name (str, optional): Manual search - first name
            last_name (str, optional): Manual search - last name
            email (str, optional): Manual search - email
            client_id (int, optional): Find duplicates for ONE specific client
            batch_size (int, optional): Max clients to process per run. Default 50.

        Returns:
            dict: Statistics of found duplicates
        """
        total_stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0, 'remaining': 0}

        # ============================================
        # MODE 1: MANUAL SEARCH (specific client provided)
        # ============================================
        if first_name or last_name or email:
            _logger.info(f"Manual duplicate search for: {first_name} {last_name} ({email})")
            manual_stats = self._find_duplicates_manual(
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            return manual_stats

        # ============================================
        # MODE 2: BATCH SEARCH (find all duplicates)
        # ============================================

        # Build domain for clients to check
        client_domain = []
        if client_id:
            client_domain.append(('id', '=', client_id))

        # Get all clients
        all_clients = self.env['mindbody.client'].search(client_domain)

        if not all_clients:
            _logger.warning("No clients found to search for duplicates")
            return total_stats

        # Apply batch size
        clients_to_process = all_clients[:batch_size]
        remaining = len(all_clients) - len(clients_to_process)
        total_stats['remaining'] = remaining

        _logger.info(
            f"Starting duplicate detection for {len(clients_to_process)} client(s) "
            f"(batch {len(clients_to_process)}/{len(all_clients)}, "
            f"remaining: {remaining})"
        )

        # Track processed pairs to avoid duplicates
        processed_pairs = set()

        # Iterate through clients
        for i, client in enumerate(clients_to_process):
            try:
                client_display = self._get_client_display_name(client)

                # Skip clients without any identifiable data
                if not client.first_name and not client.last_name and not client.email:
                    _logger.info(f"Client {client_display} has no identifiable data - skipping")
                    total_stats['skipped'] += 1
                    continue

                # Find duplicates for this client
                client_stats = self._find_duplicates_for_client(
                    client,
                    all_clients,
                    processed_pairs
                )

                # Accumulate stats
                for key in ['created', 'updated', 'errors', 'skipped']:
                    total_stats[key] += client_stats.get(key, 0)

            except Exception as e:
                total_stats['errors'] += 1
                _logger.error(f"Error processing client {client.id}: {str(e)}", exc_info=True)
                continue

        _logger.info(
            f"Duplicate detection completed: "
            f"{total_stats['created']} created, {total_stats['updated']} updated, "
            f"{total_stats['errors']} errors, {total_stats['skipped']} skipped. "
            f"Remaining for next run: {total_stats['remaining']}"
        )

        return total_stats

    @api.model
    def _find_duplicates_for_client(self, client, all_clients, processed_pairs):
        """
        Find duplicates for a single client within the Odoo database.

        Args:
            client: The client record to find duplicates for
            all_clients: Recordset of all clients to search through
            processed_pairs: Set of already processed client pairs

        Returns:
            dict: Statistics for this client
        """
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        client_display = self._get_client_display_name(client)

        # Skip if client has no usable data
        if not client.email and not (client.first_name and client.last_name):
            return stats

        # Find potential duplicates
        duplicates_found = []

        # Rule 1: Exact email match (highest priority)
        if client.email:
            email_duplicates = all_clients.filtered(
                lambda c: c.id != client.id
                          and c.email
                          and c.email.lower() == client.email.lower()
            )
            for dup in email_duplicates:
                pair_key = tuple(sorted([client.id, dup.id]))
                if pair_key not in processed_pairs:
                    duplicates_found.append({
                        'client': dup,
                        'match_type': 'exact_email',
                        'match_score': 100
                    })
                    processed_pairs.add(pair_key)

        # Rule 2: Same first_name + last_name
        if client.first_name and client.last_name:
            name_duplicates = all_clients.filtered(
                lambda c: c.id != client.id
                          and c.first_name
                          and c.last_name
                          and c.first_name.lower().strip() == client.first_name.lower().strip()
                          and c.last_name.lower().strip() == client.last_name.lower().strip()
            )
            for dup in name_duplicates:
                pair_key = tuple(sorted([client.id, dup.id]))
                if pair_key not in processed_pairs:
                    match_type = 'same_name_diff_email'
                    match_score = 90

                    # Check if emails are also similar
                    if client.email and dup.email:
                        if client.email.lower() == dup.email.lower():
                            continue  # Already caught by email rule
                        # Check for similar emails (same local part, different domain)
                        client_local = client.email.split('@')[0].lower()
                        dup_local = dup.email.split('@')[0].lower()
                        if client_local == dup_local:
                            match_type = 'similar_email'
                            match_score = 80

                    duplicates_found.append({
                        'client': dup,
                        'match_type': match_type,
                        'match_score': match_score
                    })
                    processed_pairs.add(pair_key)

        # Rule 3: Similar names (fuzzy matching - simplified)
        if client.first_name and client.last_name:
            # Look for clients with same last name and similar first name
            similar_first = all_clients.filtered(
                lambda c: c.id != client.id
                          and c.last_name
                          and c.first_name
                          and c.last_name.lower().strip() == client.last_name.lower().strip()
                          and c.first_name.lower().strip() != client.first_name.lower().strip()
                          and (
                                  c.first_name.lower().strip()[:3] == client.first_name.lower().strip()[:3]
                                  or client.first_name.lower().strip()[:3] == c.first_name.lower().strip()[:3]
                          )
            )
            for dup in similar_first:
                pair_key = tuple(sorted([client.id, dup.id]))
                if pair_key not in processed_pairs:
                    duplicates_found.append({
                        'client': dup,
                        'match_type': 'similar_name',
                        'match_score': 60
                    })
                    processed_pairs.add(pair_key)

        # Process found duplicates
        if duplicates_found:
            _logger.info(f"Found {len(duplicates_found)} duplicates for {client_display}")

            for dup_data in duplicates_found:
                try:
                    duplicate_client = dup_data['client']

                    # Prepare values
                    duplicate_vals = self._prepare_client_duplicate(
                        original_client=client,
                        duplicate_client=duplicate_client,
                        match_type=dup_data['match_type'],
                        match_score=dup_data['match_score']
                    )

                    # Check if this duplicate pair already exists
                    existing = self.search([
                        ('original_client_id', '=', client.id),
                        ('duplicate_client_id', '=', duplicate_client.id)
                    ], limit=1)

                    if not existing:
                        # Also check reversed pair
                        existing = self.search([
                            ('original_client_id', '=', duplicate_client.id),
                            ('duplicate_client_id', '=', client.id)
                        ], limit=1)

                    if existing:
                        existing.write(duplicate_vals)
                        stats['updated'] += 1
                    else:
                        self.create(duplicate_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error saving duplicate: {str(e)}", exc_info=True)
        else:
            _logger.debug(f"No duplicates found for {client_display}")

        return stats

    @api.model
    def _find_duplicates_manual(self, first_name=None, last_name=None, email=None):
        """
        Manual search for duplicates based on provided parameters.

        Args:
            first_name (str): First name to search
            last_name (str): Last name to search
            email (str): Email to search

        Returns:
            dict: Statistics
        """
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0, 'remaining': 0}

        # Build search domain
        domain = []
        if email:
            domain.append(('email', 'ilike', email))
        if first_name:
            domain.append(('first_name', 'ilike', first_name))
        if last_name:
            domain.append(('last_name', 'ilike', last_name))

        if not domain:
            _logger.warning("No search parameters provided for manual duplicate search")
            return stats

        # Search for matching clients
        matching_clients = self.env['mindbody.client'].search(domain)

        if not matching_clients:
            _logger.info(f"No clients found matching: {first_name} {last_name} ({email})")
            return stats

        _logger.info(f"Found {len(matching_clients)} matching clients")

        # If only one client found, no duplicates
        if len(matching_clients) < 2:
            _logger.info("Only one client found - no duplicates possible")
            return stats

        # Find duplicates among the matching clients
        processed_pairs = set()

        for client in matching_clients:
            # Find duplicates for each client
            client_stats = self._find_duplicates_for_client(
                client,
                matching_clients,
                processed_pairs
            )

            for key in ['created', 'updated', 'errors', 'skipped']:
                stats[key] += client_stats.get(key, 0)

        _logger.info(
            f"Manual duplicate search completed: "
            f"{stats['created']} created, {stats['updated']} updated, "
            f"{stats['errors']} errors, {stats['skipped']} skipped"
        )

        return stats

    # ============================================
    # Utility: Clear all duplicates
    # ============================================

    def clear_all_duplicates(self):
        """Remove all duplicate records"""
        all_records = self.search([])
        count = len(all_records)
        all_records.unlink()
        _logger.info(f"Cleared {count} duplicate records")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Cleared {count} duplicate records',
                'type': 'success',
            }
        }

# import logging
#
# from odoo import models, fields, api
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodyClientDuplicate(models.Model):
#     _name = 'mindbody.client.duplicate'
#     _description = 'Mindbody Client Duplicate'
#
#     client_id = fields.Char(string='Client ID')
#     unique_id = fields.Integer(string='Unique ID')
#     first_name = fields.Char(string='First Name')
#     last_name = fields.Char(string='Last Name')
#     email = fields.Char(string='Email')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     @api.model
#     def _prepare_client_duplicate(self, data):
#         """
#         Prepare client duplicate values from API response.
#
#         Args:
#             data (dict): Client duplicate data from Mindbody API (from /client/clientduplicates endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.client.duplicate create/write
#         """
#         duplicate_vals = {
#             'client_id': data.get('Id'),
#             'unique_id': data.get('UniqueId', 0),
#             'first_name': data.get('FirstName'),
#             'last_name': data.get('LastName'),
#             'email': data.get('Email'),
#         }
#
#         # Remove None values
#         duplicate_vals = {k: v for k, v in duplicate_vals.items() if v is not None}
#
#         return duplicate_vals
#
#     # ============================================
#     # Dummy Data Method
#     # ============================================
#
#     @api.model
#     def _get_dummy_client_duplicates(self):
#         """
#         Return dummy client duplicates data for testing when API returns no data.
#         """
#         # TODO: Replace with real API data when available
#         # API requires: FirstName, LastName, Email parameters
#         # This dummy data is for testing purposes only
#         return {
#             "PaginationResponse": {
#                 "RequestedLimit": 100,
#                 "RequestedOffset": 0,
#                 "PageSize": 10,
#                 "TotalResults": 10
#             },
#             "ClientDuplicates": [
#                 {
#                     "Id": "100000001",
#                     "UniqueId": 1001,
#                     "FirstName": "John",
#                     "LastName": "Smith",
#                     "Email": "john.smith@email.com"
#                 },
#                 {
#                     "Id": "100000002",
#                     "UniqueId": 1002,
#                     "FirstName": "John",
#                     "LastName": "Smith",
#                     "Email": "johnsmith@gmail.com"
#                 },
#                 {
#                     "Id": "100000003",
#                     "UniqueId": 1003,
#                     "FirstName": "Sarah",
#                     "LastName": "Johnson",
#                     "Email": "sarah.johnson@email.com"
#                 },
#                 {
#                     "Id": "100000004",
#                     "UniqueId": 1004,
#                     "FirstName": "Sara",
#                     "LastName": "Johnson",
#                     "Email": "sara.j@email.com"
#                 },
#                 {
#                     "Id": "100000005",
#                     "UniqueId": 1005,
#                     "FirstName": "Michael",
#                     "LastName": "Williams",
#                     "Email": "michael.williams@email.com"
#                 },
#                 {
#                     "Id": "100000006",
#                     "UniqueId": 1006,
#                     "FirstName": "Mike",
#                     "LastName": "Williams",
#                     "Email": "mike.w@email.com"
#                 },
#                 {
#                     "Id": "100000007",
#                     "UniqueId": 1007,
#                     "FirstName": "Jennifer",
#                     "LastName": "Brown",
#                     "Email": "jennifer.brown@email.com"
#                 },
#                 {
#                     "Id": "100000008",
#                     "UniqueId": 1008,
#                     "FirstName": "Jenny",
#                     "LastName": "Brown",
#                     "Email": "jenny.brown@gmail.com"
#                 },
#                 {
#                     "Id": "100000009",
#                     "UniqueId": 1009,
#                     "FirstName": "Robert",
#                     "LastName": "Davis",
#                     "Email": "robert.davis@email.com"
#                 },
#                 {
#                     "Id": "100000010",
#                     "UniqueId": 1010,
#                     "FirstName": "Bob",
#                     "LastName": "Davis",
#                     "Email": "bob.davis@email.com"
#                 }
#             ]
#         }
#
#     # ============================================
#     # Synchronize Method
#     # ============================================
#
#     @api.model
#     def synchronize(self, from_date=None, to_date=None, limit=None, duplicate_ids=None,
#                     first_name=None, last_name=None, email=None):
#         """
#         Synchronize client duplicates from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Maximum number of records to fetch
#             duplicate_ids (list, optional): Not used for this endpoint
#             first_name (str, optional): First name to search duplicates (required by API)
#             last_name (str, optional): Last name to search duplicates (required by API)
#             email (str, optional): Email to search duplicates (required by API)
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             _logger.info("Starting client duplicate sync")
#
#             duplicates_data = []
#             response = {}
#
#             # API requires FirstName, LastName, Email - try if provided
#             if first_name and last_name and email:
#                 params = {
#                     'FirstName': first_name,
#                     'LastName': last_name,
#                     'Email': email
#                 }
#                 if limit:
#                     params['Limit'] = limit
#
#                 try:
#                     response = api.get_client_clientduplicates(params=params)
#                     duplicates_data = response.get('ClientDuplicates', []) if isinstance(response, dict) else []
#                 except Exception as api_error:
#                     _logger.warning(f"API call failed: {str(api_error)}")
#
#             # TODO: Remove dummy data when real API is available
#             # If no data from API or required params not provided, use dummy data
#             if not duplicates_data:
#                 _logger.info("No data from API or required params not provided, using dummy data for testing")
#                 response = self._get_dummy_client_duplicates()
#                 duplicates_data = response.get('ClientDuplicates', [])
#
#             if not duplicates_data:
#                 _logger.info("No client duplicates found to sync")
#                 return stats
#
#             _logger.info(f"Processing {len(duplicates_data)} client duplicates")
#
#             # Process each client duplicate
#             for duplicate_data in duplicates_data:
#                 try:
#                     duplicate_id = duplicate_data.get('Id')
#                     if not duplicate_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping client duplicate without ID")
#                         continue
#
#                     # Check if client duplicate already exists
#                     existing = self.search([('client_id', '=', duplicate_id)], limit=1)
#
#                     # Prepare client duplicate values
#                     duplicate_vals = self._prepare_client_duplicate(duplicate_data)
#
#                     if existing:
#                         existing.write(duplicate_vals)
#                         stats['updated'] += 1
#                         _logger.info(
#                             f"Updated client duplicate {duplicate_id}: {duplicate_data.get('FirstName')} {duplicate_data.get('LastName')}")
#                     else:
#                         self.create(duplicate_vals)
#                         stats['created'] += 1
#                         _logger.info(
#                             f"Created client duplicate {duplicate_id}: {duplicate_data.get('FirstName')} {duplicate_data.get('LastName')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing client duplicate {duplicate_data.get('Id')}: {str(e)}",
#                                   exc_info=True)
#                     continue
#
#             # Save pagination info if available
#             if isinstance(response, dict) and response.get('PaginationResponse'):
#                 pagination = self.env['mindbody.pagination.response']
#                 print(pagination._prepare_pagination_response(response['PaginationResponse']))
#
#             _logger.info(f"Client duplicate sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync client duplicates")
#             stats['errors'] += 1
#             raise UserError(f"Client duplicate sync failed: {str(e)}")
#
#         return stats

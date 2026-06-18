import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyContactLog(models.Model):
    _name = 'mindbody.contact.log'
    _description = 'Mindbody Contact Log'

    client_id = fields.Many2one('mindbody.client', string='Client')

    contact_log_id = fields.Integer(string='Contact Log ID')
    text = fields.Text(string='Text')
    created_date_time = fields.Datetime(string='Created Date Time')
    followup_by_date = fields.Datetime(string='Followup By Date')
    contact_method = fields.Char(string='Contact Method')
    contact_name = fields.Char(string='Contact Name')
    client_obj_id = fields.Many2one('mindbody.client', string='Client Object')
    created_by_id = fields.Many2one('mindbody.staff', string='Created By')
    assigned_to_id = fields.Many2one('mindbody.staff', string='Assigned To')
    comment_ids = fields.One2many('mindbody.contact.log.comment', 'contact_log_id', string='Comments')
    type_ids = fields.One2many('mindbody.contact.log.type', 'contact_log_id', string='Types')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # HELPER: Get client display name for logging
    # ============================================
    # Since mindbody.client has no 'name' field, we build a display string
    # from available fields: display_name, first_name+last_name, or client_id
    def _get_client_display_name(self, client):
        """
        Build a human-readable name for logging purposes.
        mindbody.client has no 'name' field, so we use what's available.

        Priority:
        1. display_name (if set)
        2. first_name + last_name (if either is set)
        3. client_id (the external Mindbody ID - always exists)
        """
        if client.display_name:
            return client.display_name
        if client.first_name or client.last_name:
            parts = [p for p in [client.first_name, client.last_name] if p]
            return ' '.join(parts)
        # Fallback to the external ID - guaranteed to exist since we filter for it
        return f"ID:{client.client_id}"

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_contact_log(self, data):
        """
        Prepare contact log values from API response.
        Converts raw API JSON into Odoo create/write dictionary format.
        """
        self.ensure_one()

        # ============================================
        # STEP 1: Prepare nested One2many records (Comments)
        # ============================================
        # We iterate through the 'Comments' array from API response
        # For each comment, we call its model's prepare method to get valid Odoo vals
        # Then we build an Odoo command tuple: (0, 0, vals) = CREATE new record
        comment_commands = []
        for comment_data in data.get('Comments', []):
            comment_vals = self.env['mindbody.contact.log.comment']._prepare_contact_log_comment(comment_data)
            if comment_vals:
                comment_commands.append((0, 0, comment_vals))

        # ============================================
        # STEP 2: Prepare nested One2many records (Types)
        # ============================================
        # Same logic as comments - iterate Types array and build create commands
        type_commands = []
        for type_data in data.get('Types', []):
            type_vals = self.env['mindbody.contact.log.type']._prepare_contact_log_type(type_data)
            if type_vals:
                type_commands.append((0, 0, type_vals))

        # ============================================
        # STEP 3: Prepare nested Many2one records
        # ============================================
        # These are related objects (Client, Staff, Pagination) that need to be
        # created/linked. We prepare their vals and will embed them as create commands.

        # Prepare the Client linked to this contact log (NOT the same as client_id field)
        # This is the 'Client' object inside the contact log API response
        client_vals = None
        if data.get('Client'):
            client_vals = self.env['mindbody.client']._prepare_client(data['Client'])

        # Prepare the staff member who created this contact log
        created_by_vals = None
        if data.get('CreatedBy'):
            created_by_vals = self.env['mindbody.staff']._prepare_staff(data['CreatedBy'])

        # Prepare the staff member this contact log is assigned to
        assigned_to_vals = None
        if data.get('AssignedTo'):
            assigned_to_vals = self.env['mindbody.staff']._prepare_staff(data['AssignedTo'])

        # Prepare pagination info from API response (for tracking API paging)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        # ============================================
        # STEP 4: Build main contact log values dictionary
        # ============================================
        # This dictionary will be passed to Odoo's create() or write()
        contact_log_vals = {
            'contact_log_id': data.get('Id'),  # External Mindbody ID
            'text': data.get('Text'),  # Log text content
            'created_date_time': data.get('CreatedDateTime'),  # When log was created
            'followup_by_date': data.get('FollowupByDate'),  # Follow-up deadline
            'contact_method': data.get('ContactMethod'),  # How contact was made
            'contact_name': data.get('ContactName'),  # Name of contact

            # One2many fields: pass the list of create commands built above
            # If lists are empty, we set to None so they get filtered out later
            'comment_ids': comment_commands if comment_commands else None,
            'type_ids': type_commands if type_commands else None,
        }

        # ============================================
        # STEP 5: Embed Many2one records as create commands
        # ============================================
        # Format (0, 0, vals) tells Odoo to CREATE a new related record
        # and link it to this Many2one field automatically
        if client_vals:
            contact_log_vals['client_obj_id'] = (0, 0, client_vals)
        if created_by_vals:
            contact_log_vals['created_by_id'] = (0, 0, created_by_vals)
        if assigned_to_vals:
            contact_log_vals['assigned_to_id'] = (0, 0, assigned_to_vals)
        if pagination_vals:
            contact_log_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # ============================================
        # STEP 6: Clean up - remove None/False values
        # ============================================
        # Odoo write() can behave unexpectedly with False values on x2many fields
        # We filter them out to avoid accidentally unlinking existing records
        contact_log_vals = {k: v for k, v in contact_log_vals.items() if v is not None and v is not False}

        return contact_log_vals

    # ============================================
    # SYNCHRONIZATION METHOD - MAIN ENTRY POINT
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, contact_log_ids=None, client_id=None):
        """
        Synchronize contact logs from Mindbody API to Odoo.

        CRITICAL FIX: The Mindbody /client/contactlogs endpoint REQUIRES a ClientId.
        We cannot fetch all contact logs globally. Instead, we iterate through existing
        clients in Odoo and fetch contact logs for each client individually.

        Args:
            from_date (str, optional): Start date filter (YYYY-MM-DD)
            to_date (str, optional): End date filter (YYYY-MM-DD)
            limit (int, optional): Max records per API call
            contact_log_ids (list, optional): Specific contact log IDs to sync
            client_id (int, optional): Sync only ONE specific Odoo client (for manual sync)

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']

        # Stats accumulator across ALL clients
        total_stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # ============================================
        # STEP 1: Determine which clients to sync
        # ============================================
        # We build a domain to search for existing mindbody.clients in Odoo
        # The field is 'client_id' (Char) which stores the external Mindbody ID
        # We only sync clients that HAVE a client_id set (not empty/null)
        # If client_id parameter is passed, we only sync that one client (e.g., from a button)
        client_domain = [('client_id', '!=', False)]
        if client_id:
            client_domain.append(('id', '=', client_id))

        clients = self.env['mindbody.client'].search(client_domain)

        if not clients:
            _logger.warning("No clients found to sync contact logs for")
            return total_stats

        _logger.info(f"Starting contact log sync for {len(clients)} client(s)")

        # ============================================
        # STEP 2: Iterate through each client
        # ============================================
        # We MUST call the API once per client because ClientId is required
        for client in clients:
            # Get the external Mindbody client ID to pass to API
            # client_id is a Char field in mindbody.client model
            mb_client_id = client.client_id

            if not mb_client_id:
                # Use our helper to get a display name for logging (no 'name' field exists)
                client_display = self._get_client_display_name(client)
                _logger.warning(f"Client {client_display} has no Mindbody ID, skipping")
                total_stats['skipped'] += 1
                continue

            # Call the sync method for this single client
            client_stats = self._synchronize_single_client(
                client=client,
                mb_client_id=mb_client_id,
                api=api,
                from_date=from_date,
                to_date=to_date,
                limit=limit,
                contact_log_ids=contact_log_ids
            )

            # Accumulate stats from this client into totals
            for key in total_stats:
                total_stats[key] += client_stats.get(key, 0)

        _logger.info(
            f"Contact log sync completed TOTALS: "
            f"{total_stats['created']} created, {total_stats['updated']} updated, "
            f"{total_stats['errors']} errors, {total_stats['skipped']} skipped"
        )

        return total_stats

    def _synchronize_single_client(self, client, mb_client_id, api, from_date=None, to_date=None, limit=None,
                                   contact_log_ids=None):
        """
        Fetch and sync contact logs for ONE specific client.
        This is extracted as a helper method to keep code clean and handle
        per-client errors without breaking the entire batch.

        CRITICAL: We catch UserError from the API layer because mindbody_api.py
        raises UserError on API failures (400, 401, 403, etc.). If we don't catch
        it here, the entire batch sync would crash on the first failing client.

        Args:
            client (record): The Odoo mindbody.client record
            mb_client_id (str): The external Mindbody client ID (from client_id Char field)
            api (record): The mindbody.api singleton
            from_date, to_date, limit, contact_log_ids: Same as synchronize()

        Returns:
            dict: Stats for this single client only
        """
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # Get a display name for this client for all logging in this method
        # mindbody.client has no 'name' field - we use display_name, first+last, or client_id
        client_display = self._get_client_display_name(client)

        try:
            # ============================================
            # STEP 3: Build API parameters
            # ============================================
            # CRITICAL: ClientId is REQUIRED by Mindbody API
            # We pass the external Mindbody client ID (Char field value)
            # The API expects it as a string
            params = {
                'ClientId': str(mb_client_id)  # Convert to string for API safety
            }

            # Optional filters
            if limit:
                params['Limit'] = limit
            if contact_log_ids:
                params['ContactLogIDs'] = ','.join(map(str, contact_log_ids)) if isinstance(contact_log_ids,
                                                                                            list) else contact_log_ids
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            _logger.info(
                f"Syncing contact logs for client {client_display} (MB ID: {mb_client_id}) with params: {params}")

            # ============================================
            # STEP 4: Call Mindbody API
            # ============================================
            # WARNING: api.get_client_contactlogs() raises UserError on API failure
            # (like 400 InvalidPermissionConfiguration). We MUST catch it here.
            response = api.get_client_contactlogs(params=params)

            # Handle different response formats safely
            contact_logs_data = response.get('ContactLogs', []) if isinstance(response, dict) else []

            if not contact_logs_data:
                _logger.info(f"No contact logs found for client {client_display}")
                return stats

            _logger.info(f"Fetched {len(contact_logs_data)} contact logs for client {client_display}")

            # ============================================
            # STEP 5: Process each contact log
            # ============================================
            for contact_log_data in contact_logs_data:
                try:
                    # Every contact log MUST have an external ID
                    contact_log_id = contact_log_data.get('Id')
                    if not contact_log_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping contact log without ID")
                        continue

                    # ============================================
                    # STEP 6: Check if contact log already exists in Odoo
                    # ============================================
                    # We search by the external contact_log_id field (unique identifier)
                    existing = self.search([('contact_log_id', '=', contact_log_id)], limit=1)

                    # ============================================
                    # STEP 7: Prepare values and link to current client
                    # ============================================
                    # _prepare_contact_log handles nested objects (comments, types, staff)
                    contact_log_vals = self._prepare_contact_log(contact_log_data)

                    # IMPORTANT: Link this contact log to the Odoo client we're iterating
                    # client_id is the Odoo Many2one to mindbody.client
                    # We use the Odoo client's internal database ID (client.id), NOT the external MB ID
                    contact_log_vals['client_id'] = client.id

                    # ============================================
                    # STEP 8: Create or Update
                    # ============================================
                    if existing:
                        existing.write(contact_log_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated contact log {contact_log_id} for client {client_display}")
                    else:
                        self.create(contact_log_vals)
                        stats['created'] += 1
                        _logger.info(f"Created contact log {contact_log_id} for client {client_display}")

                except Exception as e:
                    # Catch per-record errors so one bad log doesn't kill the batch
                    stats['errors'] += 1
                    _logger.error(
                        f"Error processing contact log {contact_log_data.get('Id')} "
                        f"for client {client_display}: {str(e)}",
                        exc_info=True
                    )
                    continue

            # ============================================
            # STEP 9: Save pagination info if present
            # ============================================
            # PaginationResponse helps track if there are more pages to fetch
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse']
                    )
                )

        except UserError as e:
            # ============================================
            # CRITICAL CATCH: API layer raises UserError on HTTP errors
            # ============================================
            # The mindbody_api.py service raises UserError for ANY API failure:
            # - 400 Bad Request (MissingRequiredFields, InvalidPermissionConfiguration)
            # - 401 Unauthorized
            # - 403 Forbidden
            # - 500 Server Error
            #
            # If we don't catch UserError here, the entire synchronize() loop
            # would crash and stop processing remaining clients.
            #
            # Common causes for this specific error:
            # - "InvalidPermissionConfiguration": Your Mindbody API credentials
            #   don't have permission to read contact logs. Check your Mindbody
            #   developer portal > API permissions > ContactLogs access.
            # - "MissingRequiredFields": ClientId was not provided (should not happen now)
            stats['errors'] += 1
            _logger.error(
                f"API permission error for client {client_display} (MB ID: {mb_client_id}): {str(e)}. "
                f"Please check your Mindbody API permissions in the developer portal."
            )

        except Exception as e:
            # Catch any other unexpected errors
            stats['errors'] += 1
            _logger.exception(f"Unexpected error syncing contact logs for client {client_display}")

        return stats

# import logging
#
# from odoo import models, fields
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodyContactLog(models.Model):
#     _name = 'mindbody.contact.log'
#     _description = 'Mindbody Contact Log'
#
#     client_id = fields.Many2one('mindbody.client', string='Client')
#
#     contact_log_id = fields.Integer(string='Contact Log ID')
#     text = fields.Text(string='Text')
#     created_date_time = fields.Datetime(string='Created Date Time')
#     followup_by_date = fields.Datetime(string='Followup By Date')
#     contact_method = fields.Char(string='Contact Method')
#     contact_name = fields.Char(string='Contact Name')
#     client_obj_id = fields.Many2one('mindbody.client', string='Client Object')
#     created_by_id = fields.Many2one('mindbody.staff', string='Created By')
#     assigned_to_id = fields.Many2one('mindbody.staff', string='Assigned To')
#     comment_ids = fields.One2many('mindbody.contact.log.comment', 'contact_log_id', string='Comments')
#     type_ids = fields.One2many('mindbody.contact.log.type', 'contact_log_id', string='Types')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # mindbody_contact_log.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_contact_log(self, data):
#         """
#         Prepare contact log values from API response.
#
#         Args:
#             data (dict): Contact log data from Mindbody API (from /client/contactlogs endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.contact.log create/write
#         """
#         self.ensure_one()
#
#         # Prepare comments (One2many)
#         comment_commands = []
#         for comment_data in data.get('Comments', []):
#             comment_vals = self.env['mindbody.contact.log.comment']._prepare_contact_log_comment(comment_data)
#             if comment_vals:
#                 comment_commands.append((0, 0, comment_vals))
#
#         # Prepare types (One2many)
#         type_commands = []
#         for type_data in data.get('Types', []):
#             type_vals = self.env['mindbody.contact.log.type']._prepare_contact_log_type(type_data)
#             if type_vals:
#                 type_commands.append((0, 0, type_vals))
#
#         # Prepare client (Many2one)
#         client_vals = None
#         if data.get('Client'):
#             client_vals = self.env['mindbody.client']._prepare_client(data['Client'])
#
#         # Prepare created by (Many2one)
#         created_by_vals = None
#         if data.get('CreatedBy'):
#             created_by_vals = self.env['mindbody.staff']._prepare_staff(data['CreatedBy'])
#
#         # Prepare assigned to (Many2one)
#         assigned_to_vals = None
#         if data.get('AssignedTo'):
#             assigned_to_vals = self.env['mindbody.staff']._prepare_staff(data['AssignedTo'])
#
#         # Prepare pagination (Many2one)
#         pagination_vals = None
#         if data.get('PaginationResponse'):
#             pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
#                 data['PaginationResponse']
#             )
#
#         contact_log_vals = {
#             'contact_log_id': data.get('Id'),
#             'text': data.get('Text'),
#             'created_date_time': data.get('CreatedDateTime'),
#             'followup_by_date': data.get('FollowupByDate'),
#             'contact_method': data.get('ContactMethod'),
#             'contact_name': data.get('ContactName'),
#
#             # One2many fields
#             'comment_ids': comment_commands if comment_commands else None,
#             'type_ids': type_commands if type_commands else None,
#         }
#
#         # Add Many2one fields with create commands
#         if client_vals:
#             contact_log_vals['client_obj_id'] = (0, 0, client_vals)
#         if created_by_vals:
#             contact_log_vals['created_by_id'] = (0, 0, created_by_vals)
#         if assigned_to_vals:
#             contact_log_vals['assigned_to_id'] = (0, 0, assigned_to_vals)
#         if pagination_vals:
#             contact_log_vals['pagination_response_id'] = (0, 0, pagination_vals)
#
#         # Remove None values
#         contact_log_vals = {k: v for k, v in contact_log_vals.items() if v is not None and v is not False}
#
#         return contact_log_vals
#
#     # mindbody_contact_log.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, contact_log_ids=None):
#         """
#         Synchronize contact logs from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Start date for contact logs
#             to_date (str, optional): End date for contact logs
#             limit (int, optional): Maximum number of records to fetch
#             contact_log_ids (list, optional): Specific contact log IDs to sync
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             # Prepare parameters
#             params = {}
#             if limit:
#                 params['Limit'] = limit
#             if contact_log_ids:
#                 params['ContactLogIDs'] = ','.join(map(str, contact_log_ids)) if isinstance(contact_log_ids,
#                                                                                             list) else contact_log_ids
#             if from_date:
#                 params['StartDate'] = from_date
#                 if to_date:
#                     params['EndDate'] = to_date
#
#             _logger.info(f"Starting contact log sync with params: {params}")
#
#             # Fetch contact logs from Mindbody API
#             response = api.get_client_contactlogs(params=params)
#             contact_logs_data = response.get('ContactLogs', []) if isinstance(response, dict) else []
#             print(contact_logs_data)
#             if not contact_logs_data:
#                 _logger.info("No contact logs found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(contact_logs_data)} contact logs from Mindbody")
#
#             # Process each contact log
#             for contact_log_data in contact_logs_data:
#                 try:
#                     contact_log_id = contact_log_data.get('Id')
#                     if not contact_log_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping contact log without ID")
#                         continue
#
#                     # Check if contact log already exists
#                     existing = self.search([('contact_log_id', '=', contact_log_id)], limit=1)
#
#                     # Prepare contact log values
#                     contact_log_vals = self._prepare_contact_log(contact_log_data)
#
#                     if existing:
#                         existing.write(contact_log_vals)
#                         stats['updated'] += 1
#                         _logger.info(f"Updated contact log {contact_log_id}")
#                     else:
#                         self.create(contact_log_vals)
#                         stats['created'] += 1
#                         _logger.info(f"Created contact log {contact_log_id}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing contact log {contact_log_data.get('Id')}: {str(e)}", exc_info=True)
#                     continue
#
#             # Save pagination info if available
#             if isinstance(response, dict) and response.get('PaginationResponse'):
#                 self.env['mindbody.pagination.response'].create(
#                     self.env['mindbody.pagination.response']._prepare_pagination_response(
#                         response['PaginationResponse'])
#                 )
#
#             _logger.info(f"Contact log sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync contact logs")
#             stats['errors'] += 1
#             raise UserError(f"Contact log sync failed: {str(e)}")
#
#         return stats

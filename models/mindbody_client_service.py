import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyClientService(models.Model):
    _name = 'mindbody.client.service'
    _description = 'Mindbody Client Service'

    client_id = fields.Many2one('mindbody.client', string='Client')
    service_id = fields.Many2one('mindbody.service', string='Service')

    activation_type = fields.Selection([
        ('OnFirstVisit', 'On First Visit'),
        ('OnPurchase', 'On Purchase')
    ], string='Activation Type')
    cannot_pay_for_classes_before_activation = fields.Boolean(string='Cannot Pay For Classes Before Activation')
    active_date = fields.Datetime(string='Active Date')
    count = fields.Integer(string='Count')
    current = fields.Boolean(string='Current')
    expiration_date = fields.Datetime(string='Expiration Date')
    client_service_id = fields.Integer(string='Client Service ID')
    product_id = fields.Integer(string='Product ID')
    name = fields.Char(string='Name')
    payment_date = fields.Datetime(string='Payment Date')
    program_id_ref = fields.Many2one('mindbody.program', string='Program')
    remaining = fields.Integer(string='Remaining')
    site_id = fields.Integer(string='Site ID')
    action = fields.Selection([
        ('None', 'None'),
        ('Added', 'Added'),
        ('Updated', 'Updated'),
        ('Failed', 'Failed'),
        ('Removed', 'Removed')
    ], string='Action', default='None')
    client_id_str = fields.Char(string='Client ID String')
    returned = fields.Boolean(string='Returned')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # Prepare Methods
    # ============================================

    @api.model
    def _prepare_client_service(self, data):
        """
        Prepare client service values from API response.
        """
        # Handle Program (Many2one)
        program_id = False
        if data.get('Program'):
            program_data = data['Program']
            program_mb_id = program_data.get('Id')
            if program_mb_id:
                existing_program = self.env['mindbody.program'].search(
                    [('program_id', '=', program_mb_id)], limit=1
                )
                if existing_program:
                    program_id = existing_program.id
                else:
                    # Create program if not exists
                    try:
                        program_vals = self.env['mindbody.program']._prepare_program(program_data)
                        new_program = self.env['mindbody.program'].create(program_vals)
                        program_id = new_program.id
                    except Exception as e:
                        _logger.warning(f"Could not create program: {e}")

        # Link to client if ClientID exists
        client_id = False
        if data.get('ClientID'):
            client = self.env['mindbody.client'].search(
                [('client_id', '=', data['ClientID'])], limit=1
            )
            if client:
                client_id = client.id

        client_service_vals = {
            'activation_type': data.get('ActivationType'),
            'cannot_pay_for_classes_before_activation': data.get('CannotPayForClassesBeforeActivation', False),
            'active_date': data.get('ActiveDate'),
            'count': data.get('Count', 0),
            'current': data.get('Current', False),
            'expiration_date': data.get('ExpirationDate'),
            'client_service_id': data.get('Id'),
            'product_id': data.get('ProductId'),
            'name': data.get('Name'),
            'payment_date': data.get('PaymentDate'),
            'remaining': data.get('Remaining', 0),
            'site_id': data.get('SiteId'),
            'action': data.get('Action', 'None'),
            'client_id_str': data.get('ClientID'),
            'returned': data.get('Returned', False),
        }

        if program_id:
            client_service_vals['program_id_ref'] = program_id

        if client_id:
            client_service_vals['client_id'] = client_id

        # Remove None values
        client_service_vals = {k: v for k, v in client_service_vals.items() if v is not None}

        return client_service_vals

    # ============================================
    # Synchronize Method
    # ============================================

    @api.model
    def synchronize(self, from_date=None, to_date=None, limit=None, client_service_ids=None, client_id=None):
        """
        Synchronize client services from Mindbody to Odoo.

        Note: Mindbody API requires at least one of: ClientId, UniqueClientId, ClientIds, UniqueClientIds
        If no client_id is provided, services will be synced for ALL clients.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # ============================================
        # STEP A: Determine which clients to sync
        # ============================================
        client_ids_to_sync = []

        if client_id:
            # Single client specified
            client_ids_to_sync = [client_id]
        else:
            # No client specified - get ALL clients from Odoo
            _logger.info("No client_id provided. Fetching all clients to sync their services...")
            all_clients = self.env['mindbody.client'].search([])
            client_ids_to_sync = [c.client_id for c in all_clients if c.client_id]
            _logger.info(f"Found {len(client_ids_to_sync)} clients to sync services for")

        if not client_ids_to_sync:
            _logger.warning("No clients found to sync services for")
            return stats

        # ============================================
        # STEP B: Sync services for each client
        # ============================================
        for current_client_id in client_ids_to_sync:
            try:
                client_stats = self._sync_services_for_client(
                    api=api,
                    client_id=current_client_id,
                    from_date=from_date,
                    to_date=to_date,
                    limit=limit,
                    client_service_ids=client_service_ids,
                )
                # Accumulate stats
                stats['created'] += client_stats['created']
                stats['updated'] += client_stats['updated']
                stats['errors'] += client_stats['errors']
                stats['skipped'] += client_stats['skipped']

            except Exception as e:
                _logger.error(f"Error syncing services for client {current_client_id}: {str(e)}")
                stats['errors'] += 1
                continue

        _logger.info(f"Client service sync completed: {stats['created']} created, {stats['updated']} updated, "
                     f"{stats['errors']} errors, {stats['skipped']} skipped")

        return stats

    def _sync_services_for_client(self, api, client_id, from_date=None, to_date=None, limit=None,
                                  client_service_ids=None):
        """
        Sync services for a SINGLE client with pagination.
        """
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        offset = 0
        page_size = limit if limit else 100
        has_more = True

        try:
            while has_more:
                params = {
                    'ClientId': client_id,
                    'Limit': page_size,
                    'Offset': offset,
                }

                if client_service_ids:
                    params['ClientServiceIds'] = ','.join(map(str, client_service_ids)) if isinstance(
                        client_service_ids, list) else client_service_ids
                if from_date:
                    params['StartDate'] = from_date
                    if to_date:
                        params['EndDate'] = to_date

                _logger.info(f"Fetching services for client {client_id}, offset={offset}")

                response = api.get_client_clientservices(params=params)

                if isinstance(response, dict):
                    services_data = response.get('ClientServices', [])
                else:
                    services_data = response if response else []

                if not services_data:
                    break

                _logger.info(f"Got {len(services_data)} services for client {client_id}")

                for service_data in services_data:
                    try:
                        service_id = service_data.get('Id')
                        if not service_id:
                            stats['skipped'] += 1
                            continue

                        existing = self.search([('client_service_id', '=', service_id)], limit=1)
                        service_vals = self._prepare_client_service(service_data)

                        if existing:
                            existing.write(service_vals)
                            stats['updated'] += 1
                        else:
                            self.create(service_vals)
                            stats['created'] += 1

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing service {service_data.get('Id')}: {str(e)}")
                        continue

                # Pagination check
                if len(services_data) < page_size:
                    has_more = False

                    # Save pagination info
                    if isinstance(response, dict) and response.get('PaginationResponse'):
                        pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                            response['PaginationResponse']
                        )
                        if pagination_vals:
                            self.env['mindbody.pagination.response'].create(pagination_vals)
                else:
                    offset += page_size

        except Exception as e:
            _logger.error(f"API error for client {client_id}: {str(e)}")
            stats['errors'] += 1

        return stats

# import logging
#
# from odoo import models, fields, api
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodyClientService(models.Model):
#     _name = 'mindbody.client.service'
#     _description = 'Mindbody Client Service'
#
#     client_id = fields.Many2one('mindbody.client', string='Client')
#     service_id = fields.Many2one('mindbody.service', string='Service')
#
#     activation_type = fields.Selection([
#         ('OnFirstVisit', 'On First Visit'),
#         ('OnPurchase', 'On Purchase')
#     ], string='Activation Type')
#     cannot_pay_for_classes_before_activation = fields.Boolean(string='Cannot Pay For Classes Before Activation')
#     active_date = fields.Datetime(string='Active Date')
#     count = fields.Integer(string='Count')
#     current = fields.Boolean(string='Current')
#     expiration_date = fields.Datetime(string='Expiration Date')
#     client_service_id = fields.Integer(string='Client Service ID')
#     product_id = fields.Integer(string='Product ID')
#     name = fields.Char(string='Name')
#     payment_date = fields.Datetime(string='Payment Date')
#     program_id_ref = fields.Many2one('mindbody.program', string='Program')
#     remaining = fields.Integer(string='Remaining')
#     site_id = fields.Integer(string='Site ID')
#     action = fields.Selection([
#         ('None', 'None'),
#         ('Added', 'Added'),
#         ('Updated', 'Updated'),
#         ('Failed', 'Failed'),
#         ('Removed', 'Removed')
#     ], string='Action', default='None')
#     client_id_str = fields.Char(string='Client ID String')
#     returned = fields.Boolean(string='Returned')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     @api.model
#     def _prepare_client_service(self, data):
#         """
#         Prepare client service values from API response.
#         """
#         # Handle Program (Many2one)
#         program_id = False
#         if data.get('Program'):
#             program_data = data['Program']
#             program_mb_id = program_data.get('Id')
#             if program_mb_id:
#                 existing_program = self.env['mindbody.program'].search(
#                     [('program_id', '=', program_mb_id)], limit=1
#                 )
#                 if existing_program:
#                     program_id = existing_program.id
#                 else:
#                     # Create program if not exists
#                     try:
#                         program_vals = self.env['mindbody.program']._prepare_program(program_data)
#                         new_program = self.env['mindbody.program'].create(program_vals)
#                         program_id = new_program.id
#                     except Exception as e:
#                         _logger.warning(f"Could not create program: {e}")
#
#         # Link to client if ClientID exists
#         client_id = False
#         if data.get('ClientID'):
#             client = self.env['mindbody.client'].search(
#                 [('client_id', '=', data['ClientID'])], limit=1
#             )
#             if client:
#                 client_id = client.id
#
#         client_service_vals = {
#             'activation_type': data.get('ActivationType'),
#             'cannot_pay_for_classes_before_activation': data.get('CannotPayForClassesBeforeActivation', False),
#             'active_date': data.get('ActiveDate'),
#             'count': data.get('Count', 0),
#             'current': data.get('Current', False),
#             'expiration_date': data.get('ExpirationDate'),
#             'client_service_id': data.get('Id'),
#             'product_id': data.get('ProductId'),
#             'name': data.get('Name'),
#             'payment_date': data.get('PaymentDate'),
#             'remaining': data.get('Remaining', 0),
#             'site_id': data.get('SiteId'),
#             'action': data.get('Action', 'None'),
#             'client_id_str': data.get('ClientID'),
#             'returned': data.get('Returned', False),
#         }
#
#         if program_id:
#             client_service_vals['program_id_ref'] = program_id
#
#         if client_id:
#             client_service_vals['client_id'] = client_id
#
#         # Remove None values
#         client_service_vals = {k: v for k, v in client_service_vals.items() if v is not None}
#
#         return client_service_vals
#
#     # ============================================
#     # Dummy Data Method
#     # ============================================
#
#     @api.model
#     def _get_dummy_client_services(self):
#         """
#         Return dummy client services data for testing when API returns no data.
#         """
#         return {
#             "PaginationResponse": {
#                 "RequestedLimit": 100,
#                 "RequestedOffset": 0,
#                 "PageSize": 10,
#                 "TotalResults": 10
#             },
#             "ClientServices": [
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2025-01-01T10:00:00Z",
#                     "Count": 10,
#                     "Current": True,
#                     "ExpirationDate": "2025-06-01T10:00:00Z",
#                     "Id": 1001,
#                     "ProductId": 501,
#                     "Name": "10 Class Pack - Yoga",
#                     "PaymentDate": "2025-01-01T10:00:00Z",
#                     "Program": {
#                         "Id": 1,
#                         "Name": "Yoga Classes",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 24
#                     },
#                     "Remaining": 7,
#                     "SiteId": 12345,
#                     "Action": "None",
#                     "ClientID": "100000001",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnFirstVisit",
#                     "CannotPayForClassesBeforeActivation": True,
#                     "ActiveDate": "2025-02-15T10:00:00Z",
#                     "Count": 20,
#                     "Current": True,
#                     "ExpirationDate": "2025-08-15T10:00:00Z",
#                     "Id": 1002,
#                     "ProductId": 502,
#                     "Name": "20 Class Pack - Pilates",
#                     "PaymentDate": "2025-02-10T10:00:00Z",
#                     "Program": {
#                         "Id": 2,
#                         "Name": "Pilates Classes",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 12
#                     },
#                     "Remaining": 20,
#                     "SiteId": 12345,
#                     "Action": "Added",
#                     "ClientID": "100000002",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2024-10-01T10:00:00Z",
#                     "Count": 5,
#                     "Current": False,
#                     "ExpirationDate": "2025-01-01T10:00:00Z",
#                     "Id": 1003,
#                     "ProductId": 503,
#                     "Name": "5 Class Pack - HIIT",
#                     "PaymentDate": "2024-10-01T10:00:00Z",
#                     "Program": {
#                         "Id": 3,
#                         "Name": "HIIT Training",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 6
#                     },
#                     "Remaining": 2,
#                     "SiteId": 12345,
#                     "Action": "None",
#                     "ClientID": "100000003",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2024-12-01T10:00:00Z",
#                     "Count": 30,
#                     "Current": True,
#                     "ExpirationDate": "2025-05-01T10:00:00Z",
#                     "Id": 1004,
#                     "ProductId": 504,
#                     "Name": "Monthly Unlimited - Gold",
#                     "PaymentDate": "2024-12-01T10:00:00Z",
#                     "Program": {
#                         "Id": 4,
#                         "Name": "Unlimited Membership",
#                         "ScheduleType": "All",
#                         "CancelOffset": 24
#                     },
#                     "Remaining": 15,
#                     "SiteId": 12345,
#                     "Action": "Updated",
#                     "ClientID": "100000004",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2025-01-15T10:00:00Z",
#                     "Count": 8,
#                     "Current": True,
#                     "ExpirationDate": "2025-07-15T10:00:00Z",
#                     "Id": 1005,
#                     "ProductId": 505,
#                     "Name": "8 Class Pack - Spinning",
#                     "PaymentDate": "2025-01-15T10:00:00Z",
#                     "Program": {
#                         "Id": 5,
#                         "Name": "Spinning Classes",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 4
#                     },
#                     "Remaining": 5,
#                     "SiteId": 12345,
#                     "Action": "None",
#                     "ClientID": "100000005",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2024-11-15T10:00:00Z",
#                     "Count": 12,
#                     "Current": False,
#                     "ExpirationDate": "2025-04-15T10:00:00Z",
#                     "Id": 1006,
#                     "ProductId": 506,
#                     "Name": "12 Class Pack - Zumba",
#                     "PaymentDate": "2024-11-15T10:00:00Z",
#                     "Program": {
#                         "Id": 6,
#                         "Name": "Zumba Classes",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 2
#                     },
#                     "Remaining": 0,
#                     "SiteId": 12345,
#                     "Action": "None",
#                     "ClientID": "100000001",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnFirstVisit",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": None,
#                     "Count": 15,
#                     "Current": True,
#                     "ExpirationDate": "2025-09-01T10:00:00Z",
#                     "Id": 1007,
#                     "ProductId": 507,
#                     "Name": "15 Class Pack - Boxing",
#                     "PaymentDate": "2025-02-01T10:00:00Z",
#                     "Program": {
#                         "Id": 7,
#                         "Name": "Boxing Classes",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 6
#                     },
#                     "Remaining": 15,
#                     "SiteId": 12345,
#                     "Action": "Added",
#                     "ClientID": "100000006",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": True,
#                     "ActiveDate": "2025-01-10T10:00:00Z",
#                     "Count": 4,
#                     "Current": True,
#                     "ExpirationDate": "2025-07-10T10:00:00Z",
#                     "Id": 1008,
#                     "ProductId": 508,
#                     "Name": "4 Personal Training Sessions",
#                     "PaymentDate": "2025-01-10T10:00:00Z",
#                     "Program": {
#                         "Id": 8,
#                         "Name": "Personal Training",
#                         "ScheduleType": "Appointment",
#                         "CancelOffset": 24
#                     },
#                     "Remaining": 3,
#                     "SiteId": 12345,
#                     "Action": "None",
#                     "ClientID": "100000007",
#                     "Returned": False
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2025-01-20T10:00:00Z",
#                     "Count": 6,
#                     "Current": False,
#                     "ExpirationDate": "2025-06-20T10:00:00Z",
#                     "Id": 1009,
#                     "ProductId": 509,
#                     "Name": "6 Class Pack - Meditation",
#                     "PaymentDate": "2025-01-20T10:00:00Z",
#                     "Program": {
#                         "Id": 9,
#                         "Name": "Meditation & Wellness",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 1
#                     },
#                     "Remaining": 6,
#                     "SiteId": 12345,
#                     "Action": "None",
#                     "ClientID": "100000008",
#                     "Returned": True
#                 },
#                 {
#                     "ActivationType": "OnPurchase",
#                     "CannotPayForClassesBeforeActivation": False,
#                     "ActiveDate": "2025-01-25T10:00:00Z",
#                     "Count": 25,
#                     "Current": True,
#                     "ExpirationDate": "2025-07-25T10:00:00Z",
#                     "Id": 1010,
#                     "ProductId": 510,
#                     "Name": "25 Class Pack - CrossFit",
#                     "PaymentDate": "2025-01-25T10:00:00Z",
#                     "Program": {
#                         "Id": 10,
#                         "Name": "CrossFit Training",
#                         "ScheduleType": "Class",
#                         "CancelOffset": 12
#                     },
#                     "Remaining": 23,
#                     "SiteId": 12345,
#                     "Action": "Added",
#                     "ClientID": "100000009",
#                     "Returned": False
#                 }
#             ]
#         }
#
#     # ============================================
#     # Synchronize Method - Called from Button
#     # ============================================
#
#     @api.model
#     def synchronize(self, from_date=None, to_date=None, limit=None, client_service_ids=None, client_id=None):
#         """
#         Synchronize client services from Mindbody to Odoo.
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             _logger.info("Starting client service sync")
#
#             services_data = []
#             response = {}
#
#             # If specific client_id provided, call API
#             if client_id:
#                 params = {'ClientId': client_id}
#                 if limit:
#                     params['Limit'] = limit
#
#                 try:
#                     response = api.get_client_clientservices(params=params)
#                     services_data = response.get('ClientServices', []) if isinstance(response, dict) else []
#                 except Exception as api_error:
#                     _logger.warning(f"API call failed for client {client_id}: {str(api_error)}")
#
#             # If no data from API or no client_id, use dummy data
#             if not services_data:
#                 _logger.info("No data from API or no ClientId provided, using dummy data for testing")
#                 response = self._get_dummy_client_services()
#                 services_data = response.get('ClientServices', [])
#
#             if not services_data:
#                 _logger.info("No client services found to sync")
#                 return stats
#
#             _logger.info(f"Processing {len(services_data)} client services")
#
#             # Process each client service
#             for service_data in services_data:
#                 try:
#                     service_id = service_data.get('Id')
#                     if not service_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping client service without ID")
#                         continue
#
#                     # Check if client service already exists
#                     existing = self.search([('client_service_id', '=', service_id)], limit=1)
#
#                     # Prepare client service values
#                     service_vals = self._prepare_client_service(service_data)
#
#                     if existing:
#                         existing.write(service_vals)
#                         stats['updated'] += 1
#                         _logger.info(f"Updated client service {service_id}: {service_data.get('Name')}")
#                     else:
#                         self.create(service_vals)
#                         stats['created'] += 1
#                         _logger.info(f"Created client service {service_id}: {service_data.get('Name')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing client service {service_data.get('Id')}: {str(e)}",
#                                   exc_info=True)
#                     continue
#
#             # Save pagination info if available
#             if isinstance(response, dict) and response.get('PaginationResponse'):
#                 pagination = self.env['mindbody.pagination.response']
#                 print(pagination._prepare_pagination_response(response['PaginationResponse']))
#
#             _logger.info(f"Client service sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync client services")
#             stats['errors'] += 1
#             raise UserError(f"Client service sync failed: {str(e)}")
#
#         return stats

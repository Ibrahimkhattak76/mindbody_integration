import logging
from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyClientMembership(models.Model):
    _name = 'mindbody.client.membership'
    _description = 'Mindbody Client Membership'

    client_id = fields.Many2one('mindbody.client', string='Client')
    membership_id = fields.Many2one('mindbody.membership', string='Membership')

    restricted_location_ids = fields.Many2many('mindbody.location', string='Restricted Locations')
    icon_code = fields.Char()
    membership_id_int = fields.Integer()
    active_date = fields.Datetime()
    count = fields.Integer()
    current = fields.Boolean()
    expiration_date = fields.Datetime()
    client_membership_id = fields.Integer()
    product_id = fields.Integer()
    name = fields.Char()
    payment_date = fields.Datetime()
    program_id_ref = fields.Many2one('mindbody.program')
    remaining = fields.Integer()
    site_id = fields.Integer()
    action = fields.Selection([
        ('None', 'None'),
        ('Added', 'Added'),
        ('Updated', 'Updated'),
        ('Removed', 'Removed')
    ], default='None')

    client_id_str = fields.Char()
    returned = fields.Boolean()
    pagination_response_id = fields.Many2one('mindbody.pagination.response')
    error_message = fields.Char()

    # =========================================================
    # PREPARE DATA
    # =========================================================
    def _prepare_client_membership(self, data):

        program_vals = None
        if data.get('Program'):
            program_vals = self.env['mindbody.program']._prepare_program(data['Program'])

        location_commands = []
        for loc in data.get('RestrictedLocations', []):
            vals = self.env['mindbody.location']._prepare_location(loc)
            if vals:
                existing = self.env['mindbody.location'].search([
                    ('location_id', '=', loc.get('Id'))
                ], limit=1)

                if existing:
                    location_commands.append((4, existing.id))
                else:
                    location_commands.append((0, 0, vals))

        vals = {
            'icon_code': data.get('IconCode'),
            'membership_id_int': data.get('MembershipId'),
            'active_date': data.get('ActiveDate'),
            'count': data.get('Count', 0),
            'current': data.get('Current', False),
            'expiration_date': data.get('ExpirationDate'),
            'client_membership_id': data.get('Id'),
            'product_id': data.get('ProductId'),
            'name': data.get('Name'),
            'payment_date': data.get('PaymentDate'),
            'remaining': data.get('Remaining', 0),
            'site_id': data.get('SiteId'),
            'action': data.get('Action', 'None'),
            'client_id_str': data.get('ClientID'),
            'returned': data.get('Returned', False),
            'error_message': data.get('ErrorMessage'),
            'restricted_location_ids': location_commands or [(5, 0, 0)],
        }

        if program_vals:
            vals['program_id_ref'] = (0, 0, program_vals)

        return {k: v for k, v in vals.items() if v is not None}

    # =========================================================
    # FULL SYNC (FIXED + DEBUG MODE)
    # =========================================================
    def synchronize(self, from_date=None, to_date=None, limit=100):

        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            # =====================================================
            # STEP 1: GET ALL CLIENTS FROM ODOO
            # =====================================================
            clients = self.env['mindbody.client'].search([])

            if not clients:
                raise UserError("No clients found in Odoo")

            _logger.info(f"TOTAL ODOO CLIENTS FOUND: {len(clients)}")

            # =====================================================
            # STEP 2: PROCESS IN SMALL BATCHES (avoid timeout)
            # =====================================================
            BATCH_SIZE = 10

            for i in range(0, len(clients), BATCH_SIZE):
                batch = clients[i:i + BATCH_SIZE]

                _logger.info(f"PROCESSING BATCH: {i} -> {i + BATCH_SIZE}")

                for client in batch:

                    # =================================================
                    # ACTUAL CLIENT ID USED FOR API
                    # (THIS IS THE REAL MINDBODY CLIENT ID)
                    # =================================================
                    client_id = client.client_id

                    if not client_id:
                        _logger.warning(f"Skipping client with missing ID: {client.name}")
                        continue

                    # ensure int
                    try:
                        client_id = int(client_id)
                    except Exception:
                        _logger.warning(f"Invalid ClientId: {client_id}")
                        continue

                    # =================================================
                    # REQUEST SENT TO MINDBODY API
                    # =================================================
                    params = {
                        'ClientId': client_id,
                        'Limit': limit  # membership page size
                    }

                    if from_date and to_date:
                        params['ModifiedDateTime'] = f"{from_date}|{to_date}"

                    _logger.info(f"[REQUEST ? MINDBODY] {params}")

                    # =================================================
                    # API CALL
                    # =================================================
                    try:
                        response = api.get_client_activeclientmemberships(params=params)

                    except Exception as e:
                        _logger.error(f"API ERROR for {client_id}: {e}")
                        stats['errors'] += 1
                        continue

                    # =================================================
                    # RAW RESPONSE LOG (IMPORTANT)
                    # =================================================
                    _logger.info(f"[RESPONSE ? MINDBODY {client_id}] {response}")

                    memberships = response.get('ClientMemberships', [])

                    if not memberships:
                        _logger.warning(f"No memberships for ClientId {client_id}")
                        continue

                    # =================================================
                    # PROCESS MEMBERSHIPS
                    # =================================================
                    for m in memberships:
                        try:
                            vals = self._prepare_client_membership(m)

                            existing = self.search([
                                ('client_membership_id', '=', m.get('Id'))
                            ], limit=1)

                            if existing:
                                existing.write(vals)
                                stats['updated'] += 1
                            else:
                                self.create(vals)
                                stats['created'] += 1

                        except Exception as e:
                            _logger.exception(f"Error processing membership {m.get('Id')}: {e}")
                            stats['errors'] += 1

            _logger.info(f"SYNC COMPLETED: {stats}")
            return stats

        except Exception as e:
            _logger.exception("FULL SYNC FAILED")
            raise UserError(f"Client membership sync failed: {str(e)}")

# import logging
# from odoo import models, fields
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodyClientMembership(models.Model):
#     _name = 'mindbody.client.membership'
#     _description = 'Mindbody Client Membership'
#
#     client_id = fields.Many2one('mindbody.client', string='Client')
#     membership_id = fields.Many2one('mindbody.membership', string='Membership')
#
#     restricted_location_ids = fields.Many2many('mindbody.location', string='Restricted Locations')
#     icon_code = fields.Char(string='Icon Code')
#     membership_id_int = fields.Integer(string='Membership ID')
#     active_date = fields.Datetime(string='Active Date')
#     count = fields.Integer(string='Count')
#     current = fields.Boolean(string='Current')
#     expiration_date = fields.Datetime(string='Expiration Date')
#     client_membership_id = fields.Integer(string='Client Membership ID')
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
#         ('Removed', 'Removed')
#     ], default='None')
#     client_id_str = fields.Char(string='Client ID String')
#     returned = fields.Boolean(string='Returned')
#     pagination_response_id = fields.Many2one('mindbody.pagination.response')
#     error_message = fields.Char(string='Error Message')
#
#     # =========================================================
#     # PREPARE DATA
#     # =========================================================
#     def _prepare_client_membership(self, data):
#
#         program_vals = None
#         if data.get('Program'):
#             program_vals = self.env['mindbody.program']._prepare_program(data['Program'])
#
#         location_commands = []
#         for loc in data.get('RestrictedLocations', []):
#             vals = self.env['mindbody.location']._prepare_location(loc)
#             if vals:
#                 existing = self.env['mindbody.location'].search([
#                     ('location_id', '=', loc.get('Id'))
#                 ], limit=1)
#
#                 if existing:
#                     location_commands.append((4, existing.id))
#                 else:
#                     location_commands.append((0, 0, vals))
#
#         vals = {
#             'icon_code': data.get('IconCode'),
#             'membership_id_int': data.get('MembershipId'),
#             'active_date': data.get('ActiveDate'),
#             'count': data.get('Count', 0),
#             'current': data.get('Current', False),
#             'expiration_date': data.get('ExpirationDate'),
#             'client_membership_id': data.get('Id'),
#             'product_id': data.get('ProductId'),
#             'name': data.get('Name'),
#             'payment_date': data.get('PaymentDate'),
#             'remaining': data.get('Remaining', 0),
#             'site_id': data.get('SiteId'),
#             'action': data.get('Action', 'None'),
#             'client_id_str': data.get('ClientID'),
#             'returned': data.get('Returned', False),
#             'error_message': data.get('ErrorMessage'),
#             'restricted_location_ids': location_commands or [(5, 0, 0)],
#         }
#
#         if program_vals:
#             vals['program_id_ref'] = (0, 0, program_vals)
#
#         return {k: v for k, v in vals.items() if v is not None}
#
#     # =========================================================
#     #             SYNC FUNCTION
#     # =========================================================
#     def synchronize(self, from_date=None, to_date=None, limit=None, client_membership_ids=None):
#
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#
#             # =====================================================
#             # : fallback if no clients provided
#             # =====================================================
#             if not client_membership_ids:
#                 clients = self.env['mindbody.client'].search([])
#                 client_membership_ids = clients.mapped('client_id')
#
#             # safety check
#             if not client_membership_ids:
#                 raise UserError("No Client IDs found for Mindbody sync")
#
#             # ensure list
#             if not isinstance(client_membership_ids, list):
#                 client_membership_ids = [client_membership_ids]
#
#             # =====================================================
#             #  batch limit to avoid Odoo timeout crash
#             # =====================================================
#             BATCH_SIZE = 10
#             client_membership_ids = client_membership_ids[:BATCH_SIZE]
#
#             _logger.info(f"Processing batch of {len(client_membership_ids)} clients")
#
#             for client_id in client_membership_ids:
#
#                 # =====================================================
#                 #  ensure correct data type (IMPORTANT)
#                 # Mindbody expects INT not string
#                 # =====================================================
#                 try:
#                     client_id = int(client_id)
#                 except Exception:
#                     _logger.warning(f"Invalid ClientId skipped: {client_id}")
#                     continue
#
#                 # API params
#                 params = {
#                     'ClientId': client_id  # FIXED: now always integer
#                 }
#
#                 if limit:
#                     params['Limit'] = limit
#
#                 if from_date and to_date:
#                     params['ModifiedDateTime'] = f"{from_date}|{to_date}"
#                 elif from_date:
#                     params['ModifiedDateTime'] = from_date
#
#                 _logger.info(f"Sync params: {params}")
#
#                 # =====================================================
#                 #   : safe API call to prevent crash/hang
#                 # =====================================================
#                 try:
#                     response = api.get_client_activeclientmemberships(params=params) or {}
#
#                 except Exception as e:
#                     _logger.error(f"API failed for ClientId {client_id}: {e}")
#                     stats['errors'] += 1
#                     continue
#
#                 # =====================================================
#                 #    : debug response (IMPORTANT for your issue)
#                 # =====================================================
#                 _logger.info(f"RAW RESPONSE for {client_id}: {response}")
#
#                 memberships_data = response.get('ClientMemberships') or []
#
#                 if not memberships_data:
#                     _logger.warning(f"No memberships returned for ClientId {client_id}")
#                     continue
#
#                 # preload existing records
#                 ids = [m.get('Id') for m in memberships_data if m.get('Id')]
#
#                 existing_records = self.search([
#                     ('client_membership_id', 'in', ids)
#                 ])
#
#                 existing_map = {
#                     (r.client_membership_id, r.client_id.id if r.client_id else None): r
#                     for r in existing_records
#                 }
#
#                 # process memberships
#                 for membership_data in memberships_data:
#                     try:
#
#                         membership_id = membership_data.get('Id')
#                         client_id_resp = membership_data.get('ClientId')
#
#                         if not membership_id or not client_id_resp:
#                             stats['skipped'] += 1
#                             continue
#
#                         vals = self._prepare_client_membership(membership_data)
#
#                         odoo_client = self.env['mindbody.client'].search([
#                             ('client_id', '=', client_id_resp)
#                         ], limit=1)
#
#                         key = (membership_id, odoo_client.id if odoo_client else None)
#
#                         existing = existing_map.get(key)
#
#                         if existing:
#                             existing.write(vals)
#                             stats['updated'] += 1
#                         else:
#                             self.create(vals)
#                             stats['created'] += 1
#
#                     except Exception as e:
#                         stats['errors'] += 1
#                         _logger.exception(f"Error processing membership {membership_data.get('Id')}: {e}")
#
#             _logger.info(f"SYNC DONE: {stats}")
#             return stats
#
#         except Exception as e:
#             _logger.exception("SYNC FAILED")
#             raise UserError(f"Client membership sync failed: {str(e)}")

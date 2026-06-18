import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
from odoo import models, fields


class MindbodyPaymentMethod(models.Model):
    _name = 'mindbody.payment.method'
    _description = 'Mindbody Payment Method'

    name = fields.Char(string='Name')
    payment_method_id = fields.Integer(string='Payment Method ID')

    fee = fields.Float(string='Fee')
    active = fields.Boolean(string='Active')
    payment_type_name = fields.Char(string='Payment Type Name')

    alt_payment_id = fields.Integer(string='Alternative Payment ID')

    sale_ids = fields.One2many('mindbody.sale', 'payment_method_id', string='Sales')

    def _prepare_payment_method(self, data):
        """
        Prepare payment method values from API response.
        """
        payment_method_vals = {
            'name': data.get('Name'),
            'payment_method_id': data.get('Id'),
            'alt_payment_id': data.get('Id'),
            'fee': data.get('Fee', 0.0),
            'active': data.get('Active', True),
            'payment_type_name': data.get('PaymentTypeName'),
        }

        payment_method_vals = {k: v for k, v in payment_method_vals.items() if v is not None}
        return payment_method_vals

    def _sync_payment_methods_for_client(self, client_id, api, base_params, stats, method_type='custom',
                                         synced_ids=None):
        """
        Sync payment methods for ONE client.
        Returns set of newly synced IDs.
        """
        if synced_ids is None:
            synced_ids = set()

        offset = 0
        page_size = base_params.get('Limit', 100)
        new_ids = set()

        while True:
            params = dict(base_params)
            params['ClientId'] = client_id
            params['Limit'] = page_size
            params['Offset'] = offset

            try:
                if method_type == 'custom':
                    _logger.info(f"[REQUEST → MINDBODY CUSTOM] ClientId={client_id}, Offset={offset}")
                    response = api.get_sale_custompaymentmethods(params=params)
                else:
                    _logger.info(f"[REQUEST → MINDBODY ALT] ClientId={client_id}, Offset={offset}")
                    response = api.get_sale_alternativepaymentmethods(params=params)

                _logger.info(f"[RESPONSE ← MINDBODY] {response}")

                if not isinstance(response, dict):
                    break

                methods_data = response.get('PaymentMethods', [])
                pagination = response.get('PaginationResponse', {})

                if not methods_data:
                    break

                for method_data in methods_data:
                    try:
                        method_id = method_data.get('Id')
                        if not method_id:
                            stats['skipped'] += 1
                            continue

                        # Skip if already synced in this run
                        if method_id in synced_ids:
                            _logger.info(f"Skipping duplicate payment method {method_id} ({method_data.get('Name')})")
                            continue

                        synced_ids.add(method_id)
                        new_ids.add(method_id)

                        existing = self.search([('payment_method_id', '=', method_id)], limit=1)
                        method_vals = self._prepare_payment_method(method_data)

                        if existing:
                            existing.write(method_vals)
                            stats['updated'] += 1
                            _logger.info(f"Updated payment method {method_id}: {method_data.get('Name')}")
                        else:
                            self.create(method_vals)
                            stats['created'] += 1
                            _logger.info(f"Created payment method {method_id}: {method_data.get('Name')}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error: {str(e)}", exc_info=True)
                        continue

                # FIX: Handle TotalResults=0 but data exists
                total_results = pagination.get('TotalResults', 0)
                if total_results == 0 and len(methods_data) > 0:
                    total_results = offset + len(methods_data)

                offset += page_size

                if offset >= total_results:
                    break

            except UserError as e:
                _logger.warning(f"Skipping client {client_id} for {method_type}: {str(e)}")
                break
            except Exception as e:
                _logger.error(f"Error syncing {method_type} for client {client_id}: {str(e)}")
                break

        return new_ids

    def synchronize(self, from_date=None, to_date=None, limit=None, payment_method_ids=None, client_id=None):
        """
        Sync payment methods from Mindbody.
        Uses first client only since payment methods are global.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            base_params = {}
            if limit:
                base_params['Limit'] = limit
            if payment_method_ids:
                base_params['PaymentMethodIDs'] = ','.join(map(str, payment_method_ids)) if isinstance(
                    payment_method_ids, list) else payment_method_ids

            # Determine which clients to sync
            if client_id:
                clients = self.env['mindbody.client'].browse(client_id)
            else:
                clients = self.env['mindbody.client'].search([('client_id', '!=', False)],
                                                             limit=1)  # ← Only first client!

            if not clients:
                _logger.warning("No clients found to sync payment methods for")
                return stats

            synced_ids = set()  # Track globally synced IDs across both types

            # FIX: Only sync first client — payment methods are global
            first_client = clients[0]
            mb_client_id = first_client.client_id

            if not mb_client_id:
                stats['skipped'] += 1
                _logger.warning("First client has no Mindbody ID")
                return stats

            _logger.info(f"Syncing payment methods using first client {mb_client_id} (global methods)")

            # Sync custom payment methods
            custom_ids = self._sync_payment_methods_for_client(
                client_id=mb_client_id,
                api=api,
                base_params=base_params,
                stats=stats,
                method_type='custom',
                synced_ids=synced_ids
            )
            synced_ids.update(custom_ids)

            # Sync alternative payment methods
            self._sync_payment_methods_for_client(
                client_id=mb_client_id,
                api=api,
                base_params=base_params,
                stats=stats,
                method_type='alternative',
                synced_ids=synced_ids
            )

            # Log how many clients were skipped
            total_clients = self.env['mindbody.client'].search_count([('client_id', '!=', False)])
            if total_clients > 1:
                _logger.info(f"Skipped {total_clients - 1} clients — payment methods are global")

            _logger.info(f"Payment method sync completed: {stats}")

        except Exception as e:
            _logger.exception("Failed to sync payment methods")
            stats['errors'] += 1
            raise UserError(f"Payment method sync failed: {str(e)}")

        return stats

# import logging
#
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
# # mindbody_payment_method.py
# from odoo import models, fields
#
#
# class MindbodyPaymentMethod(models.Model):
#     _name = 'mindbody.payment.method'
#     _description = 'Mindbody Payment Method'
#
#     name = fields.Char(string='Name')
#     payment_method_id = fields.Integer(string='Payment Method ID')
#
#     # For custom payment methods
#     fee = fields.Float(string='Fee')
#     active = fields.Boolean(string='Active')
#     payment_type_name = fields.Char(string='Payment Type Name')
#
#     # For alternative payment methods
#     alt_payment_id = fields.Integer(string='Alternative Payment ID')
#
#     # Relations
#     sale_ids = fields.One2many('mindbody.sale', 'payment_method_id', string='Sales')
#
#     # mindbody_payment_method.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_payment_method(self, data):
#         """
#         Prepare payment method values from API response.
#
#         Args:
#             data (dict): Payment method data from Mindbody API
#
#         Returns:
#             dict: Values ready for mindbody.payment.method create/write
#         """
#         self.ensure_one()
#
#         payment_method_vals = {
#             'name': data.get('Name'),
#             'payment_method_id': data.get('Id'),
#             'alt_payment_id': data.get('Id'),  # For alternative payment methods
#             'fee': data.get('Fee', 0.0),
#             'active': data.get('Active', True),
#             'payment_type_name': data.get('PaymentTypeName'),
#         }
#
#         # Remove None values
#         payment_method_vals = {k: v for k, v in payment_method_vals.items() if v is not None and v is not False}
#
#         return payment_method_vals
#
#     # mindbody_payment_method.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, payment_method_ids=None):
#         """
#         Synchronize payment methods from Mindbody to Odoo.
#         This handles both custom and alternative payment methods.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Maximum number of records to fetch
#             payment_method_ids (list, optional): Specific payment method IDs to sync
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
#             if payment_method_ids:
#                 params['PaymentMethodIDs'] = ','.join(map(str, payment_method_ids)) if isinstance(payment_method_ids,
#                                                                                                   list) else payment_method_ids
#
#             _logger.info(f"Starting payment method sync with params: {params}")
#
#             # Fetch custom payment methods
#             custom_response = api.get_sale_custompaymentmethods(params=params)
#             custom_methods = custom_response.get('PaymentMethods', []) if isinstance(custom_response, dict) else []
#
#             # Fetch alternative payment methods
#             alt_response = api.get_sale_alternativepaymentmethods(params=params)
#             alt_methods = alt_response.get('PaymentMethods', []) if isinstance(alt_response, dict) else []
#
#             all_methods = custom_methods + alt_methods
#
#             if not all_methods:
#                 _logger.info("No payment methods found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(all_methods)} payment methods from Mindbody")
#
#             # Process each payment method
#             for method_data in all_methods:
#                 try:
#                     method_id = method_data.get('Id')
#                     if not method_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping payment method without ID")
#                         continue
#
#                     # Check if payment method already exists
#                     existing = self.search([('payment_method_id', '=', method_id)], limit=1)
#
#                     # Prepare payment method values
#                     method_vals = self._prepare_payment_method(method_data)
#
#                     if existing:
#                         existing.write(method_vals)
#                         stats['updated'] += 1
#                         _logger.info(f"Updated payment method {method_id}: {method_data.get('Name')}")
#                     else:
#                         self.create(method_vals)
#                         stats['created'] += 1
#                         _logger.info(f"Created payment method {method_id}: {method_data.get('Name')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing payment method {method_data.get('Id')}: {str(e)}", exc_info=True)
#                     continue
#
#             _logger.info(f"Payment method sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync payment methods")
#             stats['errors'] += 1
#             raise UserError(f"Payment method sync failed: {str(e)}")
#
#         return stats

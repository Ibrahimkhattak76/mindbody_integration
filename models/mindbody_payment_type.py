import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyPaymentType(models.Model):
    _name = 'mindbody.payment.type'
    _description = 'Mindbody Payment Type'

    payment_type_id = fields.Integer(string='Payment Type ID')
    payment_type_name = fields.Char(string='Payment Type Name')
    active = fields.Boolean(string='Active')
    fee = fields.Float(string='Fee')

    # ============================================
    # Prepare Methods
    # ============================================

    @api.model  # [FIXED] Added decorator + removed ensure_one()
    def _prepare_payment_type(self, data):
        """
        Prepare payment type values from API response.

        Args:
            data (dict): Payment type data from Mindbody API (from /site/paymenttypes endpoint)

        Returns:
            dict: Values ready for mindbody.payment.type create/write
        """
        # [REMOVED] self.ensure_one()
        # Reason: Called from synchronize() where self is empty recordset

        payment_type_vals = {
            'payment_type_id': data.get('Id'),
            'payment_type_name': data.get('PaymentTypeName'),
            'active': data.get('Active', True),
            'fee': data.get('Fee', 0.0),
        }

        # Remove None values
        payment_type_vals = {k: v for k, v in payment_type_vals.items() if v is not None and v is not False}

        return payment_type_vals

    # ============================================
    # Synchronize Method
    # ============================================

    @api.model  # [FIXED] Added decorator so button works from list view
    def synchronize(self, from_date=None, to_date=None, limit=None, payment_type_ids=None):
        """
        Synchronize payment types from Mindbody to Odoo.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            payment_type_ids (list, optional): Specific payment type IDs to sync

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
            if payment_type_ids:
                params['PaymentTypeIDs'] = ','.join(map(str, payment_type_ids)) if isinstance(payment_type_ids,
                                                                                              list) else payment_type_ids

            _logger.info(f"Starting payment type sync with params: {params}")

            # Fetch payment types from Mindbody API
            response = api.get_site_paymenttypes(params=params)
            payment_types_data = response.get('PaymentTypes', []) if isinstance(response, dict) else []

            if not payment_types_data:
                _logger.info("No payment types found to sync")
                return stats

            _logger.info(f"Fetched {len(payment_types_data)} payment types from Mindbody")

            # Process each payment type
            for payment_type_data in payment_types_data:
                try:
                    payment_type_id = payment_type_data.get('Id')
                    if not payment_type_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping payment type without ID")
                        continue

                    # Check if payment type already exists
                    existing = self.search([('payment_type_id', '=', payment_type_id)], limit=1)

                    # Prepare payment type values
                    payment_type_vals = self._prepare_payment_type(payment_type_data)

                    if existing:
                        existing.write(payment_type_vals)
                        stats['updated'] += 1
                        _logger.info(
                            f"Updated payment type {payment_type_id}: {payment_type_data.get('PaymentTypeName')}")
                    else:
                        self.create(payment_type_vals)
                        stats['created'] += 1
                        _logger.info(
                            f"Created payment type {payment_type_id}: {payment_type_data.get('PaymentTypeName')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing payment type {payment_type_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            _logger.info(f"Payment type sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync payment types")
            stats['errors'] += 1
            raise UserError(f"Payment type sync failed: {str(e)}")

        return stats

# import logging
#
# _logger = logging.getLogger(__name__)
# # mindbody_payment_type.py
# from odoo import models, fields
#
#
# class MindbodyPaymentType(models.Model):
#     _name = 'mindbody.payment.type'
#     _description = 'Mindbody Payment Type'
#
#     payment_type_id = fields.Integer(string='Payment Type ID')
#     payment_type_name = fields.Char(string='Payment Type Name')
#     active = fields.Boolean(string='Active')
#     fee = fields.Float(string='Fee')
#
#     # mindbody_payment_type.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_payment_type(self, data):
#         """
#         Prepare payment type values from API response.
#
#         Args:
#             data (dict): Payment type data from Mindbody API (from /site/paymenttypes endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.payment.type create/write
#         """
#         self.ensure_one()
#
#         payment_type_vals = {
#             'payment_type_id': data.get('Id'),
#             'payment_type_name': data.get('PaymentTypeName'),
#             'active': data.get('Active', True),
#             'fee': data.get('Fee', 0.0),
#         }
#
#         # Remove None values
#         payment_type_vals = {k: v for k, v in payment_type_vals.items() if v is not None and v is not False}
#
#         return payment_type_vals
#
#     # mindbody_payment_type.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, payment_type_ids=None):
#         """
#         Synchronize payment types from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Maximum number of records to fetch
#             payment_type_ids (list, optional): Specific payment type IDs to sync
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
#             if payment_type_ids:
#                 params['PaymentTypeIDs'] = ','.join(map(str, payment_type_ids)) if isinstance(payment_type_ids,
#                                                                                               list) else payment_type_ids
#
#             _logger.info(f"Starting payment type sync with params: {params}")
#
#             # Fetch payment types from Mindbody API
#             response = api.get_site_paymenttypes(params=params)
#             payment_types_data = response.get('PaymentTypes', []) if isinstance(response, dict) else []
#
#             if not payment_types_data:
#                 _logger.info("No payment types found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(payment_types_data)} payment types from Mindbody")
#
#             # Process each payment type
#             for payment_type_data in payment_types_data:
#                 try:
#                     payment_type_id = payment_type_data.get('Id')
#                     if not payment_type_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping payment type without ID")
#                         continue
#
#                     # Check if payment type already exists
#                     existing = self.search([('payment_type_id', '=', payment_type_id)], limit=1)
#
#                     # Prepare payment type values
#                     payment_type_vals = self._prepare_payment_type(payment_type_data)
#
#                     if existing:
#                         existing.write(payment_type_vals)
#                         stats['updated'] += 1
#                         _logger.info(
#                             f"Updated payment type {payment_type_id}: {payment_type_data.get('PaymentTypeName')}")
#                     else:
#                         self.create(payment_type_vals)
#                         stats['created'] += 1
#                         _logger.info(
#                             f"Created payment type {payment_type_id}: {payment_type_data.get('PaymentTypeName')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing payment type {payment_type_data.get('Id')}: {str(e)}",
#                                   exc_info=True)
#                     continue
#
#             _logger.info(f"Payment type sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync payment types")
#             stats['errors'] += 1
#             raise UserError(f"Payment type sync failed: {str(e)}")
#
#         return stats

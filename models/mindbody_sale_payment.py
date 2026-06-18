import logging

_logger = logging.getLogger(__name__)

from odoo import models, fields


class MindbodySalePayment(models.Model):
    _name = 'mindbody.sale.payment'
    _description = 'Mindbody Sale Payment'

    sale_id = fields.Many2one('mindbody.sale', string='Sale')

    payment_id = fields.Integer(string='Payment ID')
    amount = fields.Float(string='Amount')
    method = fields.Integer(string='Method')
    payment_type = fields.Char(string='Type')
    notes = fields.Text(string='Notes')
    transaction_id = fields.Integer(string='Transaction ID')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_sale_payment(self, data):
        """
        Prepare sale payment values from API response.
        """
        payment_vals = {
            'payment_id': data.get('Id'),
            'amount': data.get('Amount', 0.0),
            'method': data.get('Method', 0),
            'payment_type': data.get('Type'),
            'notes': data.get('Notes'),
            'transaction_id': data.get('TransactionId'),
        }

        # Remove None values
        payment_vals = {k: v for k, v in payment_vals.items() if v is not None and v is not False}

        return payment_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, payment_ids=None):
        """
        Trigger parent Sale sync (payments sync automatically with sales).
        """
        _logger.info("Sale Payment sync triggered — delegating to Sale sync...")
        return self.env['mindbody.sale'].synchronize(
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

# import logging
#
# _logger = logging.getLogger(__name__)
# # mindbody_sale_payment.py
# from odoo import models, fields
#
#
# class MindbodySalePayment(models.Model):
#     _name = 'mindbody.sale.payment'
#     _description = 'Mindbody Sale Payment'
#
#     sale_id = fields.Many2one('mindbody.sale', string='Sale')
#
#     payment_id = fields.Integer(string='Payment ID')
#     amount = fields.Float(string='Amount')
#     method = fields.Integer(string='Method')
#     payment_type = fields.Char(string='Type')
#     notes = fields.Text(string='Notes')
#     transaction_id = fields.Integer(string='Transaction ID')
#
#     # mindbody_sale_payment.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_sale_payment(self, data):
#         """
#         Prepare sale payment values from API response.
#
#         Args:
#             data (dict): Sale payment data from Mindbody API
#
#         Returns:
#             dict: Values ready for mindbody.sale.payment create/write
#         """
#         # ✅ ensure_one() hata diya — yeh helper method hai, record nahi chahiye
#
#         payment_vals = {
#             'payment_id': data.get('Id'),
#             'amount': data.get('Amount', 0.0),
#             'method': data.get('Method', 0),
#             'payment_type': data.get('Type'),
#             'notes': data.get('Notes'),
#             'transaction_id': data.get('TransactionId'),
#         }
#
#         # Remove None values
#         payment_vals = {k: v for k, v in payment_vals.items() if v is not None and v is not False}
#
#         return payment_vals
#
#     # mindbody_sale_payment.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, payment_ids=None):
#         """
#         Synchronize sale payments from Mindbody to Odoo.
#         Note: Sale payments are typically synced as part of sale sync.
#
#         Args:
#             from_date (str, optional): Not used for this endpoint
#             to_date (str, optional): Not used for this endpoint
#             limit (int, optional): Not used for this endpoint
#             payment_ids (list, optional): Not used for this endpoint
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         _logger.info("Sale payments are synced automatically during sale sync")
#         return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

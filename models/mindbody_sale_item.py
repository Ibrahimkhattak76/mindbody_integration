import logging
from datetime import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodySaleItem(models.Model):
    _name = 'mindbody.sale.item'
    _description = 'Mindbody Sale Item'

    sale_id = fields.Many2one('mindbody.sale', string='Sale')

    sale_detail_id = fields.Integer(string='Sale Detail ID')
    item_id = fields.Integer(string='Item ID')
    is_service = fields.Boolean(string='Is Service')
    barcode_id = fields.Char(string='Barcode ID')
    description = fields.Text(string='Description')
    contract_id = fields.Integer(string='Contract ID')
    category_id = fields.Integer(string='Category ID')
    sub_category_id = fields.Integer(string='Sub Category ID')
    unit_price = fields.Float(string='Unit Price')
    quantity = fields.Float(string='Quantity')
    discount_percent = fields.Float(string='Discount Percent')
    discount_amount = fields.Float(string='Discount Amount')
    tax1 = fields.Float(string='Tax 1')
    tax2 = fields.Float(string='Tax 2')
    tax3 = fields.Float(string='Tax 3')
    tax4 = fields.Float(string='Tax 4')
    tax5 = fields.Float(string='Tax 5')
    tax_amount = fields.Float(string='Tax Amount')
    total_amount = fields.Float(string='Total Amount')
    notes = fields.Text(string='Notes')
    returned = fields.Boolean(string='Returned')
    payment_ref_id = fields.Integer(string='Payment Ref ID')
    exp_date = fields.Datetime(string='Exp Date')
    active_date = fields.Datetime(string='Active Date')
    gift_card_barcode_id = fields.Char(string='Gift Card Barcode ID')
    recipient_client_id = fields.Integer(string='Recipient Client ID')

    def _parse_datetime(self, value):
        """Convert ISO 8601 datetime to Odoo format"""
        if not value:
            return False
        try:
            if 'Z' in value:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            elif 'T' in value:
                dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            else:
                return value
            return fields.Datetime.to_string(dt)
        except Exception as e:
            _logger.warning(f"Failed to parse datetime '{value}': {str(e)}")
            return False

    def _prepare_sale_item(self, data):
        """
        Prepare sale item values from API response.
        """
        sale_item_vals = {
            'sale_detail_id': data.get('SaleDetailId'),
            'item_id': data.get('Id'),
            'is_service': data.get('IsService', False),
            'barcode_id': data.get('BarcodeId'),
            'description': data.get('Description'),
            'contract_id': data.get('ContractId'),
            'category_id': data.get('CategoryId'),
            'sub_category_id': data.get('SubCategoryId'),
            'unit_price': data.get('UnitPrice', 0.0),
            'quantity': data.get('Quantity', 0.0),
            'discount_percent': data.get('DiscountPercent', 0.0),
            'discount_amount': data.get('DiscountAmount', 0.0),
            'tax1': data.get('Tax1', 0.0),
            'tax2': data.get('Tax2', 0.0),
            'tax3': data.get('Tax3', 0.0),
            'tax4': data.get('Tax4', 0.0),
            'tax5': data.get('Tax5', 0.0),
            'tax_amount': data.get('TaxAmount', 0.0),
            'total_amount': data.get('TotalAmount', 0.0),
            'notes': data.get('Notes'),
            'returned': data.get('Returned', False),
            'payment_ref_id': data.get('PaymentRefId'),
            'exp_date': self._parse_datetime(data.get('ExpDate')),
            'active_date': self._parse_datetime(data.get('ActiveDate')),
            'gift_card_barcode_id': data.get('GiftCardBarcodeId'),
            'recipient_client_id': data.get('RecipientClientId'),
        }

        # Remove None values only
        sale_item_vals = {k: v for k, v in sale_item_vals.items() if v is not None}

        return sale_item_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, sale_item_ids=None, sale_id=None):
        """
        Sale items are always synced as part of Sale records.
        They cannot be fetched independently from Mindbody API.
        """
        _logger.info("Sale Item sync triggered — delegating to Sale sync...")
        return self.env['mindbody.sale'].synchronize(
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            sale_ids=[sale_id] if sale_id else None,
        )

# import logging
# from datetime import datetime
#
# from odoo import models, fields
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodySaleItem(models.Model):
#     _name = 'mindbody.sale.item'
#     _description = 'Mindbody Sale Item'
#
#     sale_id = fields.Many2one('mindbody.sale', string='Sale')
#
#     sale_detail_id = fields.Integer(string='Sale Detail ID')
#     item_id = fields.Integer(string='Item ID')
#     is_service = fields.Boolean(string='Is Service')
#     barcode_id = fields.Char(string='Barcode ID')
#     description = fields.Text(string='Description')
#     contract_id = fields.Integer(string='Contract ID')
#     category_id = fields.Integer(string='Category ID')
#     sub_category_id = fields.Integer(string='Sub Category ID')
#     unit_price = fields.Float(string='Unit Price')
#     quantity = fields.Float(string='Quantity')
#     discount_percent = fields.Float(string='Discount Percent')
#     discount_amount = fields.Float(string='Discount Amount')
#     tax1 = fields.Float(string='Tax 1')
#     tax2 = fields.Float(string='Tax 2')
#     tax3 = fields.Float(string='Tax 3')
#     tax4 = fields.Float(string='Tax 4')
#     tax5 = fields.Float(string='Tax 5')
#     tax_amount = fields.Float(string='Tax Amount')
#     total_amount = fields.Float(string='Total Amount')
#     notes = fields.Text(string='Notes')
#     returned = fields.Boolean(string='Returned')
#     payment_ref_id = fields.Integer(string='Payment Ref ID')
#     exp_date = fields.Datetime(string='Exp Date')
#     active_date = fields.Datetime(string='Active Date')
#     gift_card_barcode_id = fields.Char(string='Gift Card Barcode ID')
#     recipient_client_id = fields.Integer(string='Recipient Client ID')
#
#     def _parse_datetime(self, value):
#         """Convert ISO 8601 datetime to Odoo format"""
#         if not value:
#             return False
#         try:
#             if 'Z' in value:
#                 dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
#             elif 'T' in value:
#                 dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
#             else:
#                 return value
#             return fields.Datetime.to_string(dt)
#         except Exception as e:
#             _logger.warning(f"Failed to parse datetime '{value}': {str(e)}")
#             return False
#
#     def _prepare_sale_item(self, data):
#         """
#         Prepare sale item values from API response.
#         """
#         sale_item_vals = {
#             'sale_detail_id': data.get('SaleDetailId'),
#             'item_id': data.get('Id'),
#             'is_service': data.get('IsService', False),
#             'barcode_id': data.get('BarcodeId'),
#             'description': data.get('Description'),
#             'contract_id': data.get('ContractId'),
#             'category_id': data.get('CategoryId'),
#             'sub_category_id': data.get('SubCategoryId'),
#             'unit_price': data.get('UnitPrice', 0.0),
#             'quantity': data.get('Quantity', 0.0),
#             'discount_percent': data.get('DiscountPercent', 0.0),
#             'discount_amount': data.get('DiscountAmount', 0.0),
#             'tax1': data.get('Tax1', 0.0),
#             'tax2': data.get('Tax2', 0.0),
#             'tax3': data.get('Tax3', 0.0),
#             'tax4': data.get('Tax4', 0.0),
#             'tax5': data.get('Tax5', 0.0),
#             'tax_amount': data.get('TaxAmount', 0.0),
#             'total_amount': data.get('TotalAmount', 0.0),
#             'notes': data.get('Notes'),
#             'returned': data.get('Returned', False),
#             'payment_ref_id': data.get('PaymentRefId'),
#             'exp_date': self._parse_datetime(data.get('ExpDate')),  # ✅ FIX
#             'active_date': self._parse_datetime(data.get('ActiveDate')),  # ✅ FIX
#             'gift_card_barcode_id': data.get('GiftCardBarcodeId'),
#             'recipient_client_id': data.get('RecipientClientId'),
#         }
#
#         # Remove None values
#         sale_item_vals = {k: v for k, v in sale_item_vals.items() if v is not None and v is not False}
#
#         return sale_item_vals
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, sale_item_ids=None):
#         """
#         Sale items are synced as part of sale sync.
#         Triggering sale sync instead.
#         """
#         _logger.info("Sale Item sync triggered — delegating to Sale sync...")
#         return self.env['mindbody.sale'].synchronize(
#             from_date=from_date,
#             to_date=to_date,
#             limit=limit,
#         )

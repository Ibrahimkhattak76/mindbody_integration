import logging
from datetime import datetime

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodySale(models.Model):
    _name = 'mindbody.sale'
    _description = 'Mindbody Sale'

    sale_id = fields.Integer(string='Sale ID')
    sale_date = fields.Date(string='Sale Date')
    sale_time = fields.Char(string='Sale Time')
    sale_date_time = fields.Datetime(string='Sale Date Time')
    original_sale_date_time = fields.Datetime(string='Original Sale Date Time')
    sales_rep_id = fields.Integer(string='Sales Rep ID')
    client_id = fields.Char(string='Client ID')
    recipient_client_id = fields.Integer(string='Recipient Client ID')

    purchased_item_ids = fields.One2many('mindbody.sale.item', 'sale_id', string='Purchased Items')
    location_id = fields.Many2one('mindbody.location', string='Location')
    payment_ids = fields.One2many('mindbody.sale.payment', 'sale_id', string='Payments')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    return_sale_id = fields.Integer(string='Return Sale ID')
    trainer_id = fields.Integer(string='Trainer ID')
    amount = fields.Float(string='Amount')
    payment_method_id = fields.Many2one('mindbody.payment.method', string='Payment Method')

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

    def _get_or_sync_location(self, location_id_val):
        if not location_id_val:
            return False
        location = self.env['mindbody.location'].search([('location_id', '=', location_id_val)], limit=1)
        if location:
            return location
        _logger.info(f"Location {location_id_val} not found, syncing...")
        self.env['mindbody.location'].synchronize(location_ids=[location_id_val])
        return self.env['mindbody.location'].search([('location_id', '=', location_id_val)], limit=1)

    def _prepare_sale(self, data):
        location = self._get_or_sync_location(data.get('LocationId'))

        item_commands = []
        for item_data in data.get('PurchasedItems', []):
            item_vals = self.env['mindbody.sale.item']._prepare_sale_item(item_data)
            if item_vals:
                item_commands.append((0, 0, item_vals))

        payment_commands = []
        for payment_data in data.get('Payments', []):
            payment_vals = self.env['mindbody.sale.payment']._prepare_sale_payment(payment_data)
            if payment_vals:
                payment_commands.append((0, 0, payment_vals))

        payment_method_id = False
        if data.get('Payments') and len(data['Payments']) > 0:
            payment_method = self.env['mindbody.payment.method'].search([
                ('payment_method_id', '=', data['Payments'][0].get('Method'))
            ], limit=1)
            if payment_method:
                payment_method_id = payment_method.id

        sale_vals = {
            'sale_id': data.get('Id'),
            'sale_date': data.get('SaleDate'),
            'sale_time': data.get('SaleTime'),
            'sale_date_time': self._parse_datetime(data.get('SaleDateTime')),
            'original_sale_date_time': self._parse_datetime(data.get('OriginalSaleDateTime')),
            'sales_rep_id': data.get('SalesRepId'),
            'client_id': data.get('ClientId'),
            'recipient_client_id': data.get('RecipientClientId'),
            'location_id': location.id if location else False,
            'return_sale_id': data.get('ReturnSaleID'),
            'trainer_id': data.get('TrainerID'),
            'amount': data.get('Amount', 0.0),
        }

        if payment_method_id:
            sale_vals['payment_method_id'] = payment_method_id
        if item_commands:
            sale_vals['purchased_item_ids'] = item_commands
        if payment_commands:
            sale_vals['payment_ids'] = payment_commands

        sale_vals = {k: v for k, v in sale_vals.items() if v is not None}
        return sale_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, sale_ids=None):
        """
        Synchronize sales from Mindbody to Odoo.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # ============================================
        # STEP A: Set up pagination variables
        # ============================================
        offset = 0
        page_size = limit if limit else 100
        has_more = True

        try:
            # ============================================
            # STEP B: Build the filters (date, sale IDs, etc.)
            # ============================================
            base_params = {}
            if sale_ids:
                base_params['SaleID'] = ','.join(map(str, sale_ids)) if isinstance(sale_ids, list) else sale_ids
            if from_date:
                base_params['StartSaleDateTime'] = from_date
                if to_date:
                    base_params['EndSaleDateTime'] = to_date

            # ============================================
            # STEP C: THE LOOP - Keep asking until no more data
            # ============================================
            while has_more:

                # --- C1: Build params for THIS page ---
                params = dict(base_params)
                params['Limit'] = page_size
                params['Offset'] = offset

                _logger.info(f"Fetching sales page: offset={offset}, limit={page_size}")

                # --- C2: Call the API ---
                response = api.get_sale_sales(params=params)

                # --- C3: Get the list of sales from response ---
                if isinstance(response, dict):
                    sales_data = response.get('Sales', [])
                else:
                    sales_data = response if response else []

                # --- C4: If no sales, stop ---
                if not sales_data:
                    _logger.info("No more sales. Stopping.")
                    break

                _logger.info(f"Got {len(sales_data)} sales on this page")

                # --- C5: Process EACH sale on this page ---
                for sale_data in sales_data:
                    try:
                        sale_id = sale_data.get('Id')
                        if not sale_id:
                            stats['skipped'] += 1
                            _logger.warning("Skipping sale without ID")
                            continue

                        existing = self.search([('sale_id', '=', sale_id)], limit=1)
                        sale_vals = self._prepare_sale(sale_data)

                        if existing:
                            if 'purchased_item_ids' in sale_vals:
                                existing.purchased_item_ids.unlink()
                            if 'payment_ids' in sale_vals:
                                existing.payment_ids.unlink()
                            existing.write(sale_vals)
                            stats['updated'] += 1
                            _logger.info(f"Updated sale {sale_id}")
                        else:
                            self.create(sale_vals)
                            stats['created'] += 1
                            _logger.info(f"Created sale {sale_id}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing sale {sale_data.get('Id')}: {str(e)}", exc_info=True)
                        continue

                # ============================================
                # STEP D: Decide if we need another page
                # ============================================

                # If we got LESS than page_size, it means this was the LAST page
                if len(sales_data) < page_size:
                    _logger.info(f"LAST PAGE! Total: created={stats['created']}, updated={stats['updated']}")
                    has_more = False

                    # Save pagination info if available
                    if isinstance(response, dict) and response.get('PaginationResponse'):
                        pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                            response['PaginationResponse']
                        )
                        if pagination_vals:
                            self.env['mindbody.pagination.response'].create(pagination_vals)
                else:
                    offset += page_size
                    _logger.info(f"Next page! New offset: {offset}")

        except Exception as e:
            _logger.exception("Failed to sync sales")
            raise UserError(f"Sale sync failed: {str(e)}")

        _logger.info(f"Sale sync completed: {stats['created']} created, {stats['updated']} updated, "
                     f"{stats['errors']} errors, {stats['skipped']} skipped")

        return stats

# import logging
# from datetime import datetime
#
# from odoo import models, fields
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodySale(models.Model):
#     _name = 'mindbody.sale'
#     _description = 'Mindbody Sale'
#
#     sale_id = fields.Integer(string='Sale ID')
#     sale_date = fields.Date(string='Sale Date')
#     sale_time = fields.Char(string='Sale Time')
#     sale_date_time = fields.Datetime(string='Sale Date Time')
#     original_sale_date_time = fields.Datetime(string='Original Sale Date Time')
#     sales_rep_id = fields.Integer(string='Sales Rep ID')
#     client_id = fields.Char(string='Client ID')
#     recipient_client_id = fields.Integer(string='Recipient Client ID')
#
#     purchased_item_ids = fields.One2many('mindbody.sale.item', 'sale_id', string='Purchased Items')
#     location_id = fields.Many2one('mindbody.location', string='Location')
#     payment_ids = fields.One2many('mindbody.sale.payment', 'sale_id', string='Payments')
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     return_sale_id = fields.Integer(string='Return Sale ID')
#     trainer_id = fields.Integer(string='Trainer ID')
#     amount = fields.Float(string='Amount')
#     payment_method_id = fields.Many2one('mindbody.payment.method', string='Payment Method')
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
#     def _get_or_sync_location(self, location_id_val):
#         if not location_id_val:
#             return False
#         location = self.env['mindbody.location'].search([('location_id', '=', location_id_val)], limit=1)
#         if location:
#             return location
#         _logger.info(f"Location {location_id_val} not found, syncing...")
#         self.env['mindbody.location'].synchronize(location_ids=[location_id_val])
#         return self.env['mindbody.location'].search([('location_id', '=', location_id_val)], limit=1)
#
#     def _prepare_sale(self, data):
#         location = self._get_or_sync_location(data.get('LocationId'))
#
#         item_commands = []
#         for item_data in data.get('PurchasedItems', []):
#             item_vals = self.env['mindbody.sale.item']._prepare_sale_item(item_data)
#             if item_vals:
#                 item_commands.append((0, 0, item_vals))
#
#         payment_commands = []
#         for payment_data in data.get('Payments', []):
#             payment_vals = self.env['mindbody.sale.payment']._prepare_sale_payment(payment_data)
#             if payment_vals:
#                 payment_commands.append((0, 0, payment_vals))
#
#         payment_method_id = False
#         if data.get('Payments') and len(data['Payments']) > 0:
#             payment_method = self.env['mindbody.payment.method'].search([
#                 ('payment_method_id', '=', data['Payments'][0].get('Method'))
#             ], limit=1)
#             if payment_method:
#                 payment_method_id = payment_method.id
#
#         sale_vals = {
#             'sale_id': data.get('Id'),
#             'sale_date': data.get('SaleDate'),
#             'sale_time': data.get('SaleTime'),
#             'sale_date_time': self._parse_datetime(data.get('SaleDateTime')),
#             'original_sale_date_time': self._parse_datetime(data.get('OriginalSaleDateTime')),
#             'sales_rep_id': data.get('SalesRepId'),
#             'client_id': data.get('ClientId'),
#             'recipient_client_id': data.get('RecipientClientId'),
#             'location_id': location.id if location else False,
#             'return_sale_id': data.get('ReturnSaleID'),
#             'trainer_id': data.get('TrainerID'),
#             'amount': data.get('Amount', 0.0),
#         }
#
#         if payment_method_id:
#             sale_vals['payment_method_id'] = payment_method_id
#         if item_commands:
#             sale_vals['purchased_item_ids'] = item_commands
#         if payment_commands:
#             sale_vals['payment_ids'] = payment_commands
#
#         sale_vals = {k: v for k, v in sale_vals.items() if v is not None}
#         return sale_vals
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, sale_ids=None):
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             params = {}
#             if limit:
#                 params['Limit'] = limit
#             if sale_ids:
#                 params['SaleID'] = ','.join(map(str, sale_ids)) if isinstance(sale_ids, list) else sale_ids
#             if from_date:
#                 params['StartSaleDateTime'] = from_date
#                 if to_date:
#                     params['EndSaleDateTime'] = to_date
#
#             _logger.info(f"Starting sale sync with params: {params}")
#             response = api.get_sale_sales(params=params)
#             sales_data = response.get('Sales', []) if isinstance(response, dict) else []
#
#             if not sales_data:
#                 _logger.info("No sales found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(sales_data)} sales from Mindbody")
#
#             for sale_data in sales_data:
#                 try:
#                     sale_id = sale_data.get('Id')
#                     if not sale_id:
#                         stats['skipped'] += 1
#                         continue
#
#                     existing = self.search([('sale_id', '=', sale_id)], limit=1)
#                     sale_vals = self._prepare_sale(sale_data)
#
#                     if existing:
#                         if 'purchased_item_ids' in sale_vals:
#                             existing.purchased_item_ids.unlink()
#                         if 'payment_ids' in sale_vals:
#                             existing.payment_ids.unlink()
#                         existing.write(sale_vals)
#                         stats['updated'] += 1
#                     else:
#                         self.create(sale_vals)
#                         stats['created'] += 1
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing sale {sale_data.get('Id')}: {str(e)}", exc_info=True)
#
#             _logger.info(f"Sale sync completed: {stats}")
#
#         except Exception as e:
#             _logger.exception("Failed to sync sales")
#             raise UserError(f"Sale sync failed: {str(e)}")
#
#         return stats

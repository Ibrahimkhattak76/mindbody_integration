import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from odoo import models, fields


class MindbodyClientPurchase(models.Model):
    _name = 'mindbody.client.purchase'
    _description = 'Mindbody Client Purchase'

    client_id = fields.Many2one('mindbody.client', string='Client')
    sale_id = fields.Many2one('mindbody.sale', string='Sale')

    description = fields.Text(string='Description')
    account_payment = fields.Boolean(string='Account Payment')
    price = fields.Float(string='Price')
    amount_paid = fields.Float(string='Amount Paid')
    discount = fields.Float(string='Discount')
    tax = fields.Float(string='Tax')
    returned = fields.Boolean(string='Returned')
    quantity = fields.Float(string='Quantity')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_client_purchase.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client_purchase(self, data):
        """
        Prepare client purchase values from API response.
        
        Args:
            data (dict): Client purchase data from Mindbody API (from /client/clientpurchases endpoint)
            
        Returns:
            dict: Values ready for mindbody.client.purchase create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        purchase_vals = {
            'description': data.get('Description'),
            'account_payment': data.get('AccountPayment', False),
            'price': data.get('Price', 0.0),
            'amount_paid': data.get('AmountPaid', 0.0),
            'discount': data.get('Discount', 0.0),
            'tax': data.get('Tax', 0.0),
            'returned': data.get('Returned', False),
            'quantity': data.get('Quantity', 0.0),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            purchase_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        purchase_vals = {k: v for k, v in purchase_vals.items() if v is not None and v is not False}

        return purchase_vals

    # mindbody_client_purchase.py

    def synchronize(self, from_date=None, to_date=None, limit=None, client_id=None):
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # ClientId required hai — agar nahi diya toh sab clients ka loop chalao
        if client_id:
            client_ids_to_sync = [client_id]
        else:
            # Sab clients Odoo se uthao aur unka client_id use karo
            all_clients = self.env['mindbody.client'].search([])
            client_ids_to_sync = all_clients.mapped('client_id')

        if not client_ids_to_sync:
            _logger.warning("No clients found to sync purchases for.")
            return stats

        for cid in client_ids_to_sync:
            offset = 0
            page_size = 100
            has_more = True

            _logger.info(f"Syncing purchases for client: {cid}")

            while has_more:
                try:
                    params = {
                        'request.clientId': cid,
                        'request.limit': page_size,
                        'request.offset': offset,
                    }
                    if from_date:
                        params['request.startDate'] = from_date
                    if to_date:
                        params['request.endDate'] = to_date

                    response = api.get_client_clientpurchases(params=params)
                    purchases_data = response.get('Purchases', []) if isinstance(response, dict) else []

                    if not purchases_data:
                        break

                    _logger.info(f"Client {cid}: Got {len(purchases_data)} purchases at offset {offset}")

                    for purchase_data in purchases_data:
                        try:
                            sale_ref = purchase_data.get('Sale', {})
                            sale_mindbody_id = sale_ref.get('Id') if isinstance(sale_ref, dict) else None
                            client_mindbody_id = sale_ref.get('ClientId') if isinstance(sale_ref, dict) else None

                            # Agar Sale mein ClientId nahi toh current loop wala cid use karo
                            if not client_mindbody_id:
                                client_mindbody_id = cid

                            _logger.info(
                                f"Purchase data - Sale ID: {sale_mindbody_id}, Client ID: {client_mindbody_id}")
                            _logger.info(f"Raw purchase: {purchase_data}")
                            # Odoo records dhundo
                            sale_record = self.env['mindbody.sale'].search(
                                [('sale_id', '=', sale_mindbody_id)], limit=1
                            ) if sale_mindbody_id else None

                            client_record = self.env['mindbody.client'].search(
                                [('client_id', '=', client_mindbody_id)], limit=1
                            ) if client_mindbody_id else None

                            purchase_vals = {
                                'description': purchase_data.get('Description'),
                                'account_payment': purchase_data.get('AccountPayment', False),
                                'price': purchase_data.get('Price', 0.0),
                                'amount_paid': purchase_data.get('AmountPaid', 0.0),
                                'discount': purchase_data.get('Discount', 0.0),
                                'tax': purchase_data.get('Tax', 0.0),
                                'returned': purchase_data.get('Returned', False),
                                'quantity': purchase_data.get('Quantity', 0.0),
                            }

                            if sale_record:
                                purchase_vals['sale_id'] = sale_record.id
                            if client_record:
                                purchase_vals['client_id'] = client_record.id

                            purchase_vals = {k: v for k, v in purchase_vals.items() if v is not None}

                            # Duplicate check
                            domain = []
                            if sale_record:
                                domain.append(('sale_id', '=', sale_record.id))
                            if client_record:
                                domain.append(('client_id', '=', client_record.id))

                            existing = self.search(domain, limit=1) if domain else None

                            if existing:
                                existing.write(purchase_vals)
                                stats['updated'] += 1
                            else:
                                self.create(purchase_vals)
                                stats['created'] += 1

                        except Exception as e:
                            stats['errors'] += 1
                            _logger.error(f"Error on purchase for client {cid}: {str(e)}", exc_info=True)
                            continue

                    if len(purchases_data) < page_size:
                        has_more = False
                    else:
                        offset += page_size

                except Exception as e:
                    _logger.error(f"Failed page for client {cid}: {str(e)}")
                    has_more = False
                    stats['errors'] += 1
                    continue  # Next client par jao, stop mat karo

        _logger.info(f"Purchase sync done: {stats}")
        return stats

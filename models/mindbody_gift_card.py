import logging

_logger = logging.getLogger(__name__)
# mindbody_gift_card.py
from odoo import models, fields


class MindbodyGiftCardLayout(models.Model):
    _name = 'mindbody.gift.card.layout'
    _description = 'Mindbody Gift Card Layout'

    gift_card_id = fields.Many2one('mindbody.gift.card', string='Gift Card')
    layout_id = fields.Integer(string='Layout ID')
    layout_name = fields.Char(string='Layout Name')
    layout_url = fields.Char(string='Layout URL')


class MindbodyGiftCard(models.Model):
    _name = 'mindbody.gift.card'
    _description = 'Mindbody Gift Card'

    gift_card_id = fields.Integer(string='Gift Card ID')
    location_ids = fields.Char(string='Location IDs')  # JSON list
    description = fields.Text(string='Description')
    editable_by_consumer = fields.Boolean(string='Editable By Consumer')
    card_value = fields.Float(string='Card Value')
    sale_price = fields.Float(string='Sale Price')
    sold_online = fields.Boolean(string='Sold Online')
    membership_restriction_ids = fields.Char(string='Membership Restriction IDs')  # JSON list
    gift_card_terms = fields.Text(string='Gift Card Terms')
    contact_info = fields.Text(string='Contact Info')
    display_logo = fields.Boolean(string='Display Logo')

    # Relations
    layout_ids = fields.One2many('mindbody.gift.card.layout', 'gift_card_id', string='Layouts')

    # For purchases
    barcode_id = fields.Char(string='Barcode ID')
    remaining_balance = fields.Float(string='Remaining Balance')
    value = fields.Float(string='Value')
    amount_paid = fields.Float(string='Amount Paid')
    from_name = fields.Char(string='From Name')
    purchaser_client_id = fields.Char(string='Purchaser Client ID')
    purchaser_email = fields.Char(string='Purchaser Email')
    recipient_email = fields.Char(string='Recipient Email')
    sale_id = fields.Integer(string='Sale ID')
    email_receipt = fields.Boolean(string='Email Receipt')

    payment_processing_failure_ids = fields.Many2many('mindbody.error.info', string='Payment Processing Failures')

    # mindbody_gift_card.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_gift_card(self, data):
        """
        Prepare gift card values from API response.
        
        Args:
            data (dict): Gift card data from Mindbody API (from /sale/giftcards endpoint)
            
        Returns:
            dict: Values ready for mindbody.gift.card create/write
        """
        self.ensure_one()

        # Prepare layouts (One2many)
        layout_commands = []
        for layout_data in data.get('Layouts', []):
            layout_vals = self.env['mindbody.gift.card.layout']._prepare_gift_card_layout(layout_data)
            if layout_vals:
                layout_commands.append((0, 0, layout_vals))

        # Prepare payment failures (Many2many)
        failure_commands = []
        for failure_data in data.get('PaymentProcessingFailures', []):
            failure_vals = self.env['mindbody.error.info']._prepare_error_info(failure_data)
            if failure_vals:
                failure_commands.append((0, 0, failure_vals))

        # Build gift card values
        gift_card_vals = {
            'gift_card_id': data.get('Id'),
            'location_ids': str(data.get('LocationIds', [])),
            'description': data.get('Description'),
            'editable_by_consumer': data.get('EditableByConsumer', False),
            'card_value': data.get('CardValue', 0.0),
            'sale_price': data.get('SalePrice', 0.0),
            'sold_online': data.get('SoldOnline', False),
            'membership_restriction_ids': str(data.get('MembershipRestrictionIds', [])),
            'gift_card_terms': data.get('GiftCardTerms'),
            'contact_info': data.get('ContactInfo'),
            'display_logo': data.get('DisplayLogo', False),

            # For purchases
            'barcode_id': data.get('BarcodeId'),
            'remaining_balance': data.get('RemainingBalance', 0.0),
            'value': data.get('Value', 0.0),
            'amount_paid': data.get('AmountPaid', 0.0),
            'from_name': data.get('FromName'),
            'purchaser_client_id': data.get('PurchaserClientId'),
            'purchaser_email': data.get('PurchaserEmail'),
            'recipient_email': data.get('RecipientEmail'),
            'sale_id': data.get('SaleId'),
            'email_receipt': data.get('EmailReceipt', False),

            # One2many fields
            'layout_ids': layout_commands if layout_commands else None,
            'payment_processing_failure_ids': failure_commands if failure_commands else [(5, 0, 0)],
        }

        # Remove None values
        gift_card_vals = {k: v for k, v in gift_card_vals.items() if v is not None and v is not False}

        return gift_card_vals

    # mindbody_gift_card.py

    def synchronize(self, from_date=None, to_date=None, limit=None, gift_card_ids=None):
        """
        Synchronize gift cards from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified gift cards
            to_date (str, optional): End date for modified gift cards
            limit (int, optional): Maximum number of records to fetch
            gift_card_ids (list, optional): Specific gift card IDs to sync
            
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
            if gift_card_ids:
                params['GiftCardIDs'] = ','.join(map(str, gift_card_ids)) if isinstance(gift_card_ids,
                                                                                        list) else gift_card_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting gift card sync with params: {params}")

            # Fetch gift cards from Mindbody API
            response = api.get_sale_giftcards(params=params)
            gift_cards_data = response.get('GiftCards', []) if isinstance(response, dict) else []

            if not gift_cards_data:
                _logger.info("No gift cards found to sync")
                return stats

            _logger.info(f"Fetched {len(gift_cards_data)} gift cards from Mindbody")

            # Process each gift card
            for gift_card_data in gift_cards_data:
                try:
                    gift_card_id = gift_card_data.get('Id')
                    if not gift_card_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping gift card without ID")
                        continue

                    # Check if gift card already exists
                    existing = self.search([('gift_card_id', '=', gift_card_id)], limit=1)

                    # Prepare gift card values
                    gift_card_vals = self._prepare_gift_card(gift_card_data)

                    if existing:
                        existing.write(gift_card_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated gift card {gift_card_id}: {gift_card_data.get('Description')}")
                    else:
                        self.create(gift_card_vals)
                        stats['created'] += 1
                        _logger.info(f"Created gift card {gift_card_id}: {gift_card_data.get('Description')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing gift card {gift_card_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Gift card sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync gift cards")
            stats['errors'] += 1
            raise UserError(f"Gift card sync failed: {str(e)}")

        return stats

    # ============================================
    # Additional Synchronize Methods
    # ============================================

    def synchronize_balance(self, barcode_id=None):
        """
        Synchronize gift card balance from Mindbody to Odoo.
        
        Args:
            barcode_id (str, required): Barcode ID of the gift card
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            if not barcode_id:
                stats['errors'] += 1
                return stats

            # Prepare parameters
            params = {'barcodeId': barcode_id}

            # Fetch gift card balance from Mindbody API
            response = api.get_sale_giftcardbalance(params=params)

            if not response:
                return stats

            # Update gift card with balance
            barcode_id = response.get('BarcodeId')
            remaining_balance = response.get('RemainingBalance')

            if barcode_id and remaining_balance is not None:
                gift_card = self.search([('barcode_id', '=', barcode_id)], limit=1)
                if gift_card:
                    gift_card.write({'remaining_balance': remaining_balance})
                    stats['updated'] += 1

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Gift card balance sync failed: {str(e)}")

        return stats

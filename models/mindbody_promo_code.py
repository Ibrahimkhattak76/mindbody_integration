import logging

_logger = logging.getLogger(__name__)
# mindbody_promo_code.py
from odoo import models, fields


class MindbodyPromoCode(models.Model):
    _name = 'mindbody.promo.code'
    _description = 'Mindbody Promo Code'

    promotion_id = fields.Integer(string='Promotion ID')
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active')
    discount_id = fields.Many2one('mindbody.discount', string='Discount')
    activation_date = fields.Datetime(string='Activation Date')
    expiration_date = fields.Datetime(string='Expiration Date')
    max_uses = fields.Integer(string='Max Uses')
    number_of_autopays = fields.Integer(string='Number Of Autopays')
    days_after_close_date = fields.Integer(string='Days After Close Date')
    allow_online = fields.Boolean(string='Allow Online')
    last_modified_date_time = fields.Datetime(string='Last Modified Date Time')
    days_valid = fields.Char(string='Days Valid')  # JSON list
    applicable_item_ids = fields.One2many('mindbody.promo.applicable.item', 'promo_code_id', string='Applicable Items')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_promo_code.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_promo_code(self, data):
        """
        Prepare promo code values from API response.
        
        Args:
            data (dict): Promo code data from Mindbody API (from /site/promocodes endpoint)
            
        Returns:
            dict: Values ready for mindbody.promo.code create/write
        """
        self.ensure_one()

        # Prepare discount (Many2one)
        discount_vals = None
        if data.get('Discount'):
            discount_vals = self.env['mindbody.discount']._prepare_discount(data['Discount'])

        # Prepare applicable items (One2many)
        item_commands = []
        for item_data in data.get('ApplicableItems', []):
            item_vals = self.env['mindbody.promo.applicable.item']._prepare_promo_applicable_item(item_data)
            if item_vals:
                item_commands.append((0, 0, item_vals))

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        promo_code_vals = {
            'promotion_id': data.get('PromotionID'),
            'name': data.get('Name'),
            'code': data.get('Code'),
            'active': data.get('Active', True),
            'activation_date': data.get('ActivationDate'),
            'expiration_date': data.get('ExpirationDate'),
            'max_uses': data.get('MaxUses', 0),
            'number_of_autopays': data.get('NumberOfAutopays', 0),
            'days_after_close_date': data.get('DaysAfterCloseDate', 0),
            'allow_online': data.get('AllowOnline', False),
            'last_modified_date_time': data.get('LastModifiedDateTime'),
            'days_valid': str(data.get('DaysValid', [])),

            # One2many fields
            'applicable_item_ids': item_commands if item_commands else None,
        }

        # Add Many2one fields with create commands
        if discount_vals:
            promo_code_vals['discount_id'] = (0, 0, discount_vals)
        if pagination_vals:
            promo_code_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        promo_code_vals = {k: v for k, v in promo_code_vals.items() if v is not None and v is not False}

        return promo_code_vals

    # mindbody_promo_code.py

    def synchronize(self, from_date=None, to_date=None, limit=None, promo_code_ids=None):
        """
        Synchronize promo codes from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified promo codes
            to_date (str, optional): End date for modified promo codes
            limit (int, optional): Maximum number of records to fetch
            promo_code_ids (list, optional): Specific promo code IDs to sync
            
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
            if promo_code_ids:
                params['PromoCodeIDs'] = ','.join(map(str, promo_code_ids)) if isinstance(promo_code_ids,
                                                                                          list) else promo_code_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting promo code sync with params: {params}")

            # Fetch promo codes from Mindbody API
            response = api.get_site_promocodes(params=params)
            promocodes_data = response.get('PromoCodes', []) if isinstance(response, dict) else []

            if not promocodes_data:
                _logger.info("No promo codes found to sync")
                return stats

            _logger.info(f"Fetched {len(promocodes_data)} promo codes from Mindbody")

            # Process each promo code
            for promocode_data in promocodes_data:
                try:
                    promotion_id = promocode_data.get('PromotionID')
                    if not promotion_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping promo code without PromotionID")
                        continue

                    # Check if promo code already exists
                    existing = self.search([('promotion_id', '=', promotion_id)], limit=1)

                    # Prepare promo code values
                    promocode_vals = self._prepare_promo_code(promocode_data)

                    if existing:
                        existing.write(promocode_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated promo code {promotion_id}: {promocode_data.get('Name')}")
                    else:
                        self.create(promocode_vals)
                        stats['created'] += 1
                        _logger.info(f"Created promo code {promotion_id}: {promocode_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing promo code {promocode_data.get('PromotionID')}: {str(e)}",
                                  exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Promo code sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync promo codes")
            stats['errors'] += 1
            raise UserError(f"Promo code sync failed: {str(e)}")

        return stats

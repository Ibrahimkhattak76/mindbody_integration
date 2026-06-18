import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
from odoo import models, fields


class MindbodyAcceptedCardType(models.Model):
    _name = 'mindbody.accepted.card.type'
    _description = 'Mindbody Accepted Card Type'

    name = fields.Char(string='Card Type')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_accepted_card_type(self, data):
        """
        Prepare accepted card type values from API response.
        
        Args:
            data (str/dict): Card type string or dictionary containing card type data
            
        Returns:
            dict: Values ready for mindbody.accepted.card.type create/write
        """
        self.ensure_one()

        # Handle case where data is a string (simple array response)
        if isinstance(data, str):
            card_type_vals = {
                'name': data,
            }
        else:
            card_type_vals = {
                'name': data.get('name') or data.get('Name') or data.get('CardType'),
            }

        # Remove None values
        card_type_vals = {k: v for k, v in card_type_vals.items() if v is not None and v is not False}

        return card_type_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, card_type_ids=None):
        """
        Synchronize accepted card types from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            card_type_ids (list, optional): Not used for this endpoint
            
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

            _logger.info(f"Starting accepted card type sync with params: {params}")

            # Fetch card types from Mindbody API
            response = api.get_sale_acceptedcardtypes(params=params)

            # Handle response - this endpoint returns a simple array of strings
            card_types_data = response if isinstance(response, list) else []

            if not card_types_data:
                _logger.info("No accepted card types found to sync")
                return stats

            _logger.info(f"Fetched {len(card_types_data)} accepted card types from Mindbody")

            # Process each card type
            for card_type_data in card_types_data:
                try:
                    # Prepare card type values
                    card_type_vals = self._prepare_accepted_card_type(card_type_data)

                    # Check if card type already exists
                    existing = self.search([('name', '=', card_type_vals.get('name'))], limit=1)

                    if existing:
                        existing.write(card_type_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated accepted card type: {card_type_vals.get('name')}")
                    else:
                        self.create(card_type_vals)
                        stats['created'] += 1
                        _logger.info(f"Created accepted card type: {card_type_vals.get('name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing accepted card type: {str(e)}", exc_info=True)
                    continue

            _logger.info(f"Accepted card type sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync accepted card types")
            stats['errors'] += 1
            raise UserError(f"Accepted card type sync failed: {str(e)}")

        return stats

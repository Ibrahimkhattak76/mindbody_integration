import logging

_logger = logging.getLogger(__name__)
# mindbody_mobile_provider.py
from odoo import models, fields


class MindbodyMobileProvider(models.Model):
    _name = 'mindbody.mobile.provider'
    _description = 'Mindbody Mobile Provider'

    provider_id = fields.Integer(string='Provider ID')
    active = fields.Boolean(string='Active')
    provider_name = fields.Char(string='Provider Name')
    provider_address = fields.Char(string='Provider Address')

    # mindbody_mobile_provider.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_mobile_provider(self, data):
        """
        Prepare mobile provider values from API response.
        
        Args:
            data (dict): Mobile provider data from Mindbody API (from /site/mobileproviders endpoint)
            
        Returns:
            dict: Values ready for mindbody.mobile.provider create/write
        """
        self.ensure_one()

        provider_vals = {
            'provider_id': data.get('Id'),
            'active': data.get('Active', True),
            'provider_name': data.get('ProviderName'),
            'provider_address': data.get('ProviderAddress'),
        }

        # Remove None values
        provider_vals = {k: v for k, v in provider_vals.items() if v is not None and v is not False}

        return provider_vals

    # mindbody_mobile_provider.py

    def synchronize(self, from_date=None, to_date=None, limit=None, provider_ids=None):
        """
        Synchronize mobile providers from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            provider_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            _logger.info("Starting mobile provider sync")

            # Fetch mobile providers from Mindbody API
            response = api.get_site_mobileproviders()
            providers_data = response.get('MobileProviders', []) if isinstance(response, dict) else []

            if not providers_data:
                _logger.info("No mobile providers found to sync")
                return stats

            _logger.info(f"Fetched {len(providers_data)} mobile providers from Mindbody")

            # Process each mobile provider
            for provider_data in providers_data:
                try:
                    provider_id = provider_data.get('Id')
                    if not provider_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping mobile provider without ID")
                        continue

                    # Check if mobile provider already exists
                    existing = self.search([('provider_id', '=', provider_id)], limit=1)

                    # Prepare provider values
                    provider_vals = self._prepare_mobile_provider(provider_data)

                    if existing:
                        existing.write(provider_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated mobile provider {provider_id}: {provider_data.get('ProviderName')}")
                    else:
                        self.create(provider_vals)
                        stats['created'] += 1
                        _logger.info(f"Created mobile provider {provider_id}: {provider_data.get('ProviderName')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing mobile provider {provider_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            _logger.info(f"Mobile provider sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync mobile providers")
            stats['errors'] += 1
            raise UserError(f"Mobile provider sync failed: {str(e)}")

        return stats

import logging

_logger = logging.getLogger(__name__)
# mindbody_site.py
from odoo import models, fields


class MindbodySite(models.Model):
    _name = 'mindbody.site'
    _description = 'Mindbody Site'

    site_id = fields.Integer(string='Site ID')
    accepts_american_express = fields.Boolean(string='Accepts American Express')
    accepts_discover = fields.Boolean(string='Accepts Discover')
    accepts_master_card = fields.Boolean(string='Accepts Master Card')
    accepts_visa = fields.Boolean(string='Accepts Visa')
    allows_dashboard_access = fields.Boolean(string='Allows Dashboard Access')
    contact_email = fields.Char(string='Contact Email')
    description = fields.Text(string='Description')
    logo_url = fields.Char(string='Logo URL')
    name = fields.Char(string='Name')
    page_color1 = fields.Char(string='Page Color 1')
    page_color2 = fields.Char(string='Page Color 2')
    page_color3 = fields.Char(string='Page Color 3')
    page_color4 = fields.Char(string='Page Color 4')
    pricing_level = fields.Char(string='Pricing Level')
    sms_package_enabled = fields.Boolean(string='SMS Package Enabled')
    tax_inclusive_prices = fields.Boolean(string='Tax Inclusive Prices')
    currency_iso_code = fields.Char(string='Currency ISO Code')
    country_code = fields.Char(string='Country Code')
    time_zone = fields.Char(string='Time Zone')
    accepts_direct_debit = fields.Boolean(string='Accepts Direct Debit')
    lead_channel_ids = fields.One2many('mindbody.lead.channel', 'site_id', string='Lead Channels')
    per_staff_pricing = fields.Boolean(string='Per Staff Pricing')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # For activation code
    activation_code = fields.Char(string='Activation Code')
    activation_link = fields.Char(string='Activation Link')

    # For liability waiver
    liability_waiver = fields.Text(string='Liability Waiver')

    # mindbody_site.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_site(self, data):
        """
        Prepare site values from API response.

        Args:
            data (dict): Site data from Mindbody API (from /site/sites endpoint)

        Returns:
            dict: Values ready for mindbody.site create/write
        """
        self.ensure_one()

        # Prepare lead channels (One2many)
        channel_commands = []
        for channel_data in data.get('LeadChannels', []):
            channel_vals = self.env['mindbody.lead.channel']._prepare_lead_channel(channel_data)
            if channel_vals:
                channel_commands.append((0, 0, channel_vals))

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        site_vals = {
            'site_id': data.get('Id'),
            'accepts_american_express': data.get('AcceptsAmericanExpress', False),
            'accepts_discover': data.get('AcceptsDiscover', False),
            'accepts_master_card': data.get('AcceptsMasterCard', False),
            'accepts_visa': data.get('AcceptsVisa', False),
            'allows_dashboard_access': data.get('AllowsDashboardAccess', False),
            'contact_email': data.get('ContactEmail'),
            'description': data.get('Description'),
            'logo_url': data.get('LogoUrl'),
            'name': data.get('Name'),
            'page_color1': data.get('PageColor1'),
            'page_color2': data.get('PageColor2'),
            'page_color3': data.get('PageColor3'),
            'page_color4': data.get('PageColor4'),
            'pricing_level': data.get('PricingLevel'),
            'sms_package_enabled': data.get('SmsPackageEnabled', False),
            'tax_inclusive_prices': data.get('TaxInclusivePrices', False),
            'currency_iso_code': data.get('CurrencyIsoCode'),
            'country_code': data.get('CountryCode'),
            'time_zone': data.get('TimeZone'),
            'accepts_direct_debit': data.get('AcceptsDirectDebit', False),
            'per_staff_pricing': data.get('PerStaffPricing', False),

            # For activation code
            'activation_code': data.get('ActivationCode'),
            'activation_link': data.get('ActivationLink'),

            # For liability waiver
            'liability_waiver': data.get('LiabilityWaiver'),

            # One2many fields
            'lead_channel_ids': channel_commands if channel_commands else None,
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            site_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        site_vals = {k: v for k, v in site_vals.items() if v is not None and v is not False}

        return site_vals

    # mindbody_site.py

    def synchronize(self, from_date=None, to_date=None, limit=None, site_ids=None):
        """
        Synchronize sites from Mindbody to Odoo.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            site_ids (list, optional): Specific site IDs to sync

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
            if site_ids:
                params['SiteIDs'] = ','.join(map(str, site_ids)) if isinstance(site_ids, list) else site_ids

            _logger.info(f"Starting site sync with params: {params}")

            # Fetch sites from Mindbody API
            response = api.get_site_sites(params=params)
            sites_data = response.get('Sites', []) if isinstance(response, dict) else []

            if not sites_data:
                _logger.info("No sites found to sync")
                return stats

            _logger.info(f"Fetched {len(sites_data)} sites from Mindbody")

            # Process each site
            for site_data in sites_data:
                try:
                    site_id = site_data.get('Id')
                    if not site_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping site without ID")
                        continue

                    # Check if site already exists
                    existing = self.search([('site_id', '=', site_id)], limit=1)

                    # Prepare site values
                    site_vals = self._prepare_site(site_data)

                    if existing:
                        existing.write(site_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated site {site_id}: {site_data.get('Name')}")
                    else:
                        self.create(site_vals)
                        stats['created'] += 1
                        _logger.info(f"Created site {site_id}: {site_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing site {site_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Site sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync sites")
            stats['errors'] += 1
            raise UserError(f"Site sync failed: {str(e)}")

        return stats

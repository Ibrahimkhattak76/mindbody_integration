import logging

_logger = logging.getLogger(__name__)
# mindbody_package.py
from odoo import models, fields


class MindbodyPackage(models.Model):
    _name = 'mindbody.package'
    _description = 'Mindbody Package'

    package_id = fields.Integer(string='Package ID')
    name = fields.Char(string='Name')
    discount_percentage = fields.Float(string='Discount Percentage')
    sell_online = fields.Boolean(string='Sell Online')

    # Relations
    service_ids = fields.One2many('mindbody.package.service', 'package_id', string='Services')
    product_ids = fields.One2many('mindbody.package.product', 'package_id', string='Products')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_package.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_package(self, data):
        """
        Prepare package values from API response.
        
        Args:
            data (dict): Package data from Mindbody API (from /sale/packages endpoint)
            
        Returns:
            dict: Values ready for mindbody.package create/write
        """
        self.ensure_one()

        # Prepare services (One2many)
        service_commands = []
        for service_data in data.get('Services', []):
            service_vals = self.env['mindbody.package.service']._prepare_package_service(service_data)
            if service_vals:
                service_commands.append((0, 0, service_vals))

        # Prepare products (One2many)
        product_commands = []
        for product_data in data.get('Products', []):
            product_vals = self.env['mindbody.package.product']._prepare_package_product(product_data)
            if product_vals:
                product_commands.append((0, 0, product_vals))

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        # Build package values
        package_vals = {
            'package_id': data.get('Id'),
            'name': data.get('Name'),
            'discount_percentage': data.get('DiscountPercentage', 0.0),
            'sell_online': data.get('SellOnline', False),

            # One2many fields
            'service_ids': service_commands if service_commands else None,
            'product_ids': product_commands if product_commands else None,
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            package_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        package_vals = {k: v for k, v in package_vals.items() if v is not None and v is not False}

        return package_vals

    # mindbody_package.py

    def synchronize(self, from_date=None, to_date=None, limit=None, package_ids=None):
        """
        Synchronize packages from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified packages
            to_date (str, optional): End date for modified packages
            limit (int, optional): Maximum number of records to fetch
            package_ids (list, optional): Specific package IDs to sync
            
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
            if package_ids:
                params['PackageIDs'] = ','.join(map(str, package_ids)) if isinstance(package_ids, list) else package_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting package sync with params: {params}")

            # Fetch packages from Mindbody API
            response = api.get_sale_packages(params=params)
            packages_data = response.get('Packages', []) if isinstance(response, dict) else []

            if not packages_data:
                _logger.info("No packages found to sync")
                return stats

            _logger.info(f"Fetched {len(packages_data)} packages from Mindbody")

            # Process each package
            for package_data in packages_data:
                try:
                    package_id = package_data.get('Id')
                    if not package_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping package without ID")
                        continue

                    # Check if package already exists
                    existing = self.search([('package_id', '=', package_id)], limit=1)

                    # Prepare package values
                    package_vals = self._prepare_package(package_data)

                    if existing:
                        existing.write(package_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated package {package_id}: {package_data.get('Name')}")
                    else:
                        self.create(package_vals)
                        stats['created'] += 1
                        _logger.info(f"Created package {package_id}: {package_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing package {package_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Package sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync packages")
            stats['errors'] += 1
            raise UserError(f"Package sync failed: {str(e)}")

        return stats

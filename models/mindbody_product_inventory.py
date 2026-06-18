import logging

_logger = logging.getLogger(__name__)
# mindbody_product_inventory.py
from odoo import models, fields


class MindbodyProductInventory(models.Model):
    _name = 'mindbody.product.inventory'
    _description = 'Mindbody Product Inventory'

    product_id = fields.Integer(string='Product ID')
    barcode_id = fields.Char(string='Barcode ID')
    location_id = fields.Integer(string='Location ID')
    units_logged = fields.Float(string='Units Logged')
    units_sold = fields.Float(string='Units Sold')
    units_in_stock = fields.Float(string='Units In Stock')
    reorder_level = fields.Float(string='Reorder Level')
    max_level = fields.Float(string='Max Level')
    created_date_time_utc = fields.Datetime(string='Created Date Time UTC')
    modified_date_time_utc = fields.Datetime(string='Modified Date Time UTC')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_product_inventory.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_product_inventory(self, data):
        """
        Prepare product inventory values from API response.
        
        Args:
            data (dict): Product inventory data from Mindbody API (from /sale/productsinventory endpoint)
            
        Returns:
            dict: Values ready for mindbody.product.inventory create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        inventory_vals = {
            'product_id': data.get('ProductId'),
            'barcode_id': data.get('BarcodeId'),
            'location_id': data.get('LocationId'),
            'units_logged': data.get('UnitsLogged', 0.0),
            'units_sold': data.get('UnitsSold', 0.0),
            'units_in_stock': data.get('UnitsInStock', 0.0),
            'reorder_level': data.get('ReorderLevel', 0.0),
            'max_level': data.get('MaxLevel', 0.0),
            'created_date_time_utc': data.get('CreatedDateTimeUTC'),
            'modified_date_time_utc': data.get('ModifiedDateTimeUTC'),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            inventory_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        inventory_vals = {k: v for k, v in inventory_vals.items() if v is not None and v is not False}

        return inventory_vals

    # mindbody_product_inventory.py

    def synchronize(self, from_date=None, to_date=None, limit=None, inventory_ids=None):
        """
        Synchronize product inventory from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified inventory
            to_date (str, optional): End date for modified inventory
            limit (int, optional): Maximum number of records to fetch
            inventory_ids (list, optional): Specific inventory IDs to sync
            
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
            if inventory_ids:
                params['InventoryIDs'] = ','.join(map(str, inventory_ids)) if isinstance(inventory_ids,
                                                                                         list) else inventory_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting product inventory sync with params: {params}")

            # Fetch product inventory from Mindbody API
            response = api.get_sale_productsinventory(params=params)
            inventory_data = response.get('ProductsInventory', []) if isinstance(response, dict) else []

            if not inventory_data:
                _logger.info("No product inventory found to sync")
                return stats

            _logger.info(f"Fetched {len(inventory_data)} product inventory records from Mindbody")

            # Process each inventory record
            for inventory_item in inventory_data:
                try:
                    product_id = inventory_item.get('ProductId')
                    location_id = inventory_item.get('LocationId')

                    if not product_id or not location_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping inventory without ProductId or LocationId")
                        continue

                    # Check if inventory already exists
                    existing = self.search([
                        ('product_id', '=', product_id),
                        ('location_id', '=', location_id)
                    ], limit=1)

                    # Prepare inventory values
                    inventory_vals = self._prepare_product_inventory(inventory_item)

                    if existing:
                        existing.write(inventory_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated inventory for product {product_id} at location {location_id}")
                    else:
                        self.create(inventory_vals)
                        stats['created'] += 1
                        _logger.info(f"Created inventory for product {product_id} at location {location_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing inventory: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Product inventory sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync product inventory")
            stats['errors'] += 1
            raise UserError(f"Product inventory sync failed: {str(e)}")

        return stats

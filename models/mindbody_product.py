import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyProduct(models.Model):
    _name = 'mindbody.product'
    _description = 'Mindbody Product'

    product_id = fields.Integer(string='Product ID')
    product_uuid = fields.Char(string='Product UUID')
    category_id = fields.Many2one('mindbody.category', string='Category')
    sub_category_id = fields.Many2one('mindbody.category', string='Sub Category', )
    # domain="[('parent_id', '=', category_id)]"
    # secondary_category_id = fields.Many2one(
    #     'mindbody.category',
    #     string='Secondary Category'
    # )
    secondary_category_id = fields.Integer(string='Secondary Category ID')
    price = fields.Float(string='Price')
    tax_included = fields.Float(string='Tax Included')
    tax_rate = fields.Float(string='Tax Rate')
    group_id = fields.Integer(string='Group ID')
    name = fields.Char(string='Name')
    online_price = fields.Float(string='Online Price')
    short_description = fields.Text(string='Short Description')
    long_description = fields.Text(string='Long Description')
    type_group = fields.Integer(string='Type Group')
    supplier_id = fields.Integer(string='Supplier ID')
    supplier_name = fields.Char(string='Supplier Name')
    image_url = fields.Char(string='Image URL')
    color_id = fields.Many2one('mindbody.product.color', string='Color')
    size_id = fields.Many2one('mindbody.product.size', string='Size')
    manufacturer_id = fields.Char(string='Manufacturer ID')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # Prepare Methods

    def _prepare_product(self, data):
        """
        Prepare product values from API response.

        Args:
            data (dict): Product data from Mindbody API (from /sale/products endpoint)

        Returns:
            dict: Values ready for mindbody.product create/write
        """
        category_model = self.env['mindbody.category']

        category = category_model.get_by_external_id(data.get('CategoryId', 0))

        sub_category = category_model.get_by_external_id(data.get('SubCategoryId', 0))

        product_vals = {
            'product_id': data.get('ProductId'),
            'product_uuid': data.get('Id'),
            'category_id': category.id if category else False,
            'sub_category_id': sub_category.id if sub_category else False,
            'secondary_category_id': data.get('SecondaryCategoryId'),
            'price': data.get('Price', 0.0),
            'tax_included': data.get('TaxIncluded', 0.0),
            'tax_rate': data.get('TaxRate', 0.0),
            'group_id': data.get('GroupId'),
            'name': data.get('Name'),
            'online_price': data.get('OnlinePrice', 0.0),
            'short_description': data.get('ShortDescription'),
            'long_description': data.get('LongDescription'),
            'type_group': data.get('TypeGroup', 0),
            'supplier_id': data.get('SupplierId'),
            'supplier_name': data.get('SupplierName'),
            'image_url': data.get('ImageURL'),
            'manufacturer_id': data.get('ManufacturerId'),
        }

        color = self.env['mindbody.product.color'].get_color(data['Color'])
        if color:
            product_vals['color_id'] = color.id

        size = self.env['mindbody.product.size'].get_size(data['Size'])
        if size:
            product_vals['size_id'] = size.id

        # Remove None values
        product_vals = {k: v for k, v in product_vals.items() if v is not None and v is not False}

        return product_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, product_ids=None):
        """
        Synchronize products from Mindbody to Odoo.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit  # Max 200 per page
            if product_ids:
                params['ProductIDs'] = ','.join(map(str, product_ids)) if isinstance(product_ids, list) else product_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            offset = 0
            while True:
                params['Offset'] = offset

                _logger.info(f"Fetching products with Offset={offset}")
                response = api.get_sale_products(params=params)
                products_data = response.get('Products', []) if isinstance(response, dict) else []

                if not products_data:
                    break  # No more pages

                _logger.info(f"Fetched {len(products_data)} products from page")

                for product_data in products_data:
                    try:
                        product_id = product_data.get('ProductId')
                        if not product_id:
                            stats['skipped'] += 1
                            continue

                        existing = self.search([('product_id', '=', product_id)], limit=1)
                        product_vals = self._prepare_product(product_data)

                        if existing:
                            existing.write(product_vals)
                            stats['updated'] += 1
                        else:
                            self.create(product_vals)
                            stats['created'] += 1

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error: {str(e)}", exc_info=True)
                        continue

                # Pagination check
                pagination_info = response.get('PaginationResponse', {})
                total_results = pagination_info.get('TotalResults', 0)
                page_size = pagination_info.get('PageSize', 100)

                if offset + page_size >= total_results:
                    break  # All pages done

                offset += page_size  # Next page

                # Save pagination info
                if pagination_info:
                    self.env['mindbody.pagination.response'].create(
                        self.env['mindbody.pagination.response']._prepare_pagination_response(pagination_info)
                    )

            _logger.info(f"Product sync completed: {stats}")

        except Exception as e:
            _logger.exception("Failed to sync products")
            raise UserError(f"Product sync failed: {str(e)}")

        return stats
    # def synchronize(self, from_date=None, to_date=None, limit=None, product_ids=None):
    #     """
    #     Synchronize products from Mindbody to Odoo.
    #
    #     Args:
    #         from_date (str, optional): Start date for modified products
    #         to_date (str, optional): End date for modified products
    #         limit (int, optional): Maximum number of records to fetch
    #         product_ids (list, optional): Specific product IDs to sync
    #
    #     Returns:
    #         dict: Statistics of created/updated records
    #     """
    #     api = self.env['mindbody.api']
    #     stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
    #
    #     try:
    #         # Prepare parameters
    #         params = {}
    #         if limit:
    #             params['Limit'] = limit
    #         if product_ids:
    #             params['ProductIDs'] = ','.join(map(str, product_ids)) if isinstance(product_ids, list) else product_ids
    #         if from_date:
    #             params['ModifiedDateTime'] = from_date
    #             if to_date:
    #                 params['ModifiedDateTime'] = f"{from_date},{to_date}"
    #
    #         _logger.info(f"Starting product sync with params: {params}")
    #
    #         # Fetch products from Mindbody API
    #         response = api.get_sale_products(params=params)
    #         products_data = response.get('Products', []) if isinstance(response, dict) else []
    #
    #         if not products_data:
    #             _logger.info("No products found to sync")
    #             return stats
    #
    #         _logger.info(f"Fetched {len(products_data)} products from Mindbody")
    #
    #         # Process each product
    #         for product_data in products_data:
    #             try:
    #                 product_id = product_data.get('ProductId')
    #                 if not product_id:
    #                     stats['skipped'] += 1
    #                     _logger.warning("Skipping product without ProductId")
    #                     continue
    #
    #                 # Check if product already exists
    #                 existing = self.search([('product_id', '=', product_id)], limit=1)
    #
    #                 # Prepare product values
    #                 product_vals = self._prepare_product(product_data)
    #
    #                 if existing:
    #                     existing.write(product_vals)
    #                     stats['updated'] += 1
    #                     _logger.info(f"Updated product {product_id}: {product_data.get('Name')}")
    #                 else:
    #                     self.create(product_vals)
    #                     stats['created'] += 1
    #                     _logger.info(f"Created product {product_id}: {product_data.get('Name')}")
    #
    #             except Exception as e:
    #                 stats['errors'] += 1
    #                 _logger.error(f"Error processing product {product_data.get('ProductId')}: {str(e)}", exc_info=True)
    #                 continue
    #
    #         # Save pagination info if available
    #         if isinstance(response, dict) and response.get('PaginationResponse'):
    #             pagination = self.env['mindbody.pagination.response']
    #             # pagination.create()
    #             print(pagination._prepare_pagination_response(response['PaginationResponse']))
    #
    #         _logger.info(f"Product sync completed: {stats['created']} created, {stats['updated']} updated, "
    #                      f"{stats['errors']} errors, {stats['skipped']} skipped")
    #
    #     except Exception as e:
    #         _logger.exception("Failed to sync products")
    #         stats['errors'] += 1
    #         raise UserError(f"Product sync failed: {str(e)}")
    #
    #     return stats

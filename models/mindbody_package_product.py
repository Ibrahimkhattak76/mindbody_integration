import logging

_logger = logging.getLogger(__name__)
# mindbody_package_product.py
from odoo import models, fields


class MindbodyPackageProduct(models.Model):
    _name = 'mindbody.package.product'
    _description = 'Mindbody Package Product'

    package_id = fields.Many2one('mindbody.package', string='Package')

    product_id = fields.Integer(string='Product ID')
    product_uuid = fields.Char(string='Product UUID')
    category_id = fields.Integer(string='Category ID')
    sub_category_id = fields.Integer(string='Sub Category ID')
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

    # mindbody_package_product.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_package_product(self, data):
        """
        Prepare package product values from API response.
        
        Args:
            data (dict): Package product data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.package.product create/write
        """
        self.ensure_one()

        # Prepare color (Many2one)
        color_vals = None
        if data.get('Color'):
            color_vals = self.env['mindbody.product.color']._prepare_product_color(data['Color'])

        # Prepare size (Many2one)
        size_vals = None
        if data.get('Size'):
            size_vals = self.env['mindbody.product.size']._prepare_product_size(data['Size'])

        package_product_vals = {
            'product_id': data.get('ProductId'),
            'product_uuid': data.get('Id'),
            'category_id': data.get('CategoryId'),
            'sub_category_id': data.get('SubCategoryId'),
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

        # Add Many2one fields with create commands
        if color_vals:
            package_product_vals['color_id'] = (0, 0, color_vals)
        if size_vals:
            package_product_vals['size_id'] = (0, 0, size_vals)

        # Remove None values
        package_product_vals = {k: v for k, v in package_product_vals.items() if v is not None and v is not False}

        return package_product_vals

    # mindbody_package_product.py

    def synchronize(self, from_date=None, to_date=None, limit=None, package_product_ids=None):
        """
        Synchronize package products from Mindbody to Odoo.
        Note: Package products are typically synced as part of package sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            package_product_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Package products are synced automatically during package sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

import logging

_logger = logging.getLogger(__name__)
# mindbody_package_service.py
from odoo import models, fields


class MindbodyPackageService(models.Model):
    _name = 'mindbody.package.service'
    _description = 'Mindbody Package Service'

    package_id = fields.Many2one('mindbody.package', string='Package')

    price = fields.Float(string='Price')
    online_price = fields.Float(string='Online Price')
    tax_included = fields.Float(string='Tax Included')
    program_id = fields.Integer(string='Program ID')
    tax_rate = fields.Float(string='Tax Rate')
    product_id = fields.Integer(string='Product ID')
    service_id = fields.Char(string='Service ID')
    name = fields.Char(string='Name')
    count = fields.Integer(string='Count')
    sell_online = fields.Boolean(string='Sell Online')
    sale_in_contract_only = fields.Boolean(string='Sale In Contract Only')
    service_type = fields.Char(string='Type')
    expiration_type = fields.Char(string='Expiration Type')
    expiration_unit = fields.Char(string='Expiration Unit')
    expiration_length = fields.Integer(string='Expiration Length')
    revenue_category = fields.Char(string='Revenue Category')
    membership_id = fields.Integer(string='Membership ID')
    sell_at_location_ids = fields.Char(string='Sell At Location IDs')  # JSON list
    use_at_location_ids = fields.Char(string='Use At Location IDs')  # JSON list
    priority = fields.Char(string='Priority')
    is_intro_offer = fields.Boolean(string='Is Intro Offer')
    intro_offer_type = fields.Char(string='Intro Offer Type')
    is_third_party_discount_pricing = fields.Boolean(string='Is Third Party Discount Pricing')
    program = fields.Char(string='Program')
    discontinued = fields.Boolean(string='Discontinued')
    restrict_to_membership_ids = fields.Char(string='Restrict To Membership IDs')  # JSON list
    apply_member_discounts_of_membership_ids = fields.Char(
        string='Apply Member Discounts Of Membership IDs')  # JSON list

    # mindbody_package_service.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_package_service(self, data):
        """
        Prepare package service values from API response.
        
        Args:
            data (dict): Package service data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.package.service create/write
        """
        self.ensure_one()

        package_service_vals = {
            'price': data.get('Price', 0.0),
            'online_price': data.get('OnlinePrice', 0.0),
            'tax_included': data.get('TaxIncluded', 0.0),
            'program_id': data.get('ProgramId'),
            'tax_rate': data.get('TaxRate', 0.0),
            'product_id': data.get('ProductId'),
            'service_id': data.get('Id'),
            'name': data.get('Name'),
            'count': data.get('Count', 0),
            'sell_online': data.get('SellOnline', False),
            'sale_in_contract_only': data.get('SaleInContractOnly', False),
            'service_type': data.get('Type'),
            'expiration_type': data.get('ExpirationType'),
            'expiration_unit': data.get('ExpirationUnit'),
            'expiration_length': data.get('ExpirationLength', 0),
            'revenue_category': data.get('RevenueCategory'),
            'membership_id': data.get('MembershipId'),
            'sell_at_location_ids': str(data.get('SellAtLocationIds', [])),
            'use_at_location_ids': str(data.get('UseAtLocationIds', [])),
            'priority': data.get('Priority'),
            'is_intro_offer': data.get('IsIntroOffer', False),
            'intro_offer_type': data.get('IntroOfferType'),
            'is_third_party_discount_pricing': data.get('IsThirdPartyDiscountPricing', False),
            'program': data.get('Program'),
            'discontinued': data.get('Discontinued', False),
            'restrict_to_membership_ids': str(data.get('RestrictToMembershipIds', [])),
            'apply_member_discounts_of_membership_ids': str(data.get('ApplyMemberDiscountsOfMembershipIds', [])),
        }

        # Remove None values
        package_service_vals = {k: v for k, v in package_service_vals.items() if v is not None and v is not False}

        return package_service_vals

    # mindbody_package_service.py

    def synchronize(self, from_date=None, to_date=None, limit=None, package_service_ids=None):
        """
        Synchronize package services from Mindbody to Odoo.
        Note: Package services are typically synced as part of package sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            package_service_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Package services are synced automatically during package sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

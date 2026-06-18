import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
# mindbody_service.py
from odoo import models, fields


class MindbodyService(models.Model):
    _name = 'mindbody.service'
    _description = 'Mindbody Service'

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

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # For client services
    active_date = fields.Datetime(string='Active Date')
    current = fields.Boolean(string='Current')
    expiration_date = fields.Datetime(string='Expiration Date')
    client_service_id = fields.Integer(string='Client Service ID')
    payment_date = fields.Datetime(string='Payment Date')
    remaining = fields.Integer(string='Remaining')
    site_id = fields.Integer(string='Site ID')
    client_id = fields.Char(string='Client ID')
    returned = fields.Boolean(string='Returned')
    activation_type = fields.Selection([
        ('OnFirstVisit', 'On First Visit')
    ], string='Activation Type')
    cannot_pay_for_classes_before_activation = fields.Boolean(string='Cannot Pay For Classes Before Activation')

    # mindbody_service.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_service(self, data):
        """
        Prepare service values from API response.
        """

        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        service_vals = {
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

            # Client services
            'active_date': data.get('ActiveDate'),
            'current': data.get('Current', False),
            'expiration_date': data.get('ExpirationDate'),
            'client_service_id': data.get('Id'),
            'payment_date': data.get('PaymentDate'),
            'remaining': data.get('Remaining', 0),
            'site_id': data.get('SiteId'),
            'client_id': data.get('ClientID'),
            'returned': data.get('Returned', False),
            'activation_type': data.get('ActivationType'),
            'cannot_pay_for_classes_before_activation': data.get('CannotPayForClassesBeforeActivation', False),
        }

        if pagination_vals:
            service_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # clean None values only (don?t remove False blindly)
        service_vals = {k: v for k, v in service_vals.items() if v is not None}

        return service_vals

    # mindbody_service.py

    def synchronize(self, from_date=None, to_date=None, limit=None, service_ids=None):
        """
        Synchronize services from Mindbody to Odoo.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            base_params = {}
            if service_ids:
                base_params['ServiceIDs'] = ','.join(map(str, service_ids)) if isinstance(service_ids,
                                                                                          list) else service_ids
            if from_date:
                base_params['ModifiedDateTime'] = from_date
                if to_date:
                    base_params['ModifiedDateTime'] = f"{from_date},{to_date}"

            offset = 0
            page_size = limit or 100

            while True:
                params = dict(base_params)
                params['Limit'] = page_size
                params['Offset'] = offset

                _logger.info(f"Starting service sync with params: {params}")

                response = api.get_sale_services(params=params)
                services_data = response.get('Services', []) if isinstance(response, dict) else []
                pagination = response.get('PaginationResponse', {}) if isinstance(response, dict) else {}

                if not services_data:
                    _logger.info("No more services found")
                    break

                _logger.info(f"Fetched {len(services_data)} services from Mindbody (Offset: {offset})")

                # Process each service
                for service_data in services_data:
                    try:
                        service_id = service_data.get('Id')
                        if not service_id:
                            stats['skipped'] += 1
                            _logger.warning("Skipping service without ID")
                            continue

                        existing = self.search([('service_id', '=', service_id)], limit=1)
                        service_vals = self._prepare_service(service_data)

                        if existing:
                            existing.write(service_vals)
                            stats['updated'] += 1
                            _logger.info(f"Updated service {service_id}: {service_data.get('Name')}")
                        else:
                            self.create(service_vals)
                            stats['created'] += 1
                            _logger.info(f"Created service {service_id}: {service_data.get('Name')}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing service {service_data.get('Id')}: {str(e)}", exc_info=True)
                        continue

                # Check if more pages
                total_results = pagination.get('TotalResults', 0)
                offset += page_size

                if offset >= total_results:
                    _logger.info(f"All pages done. Total services: {stats['created'] + stats['updated']}")
                    break

            # Save last pagination info
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Service sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync services")
            stats['errors'] += 1
            raise UserError(f"Service sync failed: {str(e)}")

        return stats

# import logging
#
# _logger = logging.getLogger(__name__)
# # mindbody_service.py
# from odoo import models, fields
#
#
# class MindbodyService(models.Model):
#     _name = 'mindbody.service'
#     _description = 'Mindbody Service'
#
#     price = fields.Float(string='Price')
#     online_price = fields.Float(string='Online Price')
#     tax_included = fields.Float(string='Tax Included')
#     program_id = fields.Integer(string='Program ID')
#     tax_rate = fields.Float(string='Tax Rate')
#     product_id = fields.Integer(string='Product ID')
#     service_id = fields.Char(string='Service ID')
#     name = fields.Char(string='Name')
#     count = fields.Integer(string='Count')
#     sell_online = fields.Boolean(string='Sell Online')
#     sale_in_contract_only = fields.Boolean(string='Sale In Contract Only')
#     service_type = fields.Char(string='Type')
#     expiration_type = fields.Char(string='Expiration Type')
#     expiration_unit = fields.Char(string='Expiration Unit')
#     expiration_length = fields.Integer(string='Expiration Length')
#     revenue_category = fields.Char(string='Revenue Category')
#     membership_id = fields.Integer(string='Membership ID')
#     sell_at_location_ids = fields.Char(string='Sell At Location IDs')  # JSON list
#     use_at_location_ids = fields.Char(string='Use At Location IDs')  # JSON list
#     priority = fields.Char(string='Priority')
#     is_intro_offer = fields.Boolean(string='Is Intro Offer')
#     intro_offer_type = fields.Char(string='Intro Offer Type')
#     is_third_party_discount_pricing = fields.Boolean(string='Is Third Party Discount Pricing')
#     program = fields.Char(string='Program')
#     discontinued = fields.Boolean(string='Discontinued')
#     restrict_to_membership_ids = fields.Char(string='Restrict To Membership IDs')  # JSON list
#     apply_member_discounts_of_membership_ids = fields.Char(
#         string='Apply Member Discounts Of Membership IDs')  # JSON list
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     # For client services
#     active_date = fields.Datetime(string='Active Date')
#     current = fields.Boolean(string='Current')
#     expiration_date = fields.Datetime(string='Expiration Date')
#     client_service_id = fields.Integer(string='Client Service ID')
#     payment_date = fields.Datetime(string='Payment Date')
#     remaining = fields.Integer(string='Remaining')
#     site_id = fields.Integer(string='Site ID')
#     client_id = fields.Char(string='Client ID')
#     returned = fields.Boolean(string='Returned')
#     activation_type = fields.Selection([
#         ('OnFirstVisit', 'On First Visit')
#     ], string='Activation Type')
#     cannot_pay_for_classes_before_activation = fields.Boolean(string='Cannot Pay For Classes Before Activation')
#
#     # mindbody_service.py
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_service(self, data):
#         """
#         Prepare service values from API response.
#
#         Args:
#             data (dict): Service data from Mindbody API (from /sale/services endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.service create/write
#         """
#         self.ensure_one()
#
#         # Prepare pagination (Many2one)
#         pagination_vals = None
#         if data.get('PaginationResponse'):
#             pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
#                 data['PaginationResponse']
#             )
#
#         service_vals = {
#             'price': data.get('Price', 0.0),
#             'online_price': data.get('OnlinePrice', 0.0),
#             'tax_included': data.get('TaxIncluded', 0.0),
#             'program_id': data.get('ProgramId'),
#             'tax_rate': data.get('TaxRate', 0.0),
#             'product_id': data.get('ProductId'),
#             'service_id': data.get('Id'),
#             'name': data.get('Name'),
#             'count': data.get('Count', 0),
#             'sell_online': data.get('SellOnline', False),
#             'sale_in_contract_only': data.get('SaleInContractOnly', False),
#             'service_type': data.get('Type'),
#             'expiration_type': data.get('ExpirationType'),
#             'expiration_unit': data.get('ExpirationUnit'),
#             'expiration_length': data.get('ExpirationLength', 0),
#             'revenue_category': data.get('RevenueCategory'),
#             'membership_id': data.get('MembershipId'),
#             'sell_at_location_ids': str(data.get('SellAtLocationIds', [])),
#             'use_at_location_ids': str(data.get('UseAtLocationIds', [])),
#             'priority': data.get('Priority'),
#             'is_intro_offer': data.get('IsIntroOffer', False),
#             'intro_offer_type': data.get('IntroOfferType'),
#             'is_third_party_discount_pricing': data.get('IsThirdPartyDiscountPricing', False),
#             'program': data.get('Program'),
#             'discontinued': data.get('Discontinued', False),
#             'restrict_to_membership_ids': str(data.get('RestrictToMembershipIds', [])),
#             'apply_member_discounts_of_membership_ids': str(data.get('ApplyMemberDiscountsOfMembershipIds', [])),
#
#             # For client services
#             'active_date': data.get('ActiveDate'),
#             'current': data.get('Current', False),
#             'expiration_date': data.get('ExpirationDate'),
#             'client_service_id': data.get('Id'),
#             'payment_date': data.get('PaymentDate'),
#             'remaining': data.get('Remaining', 0),
#             'site_id': data.get('SiteId'),
#             'client_id': data.get('ClientID'),
#             'returned': data.get('Returned', False),
#             'activation_type': data.get('ActivationType'),
#             'cannot_pay_for_classes_before_activation': data.get('CannotPayForClassesBeforeActivation', False),
#         }
#
#         # Add Many2one fields with create commands
#         if pagination_vals:
#             service_vals['pagination_response_id'] = (0, 0, pagination_vals)
#
#         # Remove None values
#         service_vals = {k: v for k, v in service_vals.items() if v is not None and v is not False}
#
#         return service_vals
#
#     # mindbody_service.py
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, service_ids=None):
#         """
#         Synchronize services from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Start date for modified services
#             to_date (str, optional): End date for modified services
#             limit (int, optional): Maximum number of records to fetch
#             service_ids (list, optional): Specific service IDs to sync
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             # Prepare parameters
#             params = {}
#             if limit:
#                 params['Limit'] = limit
#             if service_ids:
#                 params['ServiceIDs'] = ','.join(map(str, service_ids)) if isinstance(service_ids, list) else service_ids
#             if from_date:
#                 params['ModifiedDateTime'] = from_date
#                 if to_date:
#                     params['ModifiedDateTime'] = f"{from_date},{to_date}"
#
#             _logger.info(f"Starting service sync with params: {params}")
#
#             # Fetch services from Mindbody API
#             response = api.get_sale_services(params=params)
#             services_data = response.get('Services', []) if isinstance(response, dict) else []
#
#             if not services_data:
#                 _logger.info("No services found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(services_data)} services from Mindbody")
#
#             # Process each service
#             for service_data in services_data:
#                 try:
#                     service_id = service_data.get('Id')
#                     if not service_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping service without ID")
#                         continue
#
#                     # Check if service already exists
#                     existing = self.search([('service_id', '=', service_id)], limit=1)
#
#                     # Prepare service values
#                     service_vals = self._prepare_service(service_data)
#
#                     if existing:
#                         existing.write(service_vals)
#                         stats['updated'] += 1
#                         _logger.info(f"Updated service {service_id}: {service_data.get('Name')}")
#                     else:
#                         self.create(service_vals)
#                         stats['created'] += 1
#                         _logger.info(f"Created service {service_id}: {service_data.get('Name')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing service {service_data.get('Id')}: {str(e)}", exc_info=True)
#                     continue
#
#             # Save pagination info if available
#             if isinstance(response, dict) and response.get('PaginationResponse'):
#                 self.env['mindbody.pagination.response'].create(
#                     self.env['mindbody.pagination.response']._prepare_pagination_response(
#                         response['PaginationResponse'])
#                 )
#
#             _logger.info(f"Service sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync services")
#             stats['errors'] += 1
#             raise UserError(f"Service sync failed: {str(e)}")
#
#         return stats

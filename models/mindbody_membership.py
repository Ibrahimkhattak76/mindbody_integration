import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from odoo import models, fields


class MindbodyMembership(models.Model):
    _name = 'mindbody.membership'
    _description = 'Mindbody Membership'
    _rec_name = 'membership_name'

    membership_id = fields.Integer(string='Membership ID')
    membership_name = fields.Char(string='Membership Name')
    priority = fields.Integer(string='Priority')
    member_retail_discount = fields.Float(string='Member Retail Discount')
    member_service_discount = fields.Float(string='Member Service Discount')
    allow_clients_to_schedule_unpaid = fields.Boolean(string='Allow Clients To Schedule Unpaid')
    online_booking_restricted_to_members_only = fields.Char(
        string='Online Booking Restricted To Members Only')  # JSON list
    day_of_month_scheduling_opens_for_next_month = fields.Integer(string='Day Of Month Scheduling Opens For Next Month')
    restrict_self_sign_in_to_members_only = fields.Boolean(string='Restrict Self Sign In To Members Only')
    allow_members_to_book_appointments_without_paying = fields.Boolean(
        string='Allow Members To Book Appointments Without Paying')
    allow_members_to_purchase_non_members_services = fields.Boolean(
        string='Allow Members To Purchase Non Members Services')
    allow_members_to_purchase_non_members_products = fields.Boolean(
        string='Allow Members To Purchase Non Members Products')
    is_active = fields.Boolean(string='Is Active')
    early_access_days_before_scheduling_window = fields.Integer(string='Early Access Days Before Scheduling Window')

    # For client memberships
    restricted_location_ids = fields.Many2many('mindbody.location', string='Restricted Locations')
    icon_code = fields.Char(string='Icon Code')
    active_date = fields.Datetime(string='Active Date')
    count = fields.Integer(string='Count')
    current = fields.Boolean(string='Current')
    expiration_date = fields.Datetime(string='Expiration Date')
    client_membership_id = fields.Integer(string='Client Membership ID')
    product_id = fields.Integer(string='Product ID')
    payment_date = fields.Datetime(string='Payment Date')
    program_id_ref = fields.Many2one('mindbody.program', string='Program')
    remaining = fields.Integer(string='Remaining')
    site_id = fields.Integer(string='Site ID')
    client_id = fields.Char(string='Client ID')
    returned = fields.Boolean(string='Returned')

    # Prepare Methods
    def _prepare_membership(self, data):
        """
        Prepare membership values from API response.
        Args:
            data (dict): Membership data from Mindbody API (from /site/memberships endpoint)
        Returns:
            dict: Values ready for mindbody.membership create/write
        """
        membership_vals = {
            'membership_id': data.get('MembershipId'),
            'membership_name': data.get('MembershipName'),
            'priority': data.get('Priority', 0),
            'member_retail_discount': data.get('MemberRetailDiscount', 0.0),
            'member_service_discount': data.get('MemberServiceDiscount', 0.0),
            'allow_clients_to_schedule_unpaid': data.get('AllowClientsToScheduleUnpaid', False),
            'online_booking_restricted_to_members_only': str(data.get('OnlineBookingRestrictedToMembersOnly', [])),
            'day_of_month_scheduling_opens_for_next_month': data.get('DayOfMonthSchedulingOpensForNextMonth', 0),
            'restrict_self_sign_in_to_members_only': data.get('RestrictSelfSignInToMembersOnly', False),
            'allow_members_to_book_appointments_without_paying': data.get('AllowMembersToBookAppointmentsWithoutPaying',
                                                                          False),
            'allow_members_to_purchase_non_members_services': data.get('AllowMembersToPurchaseNonMembersServices',
                                                                       False),
            'allow_members_to_purchase_non_members_products': data.get('AllowMembersToPurchaseNonMembersProducts',
                                                                       False),
            'is_active': data.get('IsActive', True),
            'early_access_days_before_scheduling_window': data.get('EarlyAccessDaysBeforeSchedulingWindow', 0),
        }
        return {k: v for k, v in membership_vals.items() if v is not None and v is not False}

    def synchronize(self, from_date=None, to_date=None, limit=None, membership_ids=None):
        """
        Synchronize memberships from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            membership_ids (list, optional): Specific membership IDs to sync
            
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
            if membership_ids:
                params['MembershipIDs'] = ','.join(map(str, membership_ids)) if isinstance(membership_ids,
                                                                                           list) else membership_ids

            _logger.info(f"Starting membership sync with params: {params}")

            # Fetch memberships from Mindbody API
            response = api.get_site_memberships(params=params)
            memberships_data = response.get('Memberships', []) if isinstance(response, dict) else []

            if not memberships_data:
                _logger.info("No memberships found to sync")
                return stats

            _logger.info(f"Fetched {len(memberships_data)} memberships from Mindbody")

            # Process each membership
            for membership_data in memberships_data:
                try:
                    membership_id = membership_data.get('MembershipId')
                    if not membership_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping membership without MembershipId")
                        continue

                    # Check if membership already exists
                    existing = self.search([('membership_id', '=', membership_id)], limit=1)

                    # Prepare membership values
                    membership_vals = self._prepare_membership(membership_data)

                    if existing:
                        existing.write(membership_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated membership {membership_id}: {membership_data.get('MembershipName')}")
                    else:
                        self.create(membership_vals)
                        stats['created'] += 1
                        _logger.info(f"Created membership {membership_id}: {membership_data.get('MembershipName')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing membership {membership_data.get('MembershipId')}: {str(e)}",
                                  exc_info=True)
                    continue

            _logger.info(f"Membership sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync memberships")
            stats['errors'] += 1
            raise UserError(f"Membership sync failed: {str(e)}")

        return stats

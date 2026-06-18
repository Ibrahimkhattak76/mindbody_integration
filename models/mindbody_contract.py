import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
# mindbody_contract.py
from odoo import models, fields


class MindbodyContract(models.Model):
    _name = 'mindbody.contract'
    _description = 'Mindbody Contract'

    contract_id = fields.Integer(string='Contract ID', required=True)
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    assigns_membership_id = fields.Integer(string='Assigns Membership ID')
    assigns_membership_name = fields.Char(string='Assigns Membership Name')
    sold_online = fields.Boolean(string='Sold Online')

    # Relations
    contract_item_ids = fields.One2many('mindbody.contract.item', 'contract_id', string='Contract Items')
    intro_offer = fields.Char(string='Intro Offer')
    autopay_schedule_id = fields.Many2one('mindbody.autopay.schedule', string='Autopay Schedule')
    number_of_autopays = fields.Integer(string='Number of Autopays')
    autopay_trigger_type = fields.Char(string='Autopay Trigger Type')
    action_upon_completion_of_autopays = fields.Char(string='Action Upon Completion of Autopays')
    clients_charged_on = fields.Char(string='Clients Charged On')
    clients_charged_on_specific_date = fields.Datetime(string='Clients Charged On Specific Date')
    discount_amount = fields.Float(string='Discount Amount')
    deposit_amount = fields.Float(string='Deposit Amount')
    first_autopay_free = fields.Boolean(string='First Autopay Free')
    last_autopay_free = fields.Boolean(string='Last Autopay Free')
    client_terminate_online = fields.Boolean(string='Client Terminate Online')

    membership_type_restriction_ids = fields.One2many('mindbody.membership.restriction', 'contract_id',
                                                      string='Membership Type Restrictions')
    location_purchase_restriction_ids = fields.Char(
        string='Location Purchase Restriction IDs')  # JSON list or Many2many
    location_purchase_restriction_names = fields.Char(string='Location Purchase Restriction Names')  # JSON list

    agreement_terms = fields.Text(string='Agreement Terms')
    requires_electronic_confirmation = fields.Boolean(string='Requires Electronic Confirmation')
    autopay_enabled = fields.Boolean(string='Autopay Enabled')
    first_payment_amount_subtotal = fields.Float(string='First Payment Amount Subtotal')
    first_payment_amount_tax = fields.Float(string='First Payment Amount Tax')
    first_payment_amount_total = fields.Float(string='First Payment Amount Total')
    recurring_payment_amount_subtotal = fields.Float(string='Recurring Payment Amount Subtotal')
    recurring_payment_amount_tax = fields.Float(string='Recurring Payment Amount Tax')
    recurring_payment_amount_total = fields.Float(string='Recurring Payment Amount Total')
    total_contract_amount_subtotal = fields.Float(string='Total Contract Amount Subtotal')
    total_contract_amount_tax = fields.Float(string='Total Contract Amount Tax')
    total_contract_amount_total = fields.Float(string='Total Contract Amount Total')
    promo_payment_amount_subtotal = fields.Float(string='Promo Payment Amount Subtotal')
    promo_payment_amount_tax = fields.Float(string='Promo Payment Amount Tax')
    promo_payment_amount_total = fields.Float(string='Promo Payment Amount Total')
    number_of_promo_autopays = fields.Integer(string='Number of Promo Autopays')

    # mindbody_contract.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_contract(self, data):
        """
        Prepare contract values from API response.

        Args:
            data (dict): Contract data from Mindbody API (from /sale/contracts endpoint)

        Returns:
            dict: Values ready for mindbody.contract create/write
        """
        self.ensure_one()

        # Prepare contract items (One2many)
        item_commands = []
        for item_data in data.get('ContractItems', []):
            item_vals = self.env['mindbody.contract.item']._prepare_contract_item(item_data)
            if item_vals:
                item_commands.append((0, 0, item_vals))

        # Prepare autopay schedule (Many2one)
        autopay_schedule_vals = None
        if data.get('AutopaySchedule'):
            autopay_schedule_vals = self.env['mindbody.autopay.schedule']._prepare_autopay_schedule(
                data['AutopaySchedule']
            )

        # Prepare membership restrictions (One2many)
        restriction_commands = []
        for restriction_data in data.get('MembershipTypeRestrictions', []):
            restriction_vals = self.env['mindbody.membership.restriction']._prepare_membership_restriction(
                restriction_data
            )
            if restriction_vals:
                restriction_commands.append((0, 0, restriction_vals))

        # Build contract values
        contract_vals = {
            'contract_id': data.get('Id'),
            'name': data.get('Name'),
            'description': data.get('Description'),
            'assigns_membership_id': data.get('AssignsMembershipId'),
            'assigns_membership_name': data.get('AssignsMembershipName'),
            'sold_online': data.get('SoldOnline', False),
            'intro_offer': data.get('IntroOffer'),
            'number_of_autopays': data.get('NumberOfAutopays', 0),
            'autopay_trigger_type': data.get('AutopayTriggerType'),
            'action_upon_completion_of_autopays': data.get('ActionUponCompletionOfAutopays'),
            'clients_charged_on': data.get('ClientsChargedOn'),
            'clients_charged_on_specific_date': data.get('ClientsChargedOnSpecificDate'),
            'discount_amount': data.get('DiscountAmount', 0.0),
            'deposit_amount': data.get('DepositAmount', 0.0),
            'first_autopay_free': data.get('FirstAutopayFree', False),
            'last_autopay_free': data.get('LastAutopayFree', False),
            'client_terminate_online': data.get('ClientTerminateOnline', False),
            'location_purchase_restriction_ids': str(data.get('LocationPurchaseRestrictionIds', [])),
            'location_purchase_restriction_names': str(data.get('LocationPurchaseRestrictionNames', [])),
            'agreement_terms': data.get('AgreementTerms'),
            'requires_electronic_confirmation': data.get('RequiresElectronicConfirmation', False),
            'autopay_enabled': data.get('AutopayEnabled', False),
            'first_payment_amount_subtotal': data.get('FirstPaymentAmountSubtotal', 0.0),
            'first_payment_amount_tax': data.get('FirstPaymentAmountTax', 0.0),
            'first_payment_amount_total': data.get('FirstPaymentAmountTotal', 0.0),
            'recurring_payment_amount_subtotal': data.get('RecurringPaymentAmountSubtotal', 0.0),
            'recurring_payment_amount_tax': data.get('RecurringPaymentAmountTax', 0.0),
            'recurring_payment_amount_total': data.get('RecurringPaymentAmountTotal', 0.0),
            'total_contract_amount_subtotal': data.get('TotalContractAmountSubtotal', 0.0),
            'total_contract_amount_tax': data.get('TotalContractAmountTax', 0.0),
            'total_contract_amount_total': data.get('TotalContractAmountTotal', 0.0),
            'promo_payment_amount_subtotal': data.get('PromoPaymentAmountSubtotal', 0.0),
            'promo_payment_amount_tax': data.get('PromoPaymentAmountTax', 0.0),
            'promo_payment_amount_total': data.get('PromoPaymentAmountTotal', 0.0),
            'number_of_promo_autopays': data.get('NumberOfPromoAutopays', 0),

            # One2many fields
            'contract_item_ids': item_commands if item_commands else None,
            'membership_type_restriction_ids': restriction_commands if restriction_commands else None,
        }

        # Add Many2one fields with create commands
        if autopay_schedule_vals:
            contract_vals['autopay_schedule_id'] = (0, 0, autopay_schedule_vals)

        # Remove None values
        contract_vals = {k: v for k, v in contract_vals.items() if v is not None and v is not False}

        return contract_vals

    # mindbody_contract.py

    def synchronize(self, from_date=None, to_date=None, limit=None, contract_ids=None):
        """
        Synchronize contracts from Mindbody to Odoo.

        Args:
            from_date (str, optional): Start date for modified contracts
            to_date (str, optional): End date for modified contracts
            limit (int, optional): Maximum number of records to fetch
            contract_ids (list, optional): Specific contract IDs to sync

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
            if contract_ids:
                params['ContractIDs'] = ','.join(map(str, contract_ids)) if isinstance(contract_ids,
                                                                                       list) else contract_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting contract sync with params: {params}")

            # Fetch contracts from Mindbody API
            response = api.get_sale_contracts(params=params)
            contracts_data = response.get('Contracts', []) if isinstance(response, dict) else []

            if not contracts_data:
                _logger.info("No contracts found to sync")
                return stats

            _logger.info(f"Fetched {len(contracts_data)} contracts from Mindbody")

            # Process each contract
            for contract_data in contracts_data:
                try:
                    contract_id = contract_data.get('Id')
                    if not contract_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping contract without ID")
                        continue

                    # Check if contract already exists
                    existing = self.search([('contract_id', '=', contract_id)], limit=1)

                    # Prepare contract values
                    contract_vals = self._prepare_contract(contract_data)

                    if existing:
                        existing.write(contract_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated contract {contract_id}: {contract_data.get('Name')}")
                    else:
                        self.create(contract_vals)
                        stats['created'] += 1
                        _logger.info(f"Created contract {contract_id}: {contract_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing contract {contract_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Contract sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync contracts")
            stats['errors'] += 1
            raise UserError(f"Contract sync failed: {str(e)}")

        return stats

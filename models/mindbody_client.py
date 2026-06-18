import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyClient(models.Model):
    _name = 'mindbody.client'
    _description = 'Mindbody Client'

    client_id = fields.Char(string='Client ID', required=True)
    unique_id = fields.Integer(string='Unique ID')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    middle_name = fields.Char(string='Middle Name')
    display_name = fields.Char(string='Display Name')
    email = fields.Char(string='Email')
    mobile_phone = fields.Char(string='Mobile Phone')
    home_phone = fields.Char(string='Home Phone')
    work_phone = fields.Char(string='Work Phone')
    work_extension = fields.Char(string='Work Extension')
    gender = fields.Char(string='Gender')
    birth_date = fields.Datetime(string='Birth Date')
    first_appointment_date = fields.Datetime(string='First Appointment Date')
    first_class_date = fields.Datetime(string='First Class Date')
    creation_date = fields.Datetime(string='Creation Date')
    last_modified_date_time = fields.Datetime(string='Last Modified Date Time')

    # Address
    address_line1 = fields.Char(string='Address Line 1')
    address_line2 = fields.Char(string='Address Line 2')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    postal_code = fields.Char(string='Postal Code')
    country = fields.Char(string='Country')

    # Status
    active = fields.Boolean(string='Active')
    status = fields.Char(string='Status')
    is_company = fields.Boolean(string='Is Company')
    is_prospect = fields.Boolean(string='Is Prospect')
    referred_by = fields.Char(string='Referred By')

    # Preferences
    appointment_gender_preference = fields.Selection([
        ('None', 'None'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ], string='Appointment Gender Preference', default='None')
    mobile_provider = fields.Integer(string='Mobile Provider')
    send_account_emails = fields.Boolean(string='Send Account Emails')
    send_account_texts = fields.Boolean(string='Send Account Texts')
    send_promotional_emails = fields.Boolean(string='Send Promotional Emails')
    send_promotional_texts = fields.Boolean(string='Send Promotional Texts')
    send_schedule_emails = fields.Boolean(string='Send Schedule Emails')
    send_schedule_texts = fields.Boolean(string='Send Schedule Texts')

    # Alerts
    red_alert = fields.Text(string='Red Alert')
    yellow_alert = fields.Text(string='Yellow Alert')
    notes = fields.Text(string='Notes')

    # Financial
    account_balance = fields.Float(string='Account Balance')

    # Relations
    suspension_info_id = fields.Many2one('mindbody.client.suspension.info', string='Suspension Info')
    custom_client_field_ids = fields.One2many('mindbody.custom.client.field', 'client_id',
                                              string='Custom Client Fields')
    client_credit_card_id = fields.Many2one('mindbody.client.credit.card', string='Client Credit Card')
    client_index_ids = fields.One2many('mindbody.client.index.value', 'client_id', string='Client Indexes')
    client_relationship_ids = fields.One2many('mindbody.client.relationship', 'client_id',
                                              string='Client Relationships')
    liability_id = fields.Many2one('mindbody.liability', string='Liability')
    prospect_stage_id = fields.Many2one('mindbody.prospect.stage.data', string='Prospect Stage')
    photo_url = fields.Char(string='Photo URL')
    emergency_contact_info_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_info_email = fields.Char(string='Emergency Contact Email')
    emergency_contact_info_phone = fields.Char(string='Emergency Contact Phone')
    emergency_contact_info_relationship = fields.Char(string='Emergency Contact Relationship')
    last_formula_notes = fields.Text(string='Last Formula Notes')
    sales_rep_ids = fields.One2many('mindbody.sales.rep', 'client_id', string='Sales Reps')
    home_location_id = fields.Many2one('mindbody.home.location', string='Home Location')
    locker_number = fields.Char(string='Locker Number')
    client_type_id = fields.Many2one('mindbody.client.type', string='Client Type')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # For client schedule
    waitlist_info_id = fields.Many2one('mindbody.waitlist.info', string='Waitlist Info')
    class_cart_id = fields.Many2one('mindbody.class.cart', string='Class Cart')
    class_schedule_id = fields.Many2one('mindbody.class.schedule', string='Class Schedule')
    class_instance_id = fields.Many2one('mindbody.class.instance', string='Class Instance')
    enrollment_id = fields.Many2one('mindbody.enrollment', string='Enrollment')

    # For add/update response
    status_response = fields.Char(string='Status')
    error_ids = fields.Many2many('mindbody.error.info', string='Errors')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_client(self, data):
        """
        Prepare client values from API response.

        Args:
            data (dict): Client data from Mindbody API (from /client/clients endpoint)

        Returns:
            dict: Values ready for mindbody.client create/write
        """
        self.ensure_one()

        credit_card_vals = None
        if data.get('ClientCreditCard'):
            credit_card_vals = self.env['mindbody.client.credit.card']._prepare_client_credit_card(
                data['ClientCreditCard']
            )

        liability_vals = None
        if data.get('Liability') or data.get('LiabilityRelease'):
            liability_vals = self.env['mindbody.liability']._prepare_liability(
                data.get('Liability'),
                data.get('LiabilityRelease')
            )

        suspension_vals = None
        if data.get('SuspensionInfo'):
            suspension_vals = self.env['mindbody.client.suspension.info']._prepare_suspension_info(
                data['SuspensionInfo']
            )

        prospect_stage_vals = None
        if data.get('ProspectStage'):
            prospect_stage_vals = self.env['mindbody.prospect.stage.data']._prepare_prospect_stage_data(
                data['ProspectStage']
            )

        home_location_vals = None
        if data.get('HomeLocation'):
            home_location_vals = self.env['mindbody.location']._prepare_location(
                data['HomeLocation']
            )

        custom_field_commands = []
        for field_data in data.get('CustomClientFields', []):
            field_vals = self.env['mindbody.custom.client.field']._prepare_custom_client_field(field_data)
            if field_vals:
                custom_field_commands.append((0, 0, field_vals))

        relationship_commands = []
        for rel_data in data.get('ClientRelationships', []):
            rel_vals = self.env['mindbody.client.relationship']._prepare_client_relationship(rel_data)
            if rel_vals:
                relationship_commands.append((0, 0, rel_vals))

        sales_rep_commands = []
        for rep_data in data.get('SalesReps', []):
            rep_vals = self.env['mindbody.sales.rep']._prepare_sales_rep(rep_data)
            if rep_vals:
                sales_rep_commands.append((0, 0, rep_vals))

        index_commands = []
        for index_data in data.get('ClientIndexes', []):
            index_vals = self.env['mindbody.client.index.value']._prepare_client_index_value(index_data)
            if index_vals:
                existing_index = self.env['mindbody.client.index.value'].search([
                    ('value_id', '=', index_data.get('ValueId'))
                ], limit=1)
                if existing_index:
                    index_commands.append((4, existing_index.id))
                else:
                    index_commands.append((0, 0, index_vals))

        client_vals = {
            # Core identifiers
            'client_id': data.get('Id'),
            'unique_id': data.get('UniqueId'),
            # Personal information
            'first_name': data.get('FirstName'),
            'last_name': data.get('LastName'),
            'display_name': data.get('FirstName'),
            'middle_name': data.get('MiddleName'),
            'email': data.get('Email'),
            'gender': data.get('Gender'),
            'birth_date': data.get('BirthDate'),
            'photo_url': data.get('PhotoUrl'),
            # Contact information
            'mobile_phone': data.get('MobilePhone'),
            'home_phone': data.get('HomePhone'),
            'work_phone': data.get('WorkPhone'),
            'work_extension': data.get('WorkExtension'),
            # Address
            'address_line1': data.get('AddressLine1'),
            'address_line2': data.get('AddressLine2'),
            'city': data.get('City'),
            'state': data.get('State'),
            'postal_code': data.get('PostalCode'),
            'country': data.get('Country'),
            # Status flags
            'active': data.get('Active', True),
            'status': data.get('Status'),
            'is_company': data.get('IsCompany', False),
            'is_prospect': data.get('IsProspect', False),
            'referred_by': data.get('ReferredBy'),
            # Dates
            'first_appointment_date': data.get('FirstAppointmentDate'),
            'first_class_date': data.get('FirstClassDate'),
            'creation_date': data.get('CreationDate'),
            'last_modified_date_time': data.get('LastModifiedDateTime'),
            # Preferences
            'appointment_gender_preference': data.get('AppointmentGenderPreference', 'None'),
            'mobile_provider': data.get('MobileProvider'),
            'send_account_emails': data.get('SendAccountEmails', True),
            'send_account_texts': data.get('SendAccountTexts', True),
            'send_promotional_emails': data.get('SendPromotionalEmails', True),
            'send_promotional_texts': data.get('SendPromotionalTexts', True),
            'send_schedule_emails': data.get('SendScheduleEmails', True),
            'send_schedule_texts': data.get('SendScheduleTexts', True),
            # Alerts and notes
            'red_alert': data.get('RedAlert'),
            'yellow_alert': data.get('YellowAlert'),
            'notes': data.get('Notes'),
            # Financial
            'account_balance': data.get('AccountBalance', 0.0),
            # Emergency contact
            'emergency_contact_info_name': data.get('EmergencyContactInfoName'),
            'emergency_contact_info_email': data.get('EmergencyContactInfoEmail'),
            'emergency_contact_info_phone': data.get('EmergencyContactInfoPhone'),
            'emergency_contact_info_relationship': data.get('EmergencyContactInfoRelationship'),
            # Other
            'last_formula_notes': data.get('LastFormulaNotes'),
            'locker_number': data.get('LockerNumber'),
        }

        if credit_card_vals:
            client_vals['client_credit_card_id'] = (0, 0, credit_card_vals)
        if liability_vals:
            client_vals['liability_id'] = (0, 0, liability_vals)
        if suspension_vals:
            client_vals['suspension_info_id'] = (0, 0, suspension_vals)
        if prospect_stage_vals:
            client_vals['prospect_stage_id'] = (0, 0, prospect_stage_vals)
        if home_location_vals:
            client_vals['home_location_id'] = (0, 0, home_location_vals)
        if custom_field_commands:
            client_vals['custom_client_field_ids'] = custom_field_commands
        if relationship_commands:
            client_vals['client_relationship_ids'] = relationship_commands
        if sales_rep_commands:
            client_vals['sales_rep_ids'] = sales_rep_commands
        if index_commands:
            client_vals['client_index_ids'] = index_commands

        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )
            if pagination_vals:
                client_vals['pagination_response_id'] = (0, 0, pagination_vals)

        client_vals = {k: v for k, v in client_vals.items() if v is not None and v is not False}

        return client_vals

    # ============================================
    # Synchronize Methods
    # ============================================
    def synchronize(self, from_date=None, to_date=None, limit=None, client_ids=None):
        """
        Synchronize clients from Mindbody to Odoo.
        """
        api = self.env['mindbody.api']

        # This dictionary counts what we did
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # ============================================
        # STEP A: Set up pagination variables
        # ============================================
        offset = 0  # Start from the very first record
        page_size = 100  # Ask for 100 records each time
        has_more = True  # We assume there is more data to get

        try:
            # ============================================
            # STEP B: Build the filters (date, client IDs, etc.)
            # These stay the SAME for every page
            # ============================================
            base_params = {}
            if client_ids:
                base_params['ClientIDs'] = ','.join(map(str, client_ids)) if isinstance(client_ids,
                                                                                        list) else client_ids
            if from_date:
                base_params['ModifiedDateTime'] = from_date
                if to_date:
                    base_params['ModifiedDateTime'] = f"{from_date},{to_date}"

            # ============================================
            # STEP C: THE LOOP - Keep asking until no more data
            # ============================================
            while has_more:

                # --- C1: Build params for THIS page ---
                params = dict(base_params)  # Copy the filters
                params['Limit'] = page_size  # "Give me 100"
                params['Offset'] = offset  # "Start from here"

                _logger.info(f"? Fetching page: offset={offset}, limit={page_size}")

                # --- C2: Call the API ---
                response = api.get_client_clients(params=params)

                # --- C3: Get the list of clients from response ---
                if isinstance(response, dict):
                    clients_data = response.get('Clients', [])
                else:
                    clients_data = response if response else []

                # --- C4: If no clients, stop ---
                if not clients_data:
                    _logger.info("No more clients. Stopping.")
                    break

                _logger.info(f"? Got {len(clients_data)} clients on this page")

                # --- C5: Process EACH client on this page ---
                for client_data in clients_data:
                    # synchronize() mein, for loop ke andar sabse upar add karein:
                    _logger.info(f"RAW CLIENT DATA: {client_data}")
                    try:
                        # Get the client's ID
                        client_id = client_data.get('Id')
                        if not client_id:
                            stats['skipped'] += 1
                            continue

                        # Check if this client already exists in Odoo
                        existing_client = self.search([('client_id', '=', client_id)], limit=1)

                        # Build the values to save
                        client_vals = {
                            'client_id': client_data.get('Id'),
                            'unique_id': client_data.get('UniqueId'),
                            'first_name': client_data.get('FirstName'),
                            'last_name': client_data.get('LastName'),
                            'middle_name': client_data.get('MiddleName'),
                            'display_name': client_data.get('FirstName'),
                            'email': client_data.get('Email'),
                            'mobile_phone': client_data.get('MobilePhone'),
                            'home_phone': client_data.get('HomePhone'),
                            'work_phone': client_data.get('WorkPhone'),
                            'work_extension': client_data.get('WorkExtension'),
                            'gender': client_data.get('Gender'),
                            'birth_date': client_data.get('BirthDate'),
                            'first_appointment_date': client_data.get('FirstAppointmentDate'),
                            'first_class_date': client_data.get('FirstClassDate'),
                            'creation_date': client_data.get('CreationDate'),
                            'last_modified_date_time': client_data.get('LastModifiedDateTime'),
                            'address_line1': client_data.get('AddressLine1'),
                            'address_line2': client_data.get('AddressLine2'),
                            'city': client_data.get('City'),
                            'state': client_data.get('State'),
                            'postal_code': client_data.get('PostalCode'),
                            'country': client_data.get('Country'),
                            'active': client_data.get('Active', True),
                            'status': client_data.get('Status'),
                            'is_company': client_data.get('IsCompany', False),
                            'is_prospect': client_data.get('IsProspect', False),
                            'referred_by': client_data.get('ReferredBy'),
                            'appointment_gender_preference': client_data.get('AppointmentGenderPreference', 'None'),
                            'mobile_provider': client_data.get('MobileProvider'),
                            'send_account_emails': client_data.get('SendAccountEmails', True),
                            'send_account_texts': client_data.get('SendAccountTexts', True),
                            'send_promotional_emails': client_data.get('SendPromotionalEmails', True),
                            'send_promotional_texts': client_data.get('SendPromotionalTexts', True),
                            'send_schedule_emails': client_data.get('SendScheduleEmails', True),
                            'send_schedule_texts': client_data.get('SendScheduleTexts', True),
                            'red_alert': client_data.get('RedAlert'),
                            'yellow_alert': client_data.get('YellowAlert'),
                            'notes': client_data.get('Notes'),
                            'account_balance': client_data.get('AccountBalance', 0.0),
                            'photo_url': client_data.get('PhotoUrl'),
                            'emergency_contact_info_name': client_data.get('EmergencyContactInfoName'),
                            'emergency_contact_info_email': client_data.get('EmergencyContactInfoEmail'),
                            'emergency_contact_info_phone': client_data.get('EmergencyContactInfoPhone'),
                            'emergency_contact_info_relationship': client_data.get('EmergencyContactInfoRelationship'),
                            'last_formula_notes': client_data.get('LastFormulaNotes'),
                            'locker_number': client_data.get('LockerNumber'),
                        }

                        # Remove empty values
                        client_vals = {k: v for k, v in client_vals.items() if v is not None}

                        # SAVE: Update existing or create new
                        if existing_client:
                            existing_client.write(client_vals)
                            stats['updated'] += 1
                            _logger.info(f"? Updated: {client_data.get('FirstName')} {client_data.get('LastName')}")
                        else:
                            self.create(client_vals)
                            stats['created'] += 1
                            _logger.info(f"? Created: {client_data.get('FirstName')} {client_data.get('LastName')}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"? Error on client {client_data.get('Id')}: {str(e)}")
                        continue

                # ============================================
                # STEP D: Decide if we need another page
                # ============================================

                # If we got LESS than 100, it means this was the LAST page
                if len(clients_data) < page_size:
                    _logger.info(f"? LAST PAGE! Total: created={stats['created']}, updated={stats['updated']}")
                    has_more = False  # STOP the loop

                # Otherwise, move to the next page
                else:
                    offset += page_size  # Add 100 to offset
                    _logger.info(f"?? Next page! New offset: {offset}")

        except Exception as e:
            _logger.exception("Failed to sync clients")
            raise UserError(f"Client sync failed: {str(e)}")

        return stats

    # ============================================
    # Additional Synchronize Methods
    # ============================================

    def synchronize_account_balances(self, from_date=None, to_date=None, limit=None, client_ids=None):
        """
        Synchronize client account balances from Mindbody to Odoo.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            client_ids (list, optional): Specific client IDs to sync balances for

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if client_ids:
                params['ClientIds'] = ','.join(map(str, client_ids)) if isinstance(client_ids, list) else client_ids

            response = api.get_client_clientaccountbalances(params=params)
            clients_data = response.get('Clients', []) if isinstance(response, dict) else []

            if not clients_data:
                return stats

            for client_data in clients_data:
                try:
                    client_id = client_data.get('Id')
                    if not client_id:
                        stats['skipped'] += 1
                        continue

                    existing_client = self.search([('client_id', '=', client_id)], limit=1)
                    if existing_client:
                        existing_client.write({'account_balance': client_data.get('AccountBalance', 0.0)})
                        stats['updated'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Client account balance sync failed: {str(e)}")

        return stats

    def synchronize_complete_info(self, client_id=None):
        """
        Synchronize complete client info from Mindbody to Odoo.

        Args:
            client_id (str, required): Specific client ID to sync complete info for

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            if not client_id:
                stats['errors'] += 1
                return stats

            params = {'ClientId': client_id}
            response = api.get_client_clientcompleteinfo(params=params)

            if not response:
                return stats

            client_data = response.get('Client', {})
            if client_data:
                client_vals = self._prepare_client(client_data)
                existing_client = self.search([('client_id', '=', client_id)], limit=1)
                if existing_client:
                    existing_client.write(client_vals)
                    stats['updated'] += 1
                else:
                    self.create(client_vals)
                    stats['created'] += 1

            for service_data in response.get('ClientServices', []):
                service_vals = self.env['mindbody.client.service']._prepare_client_service(service_data)
                service_id = service_data.get('Id')
                if service_id:
                    existing = self.env['mindbody.client.service'].search(
                        [('client_service_id', '=', service_id)], limit=1)
                    if existing:
                        existing.write(service_vals)
                        stats['updated'] += 1
                    else:
                        self.env['mindbody.client.service'].create(service_vals)
                        stats['created'] += 1

            for contract_data in response.get('ClientContracts', []):
                contract_vals = self.env['mindbody.client.contract']._prepare_client_contract(contract_data)
                contract_id = contract_data.get('Id')
                if contract_id:
                    existing = self.env['mindbody.client.contract'].search(
                        [('client_contract_id', '=', contract_id)], limit=1)
                    if existing:
                        existing.write(contract_vals)
                        stats['updated'] += 1
                    else:
                        self.env['mindbody.client.contract'].create(contract_vals)
                        stats['created'] += 1

            for membership_data in response.get('ClientMemberships', []):
                membership_vals = self.env['mindbody.client.membership']._prepare_client_membership(membership_data)
                membership_id = membership_data.get('Id')
                if membership_id:
                    existing = self.env['mindbody.client.membership'].search(
                        [('client_membership_id', '=', membership_id)], limit=1)
                    if existing:
                        existing.write(membership_vals)
                        stats['updated'] += 1
                    else:
                        self.env['mindbody.client.membership'].create(membership_vals)
                        stats['created'] += 1

            for arrival_data in response.get('ClientArrivals', []):
                arrival_vals = self.env['mindbody.client.arrival']._prepare_client_arrival(arrival_data)
                self.env['mindbody.client.arrival'].create(arrival_vals)
                stats['created'] += 1

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Client complete info sync failed: {str(e)}")

        return stats

    def synchronize_direct_debit_info(self, client_id=None):
        """
        Synchronize client direct debit info from Mindbody to Odoo.

        Args:
            client_id (str, required): Specific client ID to sync direct debit info for

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            if not client_id:
                stats['errors'] += 1
                return stats

            params = {'clientId': client_id}
            response = api.get_client_clientdirectdebitinfo(params=params)

            if not response:
                return stats

            existing = self.env['mindbody.client.direct.debit.info'].search(
                [('client_id', '=', client_id)], limit=1)

            debit_info_vals = {
                'client_id': client_id,
                'name_on_account': response.get('NameOnAccount'),
                'routing_number': response.get('RoutingNumber'),
                'account_number': response.get('AccountNumber'),
                'account_type': response.get('AccountType'),
            }
            debit_info_vals = {k: v for k, v in debit_info_vals.items() if v is not None and v is not False}

            if existing:
                existing.write(debit_info_vals)
                stats['updated'] += 1
            else:
                self.env['mindbody.client.direct.debit.info'].create(debit_info_vals)
                stats['created'] += 1

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Client direct debit info sync failed: {str(e)}")

        return stats

    def synchronize_referral_types(self, from_date=None, to_date=None, limit=None):
        """
        Synchronize client referral types from Mindbody to Odoo.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit

            response = api.get_client_clientreferraltypes(params=params)
            referral_types_data = response.get('ReferralTypes', []) if isinstance(response, dict) else []

            if not referral_types_data:
                return stats

            self.env['mindbody.client.referral.type'].search([]).unlink()

            for referral_type_data in referral_types_data:
                try:
                    self.env['mindbody.client.referral.type'].create({'name': referral_type_data})
                    stats['created'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    continue

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Client referral types sync failed: {str(e)}")

        return stats

    def synchronize_schedule(self, from_date=None, to_date=None, limit=None, client_id=None):
        """
        Synchronize client schedule (visits) from Mindbody to Odoo.

        Args:
            from_date (str, optional): Start date for schedule
            to_date (str, optional): End date for schedule
            limit (int, optional): Maximum number of records to fetch
            client_id (str, optional): Specific client ID to sync schedule for

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if client_id:
                params['ClientId'] = client_id
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            response = api.get_client_clientschedule(params=params)
            visits_data = response.get('Visits', []) if isinstance(response, dict) else []

            if not visits_data:
                return stats

            for visit_data in visits_data:
                try:
                    visit_vals = self.env['mindbody.class.visit']._prepare_class_visit(visit_data)
                    visit_id = visit_data.get('Id')
                    if not visit_id:
                        stats['skipped'] += 1
                        continue

                    existing = self.env['mindbody.class.visit'].search([('visit_id', '=', visit_id)], limit=1)
                    if existing:
                        existing.write(visit_vals)
                        stats['updated'] += 1
                    else:
                        self.env['mindbody.class.visit'].create(visit_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Client schedule sync failed: {str(e)}")

        return stats

    def synchronize_visits(self, from_date=None, to_date=None, limit=None, client_id=None):
        """
        Synchronize client visits from Mindbody to Odoo.

        Args:
            from_date (str, optional): Start date for visits
            to_date (str, optional): End date for visits
            limit (int, optional): Maximum number of records to fetch
            client_id (str, optional): Specific client ID to sync visits for

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            params = {}
            if limit:
                params['Limit'] = limit
            if client_id:
                params['ClientId'] = client_id
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            response = api.get_client_clientvisits(params=params)
            visits_data = response.get('Visits', []) if isinstance(response, dict) else []

            if not visits_data:
                return stats

            for visit_data in visits_data:
                try:
                    visit_vals = self.env['mindbody.class.visit']._prepare_class_visit(visit_data)
                    visit_id = visit_data.get('Id')
                    if not visit_id:
                        stats['skipped'] += 1
                        continue

                    existing = self.env['mindbody.class.visit'].search([('visit_id', '=', visit_id)], limit=1)
                    if existing:
                        existing.write(visit_vals)
                        stats['updated'] += 1
                    else:
                        self.env['mindbody.class.visit'].create(visit_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Client visits sync failed: {str(e)}")

        return stats

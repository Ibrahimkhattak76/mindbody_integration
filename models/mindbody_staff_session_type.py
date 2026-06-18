import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_session_type.py
from odoo import models, fields


class MindbodyStaffSessionType(models.Model):
    _name = 'mindbody.staff.session.type'
    _description = 'Mindbody Staff Session Type'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')
    session_type_id = fields.Many2one('mindbody.session.type', string='Session Type')

    staff_id_int = fields.Integer(string='Staff ID Integer')
    session_type = fields.Selection([
        ('All', 'All'),
        ('Class', 'Class'),
        ('Enrollment', 'Enrollment'),
        ('Appointment', 'Appointment'),
        ('Resource', 'Resource'),
        ('Arrival', 'Arrival')
    ], string='Type', default='All')
    external_id = fields.Integer(string='ID')
    name = fields.Char(string='Name')
    num_deducted = fields.Integer(string='Num Deducted')
    program_id = fields.Integer(string='Program ID')
    category = fields.Char(string='Category')
    category_id = fields.Integer(string='Category ID')
    subcategory = fields.Char(string='Subcategory')
    subcategory_id = fields.Integer(string='Subcategory ID')
    time_length = fields.Integer(string='Time Length')
    prep_time = fields.Integer(string='Prep Time')
    finish_time = fields.Integer(string='Finish Time')
    pay_rate_type = fields.Char(string='Pay Rate Type')
    pay_rate_amount = fields.Float(string='Pay Rate Amount')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_staff_session_type.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff_session_type(self, data):
        """
        Prepare staff session type values from API response.
        
        Args:
            data (dict): Staff session type data from Mindbody API (from /staff/sessiontypes endpoint)
            
        Returns:
            dict: Values ready for mindbody.staff.session.type create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        session_type_vals = {
            'staff_id_int': data.get('StaffId'),
            'session_type': data.get('Type', 'All'),
            'id': data.get('Id'),
            'name': data.get('Name'),
            'num_deducted': data.get('NumDeducted', 0),
            'program_id': data.get('ProgramId'),
            'category': data.get('Category'),
            'category_id': data.get('CategoryId'),
            'subcategory': data.get('Subcategory'),
            'subcategory_id': data.get('SubcategoryId'),
            'time_length': data.get('TimeLength', 0),
            'prep_time': data.get('PrepTime', 0),
            'finish_time': data.get('FinishTime', 0),
            'pay_rate_type': data.get('PayRateType'),
            'pay_rate_amount': data.get('PayRateAmount', 0.0),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            session_type_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        session_type_vals = {k: v for k, v in session_type_vals.items() if v is not None and v is not False}

        return session_type_vals

    # mindbody_staff_session_type.py

    def synchronize(self, from_date=None, to_date=None, limit=None, staff_session_type_ids=None):
        """
        Synchronize staff session types from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified staff session types
            to_date (str, optional): End date for modified staff session types
            limit (int, optional): Maximum number of records to fetch
            staff_session_type_ids (list, optional): Specific staff session type IDs to sync
            
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
            if staff_session_type_ids:
                params['StaffSessionTypeIDs'] = ','.join(map(str, staff_session_type_ids)) if isinstance(
                    staff_session_type_ids, list) else staff_session_type_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting staff session type sync with params: {params}")

            # Fetch staff session types from Mindbody API
            response = api.get_staff_sessiontypes(params=params)
            session_types_data = response.get('StaffSessionTypes', []) if isinstance(response, dict) else []

            if not session_types_data:
                _logger.info("No staff session types found to sync")
                return stats

            _logger.info(f"Fetched {len(session_types_data)} staff session types from Mindbody")

            # Process each staff session type
            for session_type_data in session_types_data:
                try:
                    # Check if staff session type already exists
                    staff_id = session_type_data.get('StaffId')
                    session_type_id = session_type_data.get('Id')

                    if not staff_id or not session_type_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping staff session type without StaffId or Id")
                        continue

                    existing = self.search([
                        ('staff_id', '=', staff_id),
                        ('session_type_id', '=', session_type_id)
                    ], limit=1)

                    # Prepare staff session type values
                    session_type_vals = self._prepare_staff_session_type(session_type_data)

                    if existing:
                        existing.write(session_type_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated staff session type for staff {staff_id}")
                    else:
                        self.create(session_type_vals)
                        stats['created'] += 1
                        _logger.info(f"Created staff session type for staff {staff_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing staff session type: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Staff session type sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync staff session types")
            stats['errors'] += 1
            raise UserError(f"Staff session type sync failed: {str(e)}")

        return stats

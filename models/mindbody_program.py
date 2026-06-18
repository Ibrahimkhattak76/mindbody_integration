import logging

_logger = logging.getLogger(__name__)
# mindbody_program.py
from odoo import models, fields


class MindbodyProgram(models.Model):
    _name = 'mindbody.program'
    _description = 'Mindbody Program'

    program_id = fields.Integer(string='Program ID')
    name = fields.Char(string='Name')
    schedule_type = fields.Selection([
        ('All', 'All'),
        ('Class', 'Class'),
        ('Enrollment', 'Enrollment'),
        ('Appointment', 'Appointment'),
        ('Resource', 'Resource'),
        ('Arrival', 'Arrival')
    ], string='Schedule Type', default='All')
    cancel_offset = fields.Integer(string='Cancel Offset')
    content_formats = fields.Char(string='Content Formats')  # JSON list
    pricing_relationship_id = fields.Many2one('mindbody.pricing.relationship', string='Pricing Relationships')
    staff_availability_id = fields.Many2one('mindbody.staff.availability', string='Staff Availability')
    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
    bookable_item_id = fields.Many2one('mindbody.bookable.item', string='Bookable Item')

    # Additional fields
    content_format = fields.Selection([
        ('InPerson', 'In Person'),
        ('LiveStream', 'Live Stream')
    ], string='Content Format')
    online_booking_disabled = fields.Boolean(string='Online Booking Disabled')
    schedule_offset = fields.Integer(string='Schedule Offset')
    schedule_offset_end = fields.Integer(string='Schedule Offset End')

    # mindbody_program.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_program(self, data):
        """
        Prepare program values from API response.
        
        Args:
            data (dict): Program data from Mindbody API (from /site/programs endpoint)
            
        Returns:
            dict: Values ready for mindbody.program create/write
        """
        self.ensure_one()

        # Prepare pricing relationship (Many2one)
        pricing_vals = None
        if data.get('PricingRelationships'):
            pricing_vals = self.env['mindbody.pricing.relationship']._prepare_pricing_relationship(
                data['PricingRelationships']
            )

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        program_vals = {
            'program_id': data.get('Id'),
            'name': data.get('Name'),
            'schedule_type': data.get('ScheduleType', 'All'),
            'cancel_offset': data.get('CancelOffset', 0),
            'content_formats': str(data.get('ContentFormats', [])),
            'content_format': data.get('ContentFormat', 'InPerson'),
            'online_booking_disabled': data.get('OnlineBookingDisabled', False),
            'schedule_offset': data.get('ScheduleOffset', 0),
            'schedule_offset_end': data.get('ScheduleOffsetEnd', 0),
        }

        # Add Many2one fields with create commands
        if pricing_vals:
            program_vals['pricing_relationship_id'] = (0, 0, pricing_vals)
        if pagination_vals:
            program_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        program_vals = {k: v for k, v in program_vals.items() if v is not None and v is not False}

        return program_vals

    # mindbody_program.py

    def synchronize(self, from_date=None, to_date=None, limit=None, program_ids=None):
        """
        Synchronize programs from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified programs
            to_date (str, optional): End date for modified programs
            limit (int, optional): Maximum number of records to fetch
            program_ids (list, optional): Specific program IDs to sync
            
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
            if program_ids:
                params['ProgramIDs'] = ','.join(map(str, program_ids)) if isinstance(program_ids, list) else program_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting program sync with params: {params}")

            # Fetch programs from Mindbody API
            response = api.get_site_programs(params=params)
            programs_data = response.get('Programs', []) if isinstance(response, dict) else []

            if not programs_data:
                _logger.info("No programs found to sync")
                return stats

            _logger.info(f"Fetched {len(programs_data)} programs from Mindbody")

            # Process each program
            for program_data in programs_data:
                try:
                    program_id = program_data.get('Id')
                    if not program_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping program without ID")
                        continue

                    # Check if program already exists
                    existing = self.search([('program_id', '=', program_id)], limit=1)

                    # Prepare program values
                    program_vals = self._prepare_program(program_data)

                    if existing:
                        existing.write(program_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated program {program_id}: {program_data.get('Name')}")
                    else:
                        self.create(program_vals)
                        stats['created'] += 1
                        _logger.info(f"Created program {program_id}: {program_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing program {program_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Program sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync programs")
            stats['errors'] += 1
            raise UserError(f"Program sync failed: {str(e)}")

        return stats

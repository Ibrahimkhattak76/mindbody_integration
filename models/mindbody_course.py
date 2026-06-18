# mindbody_course.py
from odoo import models, fields


class MindbodyCourse(models.Model):
    _name = 'mindbody.course'
    _description = 'Mindbody Course'

    course_id = fields.Integer(string='Course ID')
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    location_id = fields.Many2one('mindbody.location', string='Location')
    organizer_id = fields.Many2one('mindbody.staff', string='Organizer')
    program_id = fields.Many2one('mindbody.program', string='Program')
    image_url = fields.Char(string='Image URL')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_course(self, data):
        """
        Prepare course values from API response.
        
        Args:
            data (dict): Course data from Mindbody API (from /class/courses endpoint)
            
        Returns:
            dict: Values ready for mindbody.course create/write
        """
        self.ensure_one()

        # Prepare location (Many2one)
        location_vals = None
        if data.get('Location'):
            location_vals = self.env['mindbody.location']._prepare_location(data['Location'])

        # Prepare organizer (Many2one)
        organizer_vals = None
        if data.get('Organizer'):
            organizer_vals = self.env['mindbody.staff']._prepare_staff(data['Organizer'])

        # Prepare program (Many2one)
        program_vals = None
        if data.get('Program'):
            program_vals = self.env['mindbody.program']._prepare_program(data['Program'])

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        course_vals = {
            'course_id': data.get('Id'),
            'name': data.get('Name'),
            'description': data.get('Description'),
            'notes': data.get('Notes'),
            'start_date': data.get('StartDate'),
            'end_date': data.get('EndDate'),
            'image_url': data.get('ImageUrl'),
        }

        # Add Many2one fields with create commands
        if location_vals:
            course_vals['location_id'] = (0, 0, location_vals)
        if organizer_vals:
            course_vals['organizer_id'] = (0, 0, organizer_vals)
        if program_vals:
            course_vals['program_id'] = (0, 0, program_vals)
        if pagination_vals:
            course_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        course_vals = {k: v for k, v in course_vals.items() if v is not None and v is not False}

        return course_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, course_ids=None):
        """
        Synchronize courses from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for courses
            to_date (str, optional): End date for courses
            limit (int, optional): Maximum number of records to fetch
            course_ids (list, optional): Specific course IDs to sync
            
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
            if course_ids:
                params['CourseIDs'] = ','.join(map(str, course_ids)) if isinstance(course_ids, list) else course_ids
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            # Fetch courses from Mindbody API
            response = api.get_class_courses(params=params)
            courses_data = response.get('Courses', []) if isinstance(response, dict) else []

            if not courses_data:
                return stats

            # Process each course
            for course_data in courses_data:
                try:
                    course_id = course_data.get('Id')
                    if not course_id:
                        stats['skipped'] += 1
                        continue

                    # Check if course already exists
                    existing = self.search([('course_id', '=', course_id)], limit=1)

                    # Prepare course values
                    course_vals = self._prepare_course(course_data)

                    if existing:
                        existing.write(course_vals)
                        stats['updated'] += 1
                    else:
                        self.create(course_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Course sync failed: {str(e)}")

        return stats

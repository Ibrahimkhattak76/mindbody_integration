# mindbody_semester.py
from odoo import models, fields


class MindbodySemester(models.Model):
    _name = 'mindbody.semester'
    _description = 'Mindbody Semester'

    semester_id = fields.Integer(string='Semester ID')
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    multi_registration_discount = fields.Float(string='Multi Registration Discount')
    multi_registration_deadline = fields.Datetime(string='Multi Registration Deadline')
    active = fields.Boolean(string='Active')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_semester.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_semester(self, data):
        """
        Prepare semester values from API response.
        
        Args:
            data (dict): Semester data from Mindbody API (from /class/semesters endpoint)
            
        Returns:
            dict: Values ready for mindbody.semester create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        semester_vals = {
            'semester_id': data.get('Id'),
            'name': data.get('Name'),
            'description': data.get('Description'),
            'start_date': data.get('StartDate'),
            'end_date': data.get('EndDate'),
            'multi_registration_discount': data.get('MultiRegistrationDiscount', 0.0),
            'multi_registration_deadline': data.get('MultiRegistrationDeadline'),
            'active': data.get('Active', True),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            semester_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        semester_vals = {k: v for k, v in semester_vals.items() if v is not None and v is not False}

        return semester_vals

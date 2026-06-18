# mindbody_pickaspot_class.py
from odoo import models, fields


class MindbodyPickaspotClass(models.Model):
    _name = 'mindbody.pickaspot.class'
    _description = 'Mindbody Pick-a-Spot Class'

    site_id = fields.Integer(string='Site ID')
    location_id = fields.Integer(string='Location ID')
    class_id = fields.Char(string='Class ID')
    class_external_id = fields.Char(string='Class External ID')
    class_name = fields.Char(string='Class Name')
    class_start_time = fields.Datetime(string='Class Start Time')
    class_end_time = fields.Datetime(string='Class End Time')
    class_maximum_capacity = fields.Integer(string='Class Maximum Capacity')
    room_id = fields.Char(string='Room ID')
    spots_id = fields.Many2one('mindbody.pickaspot.spots', string='Spots')
    reservation_ids = fields.One2many('mindbody.pickaspot.reservation', 'class_id', string='Reservations')

    pagination_id = fields.Many2one('mindbody.pagination.details', string='Pagination')
    response_details_id = fields.Many2one('mindbody.response.details', string='Response Details')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_pickaspot_class(self, data):
        """
        Prepare pick-a-spot class values from API response.

        Args:
            data (dict): Pick-a-spot class data from Mindbody API (from /pickaspot/v1/class endpoint)

        Returns:
            dict: Values ready for mindbody.pickaspot.class create/write
        """
        self.ensure_one()

        # Prepare spots (Many2one)
        spots_vals = None
        if data.get('Spots'):
            spots_vals = self.env['mindbody.pickaspot.spots']._prepare_pickaspot_spots(data['Spots'])

        # Prepare reservations (One2many)
        reservation_commands = []
        for res_data in data.get('Reservations', []):
            res_vals = self.env['mindbody.pickaspot.reservation']._prepare_pickaspot_reservation(res_data)
            if res_vals:
                reservation_commands.append((0, 0, res_vals))

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('pagination'):
            pagination_vals = self.env['mindbody.pagination.details']._prepare_pagination_details(data['pagination'])

        # Prepare response details (Many2one)
        response_vals = None
        if data.get('responseDetails'):
            response_vals = self.env['mindbody.response.details']._prepare_response_details(data['responseDetails'])

        class_vals = {
            'site_id': data.get('SiteId'),
            'location_id': data.get('LocationId'),
            'class_id': data.get('ClassId'),
            'class_external_id': data.get('ClassExternalId'),
            'class_name': data.get('ClassName'),
            'class_start_time': data.get('ClassStartTime'),
            'class_end_time': data.get('ClassEndTime'),
            'class_maximum_capacity': data.get('ClassMaximumCapacity', 0),
            'room_id': data.get('RoomId'),

            # One2many fields
            'reservation_ids': reservation_commands if reservation_commands else None,
        }

        # Add Many2one fields with create commands
        if spots_vals:
            class_vals['spots_id'] = (0, 0, spots_vals)
        if pagination_vals:
            class_vals['pagination_id'] = (0, 0, pagination_vals)
        if response_vals:
            class_vals['response_details_id'] = (0, 0, response_vals)

        # Remove None values
        class_vals = {k: v for k, v in class_vals.items() if v is not None and v is not False}

        return class_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, class_ids=None):
        """
        Synchronize pick-a-spot classes from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for classes
            to_date (str, optional): End date for classes
            limit (int, optional): Maximum number of records to fetch
            class_ids (list, optional): Specific class IDs to sync
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            # Prepare parameters
            params = {}
            if limit:
                params['limit'] = limit
            if from_date:
                params['start_date'] = from_date
                if to_date:
                    params['end_date'] = to_date

            # Fetch pick-a-spot classes from Mindbody API
            response = api.get_pickaspot_class(params=params)
            classes_data = response.get('classes', []) if isinstance(response, dict) else []

            if not classes_data:
                return stats

            # Process each class
            for class_data in classes_data:
                try:
                    class_id = class_data.get('ClassId')
                    if not class_id:
                        stats['skipped'] += 1
                        continue

                    # Check if class already exists
                    existing = self.search([('class_id', '=', class_id)], limit=1)

                    # Prepare class values
                    class_vals = self._prepare_pickaspot_class(class_data)

                    if existing:
                        existing.write(class_vals)
                        stats['updated'] += 1
                    else:
                        self.create(class_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('pagination'):
                self.env['mindbody.pagination.details'].create(
                    self.env['mindbody.pagination.details']._prepare_pagination_details(response['pagination'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Pick-a-spot class sync failed: {str(e)}")

        return stats

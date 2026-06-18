# mindbody_pickaspot_reservation.py
from odoo import models, fields
from odoo.exceptions import UserError


class MindbodyPickaspotReservation(models.Model):
    _name = 'mindbody.pickaspot.reservation'
    _description = 'Mindbody Pick-a-Spot Reservation'

    class_id = fields.Many2one('mindbody.pickaspot.class', string='Class')

    reservation_id = fields.Char(string='Reservation ID')
    reservation_external_id = fields.Char(string='Reservation External ID')
    class_id_str = fields.Char(string='Class ID String')
    class_external_id = fields.Char(string='Class External ID')
    member_external_id = fields.Char(string='Member External ID')
    reservation_type = fields.Char(string='Reservation Type')
    spots_id = fields.Many2one('mindbody.pickaspot.spots', string='Spots')
    is_confirmed = fields.Boolean(string='Is Confirmed')
    confirmation_date = fields.Datetime(string='Confirmation Date')

    pagination_id = fields.Many2one('mindbody.pagination.details', string='Pagination')
    response_details_id = fields.Many2one('mindbody.response.details', string='Response Details')

    # mindbody_pickaspot_reservation.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_pickaspot_reservation(self, data):
        """
        Prepare pick-a-spot reservation values from API response.
        
        Args:
            data (dict): Pick-a-spot reservation data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.pickaspot.reservation create/write
        """
        self.ensure_one()

        # Prepare spots (Many2one)
        spots_vals = None
        if data.get('Spots'):
            spots_vals = self.env['mindbody.pickaspot.spots']._prepare_pickaspot_spots(data['Spots'])

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('Pagination'):
            pagination_vals = self.env['mindbody.pagination.details']._prepare_pagination_details(data['Pagination'])

        # Prepare response details (Many2one)
        response_vals = None
        if data.get('ResponseDetails'):
            response_vals = self.env['mindbody.response.details']._prepare_response_details(data['ResponseDetails'])

        reservation_vals = {
            'reservation_id': data.get('ReservationId'),
            'reservation_external_id': data.get('ReservationExternalId'),
            'class_id_str': data.get('ClassId'),
            'class_external_id': data.get('ClassExternalId'),
            'member_external_id': data.get('MemberExternalId'),
            'reservation_type': data.get('ReservationType'),
            'is_confirmed': data.get('IsConfirmed', False),
            'confirmation_date': data.get('ConfirmationDate'),
        }

        # Add Many2one fields with create commands
        if spots_vals:
            reservation_vals['spots_id'] = (0, 0, spots_vals)
        if pagination_vals:
            reservation_vals['pagination_id'] = (0, 0, pagination_vals)
        if response_vals:
            reservation_vals['response_details_id'] = (0, 0, response_vals)

        # Remove None values
        reservation_vals = {k: v for k, v in reservation_vals.items() if v is not None and v is not False}

        return reservation_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, reservation_ids=None):
        """
        Synchronize pick-a-spot reservations from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for reservations
            to_date (str, optional): End date for reservations
            limit (int, optional): Maximum number of records to fetch
            reservation_ids (list, optional): Specific reservation IDs to sync
            
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
            if reservation_ids:
                params['reservation_ids'] = ','.join(map(str, reservation_ids)) if isinstance(reservation_ids,
                                                                                              list) else reservation_ids
            if from_date:
                params['start_date'] = from_date
                if to_date:
                    params['end_date'] = to_date

            # Fetch pick-a-spot reservations from Mindbody API
            # Note: This might need a specific pathInfo parameter
            response = api.get_pickaspot_reservation_by_pathinfo(params=params)
            reservations_data = response.get('Reservations', []) if isinstance(response, dict) else []

            if not reservations_data:
                return stats

            # Process each reservation
            for reservation_data in reservations_data:
                try:
                    reservation_id = reservation_data.get('ReservationId')
                    if not reservation_id:
                        stats['skipped'] += 1
                        continue

                    # Check if reservation already exists
                    existing = self.search([('reservation_id', '=', reservation_id)], limit=1)

                    # Prepare reservation values
                    reservation_vals = self._prepare_pickaspot_reservation(reservation_data)

                    if existing:
                        existing.write(reservation_vals)
                        stats['updated'] += 1
                    else:
                        self.create(reservation_vals)
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('Pagination'):
                self.env['mindbody.pagination.details'].create(
                    self.env['mindbody.pagination.details']._prepare_pagination_details(response['Pagination'])
                )

        except Exception as e:
            stats['errors'] += 1
            raise UserError(f"Pick-a-spot reservation sync failed: {str(e)}")

        return stats

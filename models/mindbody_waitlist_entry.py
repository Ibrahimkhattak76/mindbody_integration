# mindbody_waitlist_entry.py
from odoo import models, fields


class MindbodyWaitlistEntry(models.Model):
    _name = 'mindbody.waitlist.entry'
    _description = 'Mindbody Waitlist Entry'

    class_date = fields.Datetime(string='Class Date')
    class_id = fields.Integer(string='Class ID')
    class_schedule_id = fields.Many2one('mindbody.class.schedule', string='Class Schedule')
    client_id = fields.Many2one('mindbody.client', string='Client')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_waitlist_entry.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_waitlist_entry(self, data):
        """
        Prepare waitlist entry values from API response.
        
        Args:
            data (dict): Waitlist entry data from Mindbody API (from /class/waitlistentries endpoint)
            
        Returns:
            dict: Values ready for mindbody.waitlist.entry create/write
        """
        self.ensure_one()

        # Prepare class schedule (Many2one)
        class_schedule_vals = None
        if data.get('ClassSchedule'):
            class_schedule_vals = self.env['mindbody.class.schedule']._prepare_class_schedule(data['ClassSchedule'])

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        waitlist_vals = {
            'class_date': data.get('ClassDate'),
            'class_id': data.get('ClassId'),
        }

        # Add Many2one fields with create commands
        if class_schedule_vals:
            waitlist_vals['class_schedule_id'] = (0, 0, class_schedule_vals)
        if pagination_vals:
            waitlist_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        waitlist_vals = {k: v for k, v in waitlist_vals.items() if v is not None and v is not False}

        return waitlist_vals

    # ============================================
    # Synchronize Methods
    # ============================================

    def synchronize(self, from_date=None, to_date=None, limit=None, class_id=None):
        """
        Synchronize waitlist entries from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for waitlist entries
            to_date (str, optional): End date for waitlist entries
            limit (int, optional): Maximum number of records to fetch
            class_id (int, optional): Specific class ID to sync waitlist for
            
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
            if class_id:
                params['ClassID'] = class_id
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            # Fetch waitlist entries from Mindbody API
            response = api.get_class_waitlistentries(params=params)
            waitlist_data = response.get('WaitlistEntries', []) if isinstance(response, dict) else []

            if not waitlist_data:
                return stats

            # Process each waitlist entry
            for entry_data in waitlist_data:
                try:
                    entry_vals = self._prepare_waitlist_entry(entry_data)

                    # Check if waitlist entry already exists
                    class_date = entry_data.get('ClassDate')
                    class_id = entry_data.get('ClassId')
                    client_id = entry_data.get('ClientId')

                    if not class_date or not class_id or not client_id:
                        stats['skipped'] += 1
                        continue

                    existing = self.search([
                        ('class_date', '=', class_date),
                        ('class_id', '=', class_id),
                        ('client_id', '=', client_id)
                    ], limit=1)

                    if existing:
                        existing.write(entry_vals)
                        stats['updated'] += 1
                    else:
                        self.create(entry_vals)
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
            raise UserError(f"Waitlist entries sync failed: {str(e)}")

        return stats

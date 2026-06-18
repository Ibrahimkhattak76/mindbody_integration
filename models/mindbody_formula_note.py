import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyFormulaNote(models.Model):
    _name = 'mindbody.formula.note'
    _description = 'Mindbody Formula Note'

    client_id = fields.Many2one('mindbody.client', string='Client')

    formula_note_id = fields.Integer(string='Formula Note ID')
    appointment_id = fields.Integer(string='Appointment ID')
    entry_date = fields.Datetime(string='Entry Date')
    note = fields.Text(string='Note')
    site_id = fields.Integer(string='Site ID')
    site_name = fields.Char(string='Site Name')
    staff_first_name = fields.Char(string='Staff First Name')
    staff_last_name = fields.Char(string='Staff Last Name')
    staff_display_name = fields.Char(string='Staff Display Name')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_formula_note.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_formula_note(self, data):
        """
        Prepare formula note values from API response.
        
        Args:
            data (dict): Formula note data from Mindbody API (from /client/clientformulanotes endpoint)
            
        Returns:
            dict: Values ready for mindbody.formula.note create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        formula_note_vals = {
            'formula_note_id': data.get('Id'),
            'appointment_id': data.get('AppointmentId'),
            'entry_date': data.get('EntryDate'),
            'note': data.get('Note'),
            'site_id': data.get('SiteId'),
            'site_name': data.get('SiteName'),
            'staff_first_name': data.get('StaffFirstName'),
            'staff_last_name': data.get('StaffLastName'),
            'staff_display_name': data.get('StaffDisplayName'),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            formula_note_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        formula_note_vals = {k: v for k, v in formula_note_vals.items() if v is not None and v is not False}

        return formula_note_vals

    # mindbody_formula_note.py

    def synchronize(self, from_date=None, to_date=None, limit=None, formula_note_ids=None):
        """
        Synchronize formula notes from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for formula notes
            to_date (str, optional): End date for formula notes
            limit (int, optional): Maximum number of records to fetch
            formula_note_ids (list, optional): Specific formula note IDs to sync
            
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
            if formula_note_ids:
                params['FormulaNoteIDs'] = ','.join(map(str, formula_note_ids)) if isinstance(formula_note_ids,
                                                                                              list) else formula_note_ids
            if from_date:
                params['StartDate'] = from_date
                if to_date:
                    params['EndDate'] = to_date

            _logger.info(f"Starting formula note sync with params: {params}")

            # Fetch formula notes from Mindbody API
            response = api.get_client_clientformulanotes(params=params)
            notes_data = response.get('FormulaNotes', []) if isinstance(response, dict) else []

            if not notes_data:
                _logger.info("No formula notes found to sync")
                return stats

            _logger.info(f"Fetched {len(notes_data)} formula notes from Mindbody")

            # Process each formula note
            for note_data in notes_data:
                try:
                    note_id = note_data.get('Id')
                    if not note_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping formula note without ID")
                        continue

                    # Check if formula note already exists
                    existing = self.search([('formula_note_id', '=', note_id)], limit=1)

                    # Prepare formula note values
                    note_vals = self._prepare_formula_note(note_data)

                    if existing:
                        existing.write(note_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated formula note {note_id}")
                    else:
                        self.create(note_vals)
                        stats['created'] += 1
                        _logger.info(f"Created formula note {note_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing formula note {note_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Formula note sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync formula notes")
            stats['errors'] += 1
            raise UserError(f"Formula note sync failed: {str(e)}")

        return stats

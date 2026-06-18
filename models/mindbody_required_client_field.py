import logging

_logger = logging.getLogger(__name__)
# mindbody_required_client_field.py
from odoo import models, fields


class MindbodyRequiredClientField(models.Model):
    _name = 'mindbody.required.client.field'
    _description = 'Mindbody Required Client Field'

    site_id = fields.Many2one('mindbody.site', string='Site')

    field_name = fields.Char(string='Field Name')

    # mindbody_required_client_field.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_required_client_field(self, data):
        """
        Prepare required client field values from API response.
        
        Args:
            data (str/dict): Required client field name or dictionary
            
        Returns:
            dict: Values ready for mindbody.required.client.field create/write
        """
        self.ensure_one()

        if isinstance(data, str):
            field_vals = {
                'field_name': data,
            }
        else:
            field_vals = {
                'field_name': data.get('field_name') or data.get('FieldName') or data.get('RequiredClientField'),
            }

        # Remove None values
        field_vals = {k: v for k, v in field_vals.items() if v is not None and v is not False}

        return field_vals

    # mindbody_required_client_field.py

    def synchronize(self, from_date=None, to_date=None, limit=None, field_ids=None):
        """
        Synchronize required client fields from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            field_ids (list, optional): Not used for this endpoint
            
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

            _logger.info(f"Starting required client field sync with params: {params}")

            # Fetch required client fields from Mindbody API
            response = api.get_client_requiredclientfields(params=params)
            fields_data = response.get('RequiredClientFields', []) if isinstance(response, dict) else []

            if not fields_data:
                _logger.info("No required client fields found to sync")
                return stats

            _logger.info(f"Fetched {len(fields_data)} required client fields from Mindbody")

            # Clear existing records and create new ones
            self.search([]).unlink()

            # Process each required client field
            for field_data in fields_data:
                try:
                    # Prepare required client field values
                    field_vals = self._prepare_required_client_field(field_data)

                    self.create(field_vals)
                    stats['created'] += 1
                    _logger.info(f"Created required client field: {field_data}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing required client field: {str(e)}", exc_info=True)
                    continue

            _logger.info(
                f"Required client field sync completed: {stats['created']} created, {stats['updated']} updated, "
                f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync required client fields")
            stats['errors'] += 1
            raise UserError(f"Required client field sync failed: {str(e)}")

        return stats

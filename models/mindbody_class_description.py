import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
# mindbody_class_description.py
from odoo import models, fields


class MindbodyClassDescription(models.Model):
    _name = 'mindbody.class.description'
    _description = 'Mindbody Class Description'

    class_description_id = fields.Integer(string='Class Description ID')
    active = fields.Boolean(string='Active')
    description = fields.Text(string='Description')
    image_url = fields.Char(string='Image URL')
    last_updated = fields.Datetime(string='Last Updated')
    level_id = fields.Many2one('mindbody.class.level', string='Level')
    name = fields.Char(string='Name')
    notes = fields.Text(string='Notes')
    prereq = fields.Text(string='Prereq')
    program_id = fields.Many2one('mindbody.program', string='Program')
    session_type_id = fields.Many2one('mindbody.session.type', string='Session Type')
    category = fields.Char(string='Category')
    category_id = fields.Integer(string='Category ID')
    subcategory = fields.Char(string='Subcategory')
    subcategory_id = fields.Integer(string='Subcategory ID')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_class_description.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_class_description(self, data):
        """
        Prepare class description values from API response.
        
        Args:
            data (dict): Class description data from Mindbody API (from /class/classdescriptions endpoint)
            
        Returns:
            dict: Values ready for mindbody.class.description create/write
        """
        self.ensure_one()

        # Prepare level (Many2one)
        level_vals = None
        if data.get('Level'):
            level_vals = self.env['mindbody.class.level']._prepare_class_level(data['Level'])

        # Prepare program (Many2one)
        program_vals = None
        if data.get('Program'):
            program_vals = self.env['mindbody.program']._prepare_program(data['Program'])

        # Prepare session type (Many2one)
        session_type_vals = None
        if data.get('SessionType'):
            session_type_vals = self.env['mindbody.session.type']._prepare_session_type(data['SessionType'])

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        class_desc_vals = {
            'class_description_id': data.get('Id'),
            'active': data.get('Active', True),
            'description': data.get('Description'),
            'image_url': data.get('ImageURL'),
            'last_updated': data.get('LastUpdated'),
            'name': data.get('Name'),
            'notes': data.get('Notes'),
            'prereq': data.get('Prereq'),
            'category': data.get('Category'),
            'category_id': data.get('CategoryId'),
            'subcategory': data.get('Subcategory'),
            'subcategory_id': data.get('SubcategoryId'),
        }

        # Add Many2one fields with create commands
        if level_vals:
            class_desc_vals['level_id'] = (0, 0, level_vals)
        if program_vals:
            class_desc_vals['program_id'] = (0, 0, program_vals)
        if session_type_vals:
            class_desc_vals['session_type_id'] = (0, 0, session_type_vals)
        if pagination_vals:
            class_desc_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        class_desc_vals = {k: v for k, v in class_desc_vals.items() if v is not None and v is not False}

        return class_desc_vals

    # mindbody_class_description.py

    def synchronize(self, from_date=None, to_date=None, limit=None, class_description_ids=None):
        """
        Synchronize class descriptions from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified class descriptions
            to_date (str, optional): End date for modified class descriptions
            limit (int, optional): Maximum number of records to fetch
            class_description_ids (list, optional): Specific class description IDs to sync
            
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
            if class_description_ids:
                params['ClassDescriptionIDs'] = ','.join(map(str, class_description_ids)) if isinstance(
                    class_description_ids, list) else class_description_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting class description sync with params: {params}")

            # Fetch class descriptions from Mindbody API
            response = api.get_class_classdescriptions(params=params)
            class_descriptions_data = response.get('ClassDescriptions', []) if isinstance(response, dict) else []

            if not class_descriptions_data:
                _logger.info("No class descriptions found to sync")
                return stats

            _logger.info(f"Fetched {len(class_descriptions_data)} class descriptions from Mindbody")

            # Process each class description
            for class_description_data in class_descriptions_data:
                try:
                    class_description_id = class_description_data.get('Id')
                    if not class_description_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping class description without ID")
                        continue

                    # Check if class description already exists
                    existing = self.search([('class_description_id', '=', class_description_id)], limit=1)

                    # Prepare class description values
                    class_description_vals = self._prepare_class_description(class_description_data)

                    if existing:
                        existing.write(class_description_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated class description {class_description_id}")
                    else:
                        self.create(class_description_vals)
                        stats['created'] += 1
                        _logger.info(f"Created class description {class_description_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing class description {class_description_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Class description sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped ")

        except Exception as e:
            _logger.exception("Failed to sync class descriptions")
            stats['errors'] += 1
            raise UserError(f"Class description sync failed: {str(e)}")

        return stats

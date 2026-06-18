import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from odoo import models, fields


class MindbodySessionType(models.Model):
    _name = 'mindbody.session.type'
    _description = 'Mindbody Session Type'

    session_type_id = fields.Integer(string='Session Type ID')
    session_type = fields.Selection([
        ('All', 'All'),
        ('Class', 'Class'),
        ('Enrollment', 'Enrollment'),
        ('Appointment', 'Appointment'),
        ('Resource', 'Resource'),
        ('Arrival', 'Arrival')
    ], string='Type', default='All')
    default_time_length = fields.Integer(string='Default Time Length')
    staff_time_length = fields.Integer(string='Staff Time Length')
    name = fields.Char(string='Name')
    online_description = fields.Text(string='Online Description')
    num_deducted = fields.Integer(string='Num Deducted')
    program_id = fields.Integer(string='Program ID')
    category = fields.Char(string='Category')
    category_id = fields.Integer(string='Category ID')
    subcategory = fields.Char(string='Subcategory')
    subcategory_id = fields.Integer(string='Subcategory ID')
    available_for_add_on = fields.Boolean(string='Available For Add On')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # Additional fields
    active = fields.Boolean(string='Active')
    capacity = fields.Integer(string='Capacity')
    resource_required = fields.Boolean(string='Resource Required')
    category_obj_id = fields.Many2one('mindbody.category', string='Category')
    subcategory_obj_id = fields.Many2one('mindbody.category', string='Sub Category')

    # Prepare Methods
    def _prepare_session_type(self, data):
        """
        Prepare session type values from API response.

        Args:
            data (dict): Session type data from Mindbody API (from /site/sessiontypes endpoint)

        Returns:
            dict: Values ready for mindbody.session.type create/write
        """

        # Prepare category (Many2one)
        category_vals = None
        if data.get('Category') and isinstance(data['Category'], dict):
            category_vals = self.env['mindbody.category']._prepare_category({
                'Id': data.get('CategoryId'),
                'Name': data.get('Category'),
            })

        # Prepare subcategory (Many2one)
        subcategory_vals = None
        if data.get('Subcategory') and isinstance(data['Subcategory'], dict):
            subcategory_vals = self.env['mindbody.category']._prepare_category({
                'Id': data.get('SubcategoryId'),
                'Name': data.get('Subcategory'),
            })

        session_type_vals = {
            'session_type_id': data.get('Id'),
            'session_type': data.get('Type', 'All'),
            'default_time_length': data.get('DefaultTimeLength', 0),
            'staff_time_length': data.get('StaffTimeLength', 0),
            'name': data.get('Name'),
            'online_description': data.get('OnlineDescription'),
            'num_deducted': data.get('NumDeducted', 0),
            'program_id': data.get('ProgramId'),
            'category': data.get('Category'),
            'category_id': data.get('CategoryId'),
            'subcategory': data.get('Subcategory'),
            'subcategory_id': data.get('SubcategoryId'),
            'available_for_add_on': data.get('AvailableForAddOn', False),
            'active': data.get('Active', True),
            'capacity': data.get('Capacity', 0),
            'resource_required': data.get('ResourceRequired', False),
        }

        # Add Many2one fields with create commands
        if category_vals:
            session_type_vals['category_obj_id'] = (0, 0, category_vals)
        if subcategory_vals:
            session_type_vals['subcategory_obj_id'] = (0, 0, subcategory_vals)

        return {k: v for k, v in session_type_vals.items() if v is not None and v is not False}

    def synchronize(self, from_date=None, to_date=None, limit=None, session_type_ids=None):
        """
        Synchronize session types from Mindbody to Odoo with pagination.

        Args:
            from_date (str, optional): Start date for modified session types
            to_date (str, optional): End date for modified session types
            limit (int, optional): Maximum number of records to fetch per page
            session_type_ids (list, optional): Specific session type IDs to sync

        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        offset = 0
        page_size = limit if limit else 100
        has_more = True

        try:
            while has_more:
                # Prepare parameters
                params = {
                    'Limit': page_size,
                    'Offset': offset,
                }
                if session_type_ids:
                    params['SessionTypeIDs'] = ','.join(map(str, session_type_ids)) if isinstance(session_type_ids,
                                                                                                  list) else session_type_ids
                if from_date:
                    params['ModifiedDateTime'] = from_date
                    if to_date:
                        params['ModifiedDateTime'] = f"{from_date},{to_date}"

                _logger.info(f"Fetching session types, offset={offset}, limit={page_size}")

                # Fetch session types from Mindbody API
                response = api.get_site_sessiontypes(params=params)
                session_types_data = response.get('SessionTypes', []) if isinstance(response, dict) else []

                if not session_types_data:
                    break

                _logger.info(f"Fetched {len(session_types_data)} session types from Mindbody")

                # Process each session type
                for session_type_data in session_types_data:
                    try:
                        session_type_id = session_type_data.get('Id')
                        if not session_type_id:
                            stats['skipped'] += 1
                            _logger.warning("Skipping session type without ID")
                            continue

                        # Check if session type already exists
                        existing = self.search([('session_type_id', '=', session_type_id)], limit=1)

                        # Prepare session type values
                        session_type_vals = self._prepare_session_type(session_type_data)

                        if existing:
                            existing.write(session_type_vals)
                            stats['updated'] += 1
                            _logger.info(f"Updated session type {session_type_id}: {session_type_data.get('Name')}")
                        else:
                            self.create(session_type_vals)
                            stats['created'] += 1
                            _logger.info(f"Created session type {session_type_id}: {session_type_data.get('Name')}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing session type {session_type_data.get('Id')}: {str(e)}",
                                      exc_info=True)
                        continue

                # Pagination check
                if len(session_types_data) < page_size:
                    has_more = False

                    # Save pagination info
                    if isinstance(response, dict) and response.get('PaginationResponse'):
                        pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                            response['PaginationResponse']
                        )
                        if pagination_vals:
                            self.env['mindbody.pagination.response'].create(pagination_vals)
                else:
                    offset += page_size

            _logger.info(f"Session type sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync session types")
            stats['errors'] += 1
            raise UserError(f"Session type sync failed: {str(e)}")

        return stats
    # def synchronize(self, from_date=None, to_date=None, limit=None, session_type_ids=None):
    #     """
    #     Synchronize session types from Mindbody to Odoo.
    #
    #     Args:
    #         from_date (str, optional): Start date for modified session types
    #         to_date (str, optional): End date for modified session types
    #         limit (int, optional): Maximum number of records to fetch
    #         session_type_ids (list, optional): Specific session type IDs to sync
    #
    #     Returns:
    #         dict: Statistics of created/updated records
    #     """
    #     api = self.env['mindbody.api']
    #     stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
    #
    #     try:
    #         # Prepare parameters
    #         params = {}
    #         if limit:
    #             params['Limit'] = limit
    #         if session_type_ids:
    #             params['SessionTypeIDs'] = ','.join(map(str, session_type_ids)) if isinstance(session_type_ids,
    #                                                                                           list) else session_type_ids
    #         if from_date:
    #             params['ModifiedDateTime'] = from_date
    #             if to_date:
    #                 params['ModifiedDateTime'] = f"{from_date},{to_date}"
    #
    #         _logger.info(f"Starting session type sync with params: {params}")
    #
    #         # Fetch session types from Mindbody API
    #         response = api.get_site_sessiontypes(params=params)
    #         session_types_data = response.get('SessionTypes', []) if isinstance(response, dict) else []
    #
    #         if not session_types_data:
    #             _logger.info("No session types found to sync")
    #             return stats
    #
    #         _logger.info(f"Fetched {len(session_types_data)} session types from Mindbody")
    #
    #         # Process each session type
    #         for session_type_data in session_types_data:
    #             try:
    #                 session_type_id = session_type_data.get('Id')
    #                 if not session_type_id:
    #                     stats['skipped'] += 1
    #                     _logger.warning("Skipping session type without ID")
    #                     continue
    #
    #                 # Check if session type already exists
    #                 existing = self.search([('session_type_id', '=', session_type_id)], limit=1)
    #
    #                 # Prepare session type values
    #                 session_type_vals = self._prepare_session_type(session_type_data)
    #
    #                 if existing:
    #                     existing.write(session_type_vals)
    #                     stats['updated'] += 1
    #                     _logger.info(f"Updated session type {session_type_id}: {session_type_data.get('Name')}")
    #                 else:
    #                     self.create(session_type_vals)
    #                     stats['created'] += 1
    #                     _logger.info(f"Created session type {session_type_id}: {session_type_data.get('Name')}")
    #
    #             except Exception as e:
    #                 stats['errors'] += 1
    #                 _logger.error(f"Error processing session type {session_type_data.get('Id')}: {str(e)}",
    #                               exc_info=True)
    #                 continue
    #
    #         # Save pagination info if available
    #         if isinstance(response, dict) and response.get('PaginationResponse'):
    #             self.env['mindbody.pagination.response'].create(
    #                 self.env['mindbody.pagination.response']._prepare_pagination_response(
    #                     response['PaginationResponse'])
    #             )
    #
    #         _logger.info(f"Session type sync completed: {stats['created']} created, {stats['updated']} updated, "
    #                      f"{stats['errors']} errors, {stats['skipped']} skipped")
    #
    #     except Exception as e:
    #         _logger.exception("Failed to sync session types")
    #         stats['errors'] += 1
    #         raise UserError(f"Session type sync failed: {str(e)}")
    #
    #     return stats

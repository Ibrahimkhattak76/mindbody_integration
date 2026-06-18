import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyCategory(models.Model):
    _name = 'mindbody.category'
    _description = 'Mindbody Category'
    _rec_name = 'category_name'

    category_id = fields.Integer(string='Category ID')
    category_name = fields.Char(string='Category Name')
    description = fields.Text(string='Description')
    service = fields.Boolean(string='Service')
    active = fields.Boolean(string='Active')
    is_primary = fields.Boolean(string='Is Primary')
    is_secondary = fields.Boolean(string='Is Secondary')
    created_date_time_utc = fields.Datetime(string='Created Date Time UTC')
    modified_date_time_utc = fields.Datetime(string='Modified Date Time UTC')
    parent_id = fields.Many2one('mindbody.category', string='Parent')
    sub_category_ids = fields.One2many('mindbody.category', 'parent_id', string='Sub Categories')
    total_count = fields.Integer(string='Total Count')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    def get_by_external_id(self, categ_id, vals=None):
        """
        Fetch category by external category_id or create it.

        Args:
            categ_id (int): external CategoryId from API
            vals (dict, optional): extra values for creation

        Returns:
            record (mindbody.category) or False
        """
        if not categ_id:
            return False

        record = self.search([('category_id', '=', categ_id)], limit=1)
        if record:
            return record

        create_vals = {
            'category_id': categ_id,
            'category_name': vals.get('category_name') if vals else False,
        }
        if vals:
            create_vals.update(vals)

        return self.create(create_vals)

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_category(self, data):
        """
        Prepare category values from API response.

        Args:
            data (dict): Category data from Mindbody API (from /site/categories endpoint)

        Returns:
            dict: Values ready for mindbody.category create/write
        """
        # Prepare subcategories (One2many)
        subcategory_commands = []
        for sub_data in data.get('SubCategories', []):
            sub_vals = self.env['mindbody.category']._prepare_category(sub_data)
            if sub_vals:
                subcategory_commands.append((0, 0, sub_vals))

        category_vals = {
            'category_id': data.get('Id'),
            'category_name': data.get('CategoryName', ''),
            'description': data.get('Description', ''),
            'service': data.get('Service', False),
            'active': data.get('Active', True),
            'is_primary': data.get('IsPrimary', False),
            'is_secondary': data.get('IsSecondary', False),
            'created_date_time_utc': data.get('CreatedDateTimeUTC'),
            'modified_date_time_utc': data.get('ModifiedDateTimeUTC'),
            'total_count': data.get('TotalCount', 0),
            'sub_category_ids': subcategory_commands if subcategory_commands else None,
        }
        # Remove None values
        category_vals = {k: v for k, v in category_vals.items() if v is not None and v is not False}

        return category_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, category_ids=None):
        """
        Synchronize categories from Mindbody to Odoo.
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        # ============================================
        # STEP A: Set up pagination variables
        # ============================================
        offset = 0
        page_size = limit if limit else 100
        has_more = True

        try:
            # ============================================
            # STEP B: Build the filters (date, category IDs, etc.)
            # ============================================
            base_params = {}
            if category_ids:
                base_params['CategoryIDs'] = ','.join(map(str, category_ids)) if isinstance(category_ids,
                                                                                            list) else category_ids
            if from_date:
                base_params['ModifiedDateTime'] = from_date
                if to_date:
                    base_params['ModifiedDateTime'] = f"{from_date},{to_date}"

            # ============================================
            # STEP C: THE LOOP - Keep asking until no more data
            # ============================================
            while has_more:

                # --- C1: Build params for THIS page ---
                params = dict(base_params)
                params['Limit'] = page_size
                params['Offset'] = offset

                _logger.info(f"Fetching categories page: offset={offset}, limit={page_size}")

                # --- C2: Call the API ---
                response = api.get_site_categories(params=params)

                # --- C3: Get the list of categories from response ---
                if isinstance(response, dict):
                    categories_data = response.get('Categories', [])
                else:
                    categories_data = response if response else []

                # --- C4: If no categories, stop ---
                if not categories_data:
                    _logger.info("No more categories. Stopping.")
                    break

                _logger.info(f"Got {len(categories_data)} categories on this page")

                # --- C5: Process EACH category on this page ---
                for category_data in categories_data:
                    try:
                        category_id = category_data.get('Id')
                        if not category_id:
                            stats['skipped'] += 1
                            _logger.warning("Skipping category without ID")
                            continue

                        # Check if category already exists
                        existing = self.search([('category_id', '=', category_id)], limit=1)

                        # Prepare category values
                        category_vals = self._prepare_category(category_data)

                        if existing:
                            existing.write(category_vals)
                            stats['updated'] += 1
                            _logger.info(f"Updated category {category_id}: {category_data.get('CategoryName')}")
                        else:
                            self.create(category_vals)
                            stats['created'] += 1
                            _logger.info(f"Created category {category_id}: {category_data.get('CategoryName')}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing category {category_data.get('Id')}: {str(e)}", exc_info=True)
                        continue

                # ============================================
                # STEP D: Decide if we need another page
                # ============================================

                # If we got LESS than page_size, it means this was the LAST page
                if len(categories_data) < page_size:
                    _logger.info(f"LAST PAGE! Total: created={stats['created']}, updated={stats['updated']}")
                    has_more = False

                    # Save pagination info if available
                    if isinstance(response, dict) and response.get('PaginationResponse'):
                        pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                            response['PaginationResponse']
                        )
                        if pagination_vals:
                            self.env['mindbody.pagination.response'].create(pagination_vals)
                else:
                    offset += page_size
                    _logger.info(f"Next page! New offset: {offset}")

        except Exception as e:
            _logger.exception("Failed to sync categories")
            stats['errors'] += 1
            raise UserError(f"Category sync failed: {str(e)}")

        _logger.info(f"Category sync completed: {stats['created']} created, {stats['updated']} updated, "
                     f"{stats['errors']} errors, {stats['skipped']} skipped")

        return stats

# import logging
#
# from odoo import models, fields
# from odoo.exceptions import UserError
#
# _logger = logging.getLogger(__name__)
#
#
# class MindbodyCategory(models.Model):
#     _name = 'mindbody.category'
#     _description = 'Mindbody Category'
#     _rec_name = 'category_name'
#
#     category_id = fields.Integer(string='Category ID')
#     category_name = fields.Char(string='Category Name')
#     description = fields.Text(string='Description')
#     service = fields.Boolean(string='Service')
#     active = fields.Boolean(string='Active')
#     is_primary = fields.Boolean(string='Is Primary')
#     is_secondary = fields.Boolean(string='Is Secondary')
#     created_date_time_utc = fields.Datetime(string='Created Date Time UTC')
#     modified_date_time_utc = fields.Datetime(string='Modified Date Time UTC')
#     parent_id = fields.Many2one('mindbody.category', string='Parent')
#     sub_category_ids = fields.One2many('mindbody.category', 'parent_id', string='Sub Categories')
#     total_count = fields.Integer(string='Total Count')
#
#     pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')
#
#     def get_by_external_id(self, categ_id, vals=None):
#         """
#         Fetch category by external category_id or create it.
#
#         Args:
#             categ_id (int): external CategoryId from API
#             vals (dict, optional): extra values for creation
#
#         Returns:
#             record (mindbody.category) or False
#         """
#         if not categ_id:
#             return False
#
#         record = self.search([('category_id', '=', categ_id)], limit=1)
#         if record:
#             return record
#
#         create_vals = {
#             'category_id': categ_id,
#             'category_name': vals.get('category_name') if vals else False,
#         }
#         if vals:
#             create_vals.update(vals)
#
#         return self.create(create_vals)
#
#     # ============================================
#     # Prepare Methods
#     # ============================================
#
#     def _prepare_category(self, data):
#         """
#         Prepare category values from API response.
#
#         Args:
#             data (dict): Category data from Mindbody API (from /site/categories endpoint)
#
#         Returns:
#             dict: Values ready for mindbody.category create/write
#         """
#         # Prepare subcategories (One2many)
#         subcategory_commands = []
#         for sub_data in data.get('SubCategories', []):
#             sub_vals = self.env['mindbody.category']._prepare_category(sub_data)
#             if sub_vals:
#                 subcategory_commands.append((0, 0, sub_vals))
#
#         category_vals = {
#             'category_id': data.get('Id'),
#             'category_name': data.get('CategoryName', ''),
#             'description': data.get('Description', ''),
#             'service': data.get('Service', False),
#             'active': data.get('Active', True),
#             'is_primary': data.get('IsPrimary', False),
#             'is_secondary': data.get('IsSecondary', False),
#             'created_date_time_utc': data.get('CreatedDateTimeUTC'),
#             'modified_date_time_utc': data.get('ModifiedDateTimeUTC'),
#             'total_count': data.get('TotalCount', 0),
#             'sub_category_ids': subcategory_commands if subcategory_commands else None,
#         }
#         # Remove None values
#         category_vals = {k: v for k, v in category_vals.items() if v is not None and v is not False}
#
#         return category_vals
#
#     def synchronize(self, from_date=None, to_date=None, limit=None, category_ids=None):
#         """
#         Synchronize categories from Mindbody to Odoo.
#
#         Args:
#             from_date (str, optional): Start date for modified categories
#             to_date (str, optional): End date for modified categories
#             limit (int, optional): Maximum number of records to fetch
#             category_ids (list, optional): Specific category IDs to sync
#
#         Returns:
#             dict: Statistics of created/updated records
#         """
#         api = self.env['mindbody.api']
#         stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
#
#         try:
#             # Prepare parameters
#             params = {}
#             if limit:
#                 params['Limit'] = limit
#             if category_ids:
#                 params['CategoryIDs'] = ','.join(map(str, category_ids)) if isinstance(category_ids,
#                                                                                        list) else category_ids
#             if from_date:
#                 params['ModifiedDateTime'] = from_date
#                 if to_date:
#                     params['ModifiedDateTime'] = f"{from_date},{to_date}"
#
#             _logger.info(f"Starting category sync with params: {params}")
#
#             # Fetch categories from Mindbody API
#             response = api.get_site_categories(params=params)
#             categories_data = response.get('Categories', []) if isinstance(response, dict) else []
#
#             if not categories_data:
#                 _logger.info("No categories found to sync")
#                 return stats
#
#             _logger.info(f"Fetched {len(categories_data)} categories from Mindbody")
#
#             # Process each category
#             for category_data in categories_data:
#                 try:
#                     category_id = category_data.get('Id')
#                     if not category_id:
#                         stats['skipped'] += 1
#                         _logger.warning("Skipping category without ID")
#                         continue
#
#                     # Check if category already exists
#                     existing = self.search([('category_id', '=', category_id)], limit=1)
#
#                     # Prepare category values
#                     category_vals = self._prepare_category(category_data)
#
#                     if existing:
#                         existing.write(category_vals)
#                         stats['updated'] += 1
#                         _logger.info(f"Updated category {category_id}: {category_data.get('CategoryName')}")
#                     else:
#                         self.create(category_vals)
#                         stats['created'] += 1
#                         _logger.info(f"Created category {category_id}: {category_data.get('CategoryName')}")
#
#                 except Exception as e:
#                     stats['errors'] += 1
#                     _logger.error(f"Error processing category {category_data.get('Id')}: {str(e)}", exc_info=True)
#                     continue
#
#             _logger.info(f"Category sync completed: {stats['created']} created, {stats['updated']} updated, "
#                          f"{stats['errors']} errors, {stats['skipped']} skipped")
#
#         except Exception as e:
#             _logger.exception("Failed to sync categories")
#             stats['errors'] += 1
#             raise UserError(f"Category sync failed: {str(e)}")
#
#         return stats

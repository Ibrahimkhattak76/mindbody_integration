import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MindbodyGenderOption(models.Model):
    _name = 'mindbody.gender'
    _description = 'Mindbody Gender'

    gender_id = fields.Integer(string='Gender ID')
    name = fields.Char(string='Name')
    is_active = fields.Boolean(string='Is Active')
    is_default = fields.Boolean(string='Is Default')

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_gender_option(self, data):
        """
        Prepare gender option values from API response.
        
        Args:
            data (dict): Gender option data from Mindbody API (from /site/genders endpoint)
            
        Returns:
            dict: Values ready for mindbody.gender create/write
        """

        gender_option_vals = {
            'gender_id': data.get('Id'),
            'name': data.get('Name'),
            'is_active': data.get('IsActive', True),
            'is_default': data.get('IsDefault', False),
        }
        gender_option_vals = {k: v for k, v in gender_option_vals.items() if v is not None and v is not False}

        return gender_option_vals

    def synchronize(self, from_date=None, to_date=None, limit=None, gender_ids=None):
        """
        Synchronize gender options from Mindbody to Odoo with pagination.

        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch per page
            gender_ids (list, optional): Not used for this endpoint

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

                _logger.info(f"Fetching gender options, offset={offset}, limit={page_size}")

                # Fetch gender options from Mindbody API
                response = api.get_site_genders(params=params)
                gender_options = response.get('GenderOptions', []) if isinstance(response, dict) else []

                if not gender_options:
                    break

                _logger.info(f"Fetched {len(gender_options)} gender options from Mindbody")

                # Process each gender option
                for gender_data in gender_options:
                    try:
                        gender_id = gender_data.get('Id')
                        if not gender_id:
                            stats['skipped'] += 1
                            _logger.warning("Skipping gender option without ID")
                            continue

                        # Check if gender option already exists
                        existing = self.search([('gender_id', '=', gender_id)], limit=1)

                        # Prepare gender option values
                        gender_vals = self._prepare_gender_option(gender_data)

                        if existing:
                            existing.write(gender_vals)
                            stats['updated'] += 1
                            _logger.info(f"Updated gender option {gender_id}: {gender_data.get('Name')}")
                        else:
                            self.create(gender_vals)
                            stats['created'] += 1
                            _logger.info(f"Created gender option {gender_id}: {gender_data.get('Name')}")

                    except Exception as e:
                        stats['errors'] += 1
                        _logger.error(f"Error processing gender option {gender_data.get('Id')}: {str(e)}",
                                      exc_info=True)
                        continue

                # Pagination check
                if len(gender_options) < page_size:
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

            _logger.info(f"Gender option sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync gender options")
            stats['errors'] += 1
            raise UserError(f"Gender option sync failed: {str(e)}")

        return stats
    # def synchronize(self, from_date=None, to_date=None, limit=None, gender_ids=None):
    #     """
    #     Synchronize gender options from Mindbody to Odoo.
    #
    #     Args:
    #         from_date (str, optional): Not used for this endpoint
    #         to_date (str, optional): Not used for this endpoint
    #         limit (int, optional): Maximum number of records to fetch
    #         gender_ids (list, optional): Not used for this endpoint
    #
    #     Returns:
    #         dict: Statistics of created/updated records
    #     """
    #     api = self.env['mindbody.api']
    #     stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
    #
    #     try:
    #         _logger.info("Starting gender option sync")
    #         # Fetch gender options from Mindbody API
    #         response = api.get_site_genders()
    #         gender_options = response.get('GenderOptions', []) if isinstance(response, dict) else []
    #
    #         if not gender_options:
    #             _logger.info("No gender options found to sync")
    #             return stats
    #
    #         _logger.info(f"Fetched {len(gender_options)} gender options from Mindbody")
    #
    #         # Process each gender option
    #         for gender_data in gender_options:
    #             try:
    #                 gender_id = gender_data.get('Id')
    #                 if not gender_id:
    #                     stats['skipped'] += 1
    #                     _logger.warning("Skipping gender option without ID")
    #                     continue
    #
    #                 # Check if gender option already exists
    #                 existing = self.search([('gender_id', '=', gender_id)], limit=1)
    #
    #                 # Prepare gender option values
    #                 gender_vals = self._prepare_gender_option(gender_data)
    #
    #                 if existing:
    #                     existing.write(gender_vals)
    #                     stats['updated'] += 1
    #                     _logger.info(f"Updated gender option {gender_id}: {gender_data.get('Name')}")
    #                 else:
    #                     self.create(gender_vals)
    #                     stats['created'] += 1
    #                     _logger.info(f"Created gender option {gender_id}: {gender_data.get('Name')}")
    #
    #             except Exception as e:
    #                 stats['errors'] += 1
    #                 _logger.error(f"Error processing gender option {gender_data.get('Id')}: {str(e)}", exc_info=True)
    #                 continue
    #
    #         _logger.info(f"Gender option sync completed: {stats['created']} created, {stats['updated']} updated, "
    #                      f"{stats['errors']} errors, {stats['skipped']} skipped")
    #
    #     except Exception as e:
    #         _logger.exception("Failed to sync gender options")
    #         stats['errors'] += 1
    #         raise UserError(f"Gender option sync failed: {str(e)}")
    #
    #     return stats

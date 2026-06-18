import logging

_logger = logging.getLogger(__name__)
# mindbody_staff_sales_rep.py
from odoo import models, fields


class MindbodyStaffSalesRep(models.Model):
    _name = 'mindbody.staff.sales.rep'
    _description = 'Mindbody Staff Sales Rep'

    staff_id = fields.Many2one('mindbody.staff', string='Staff')

    external_id = fields.Integer(string='ID')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    sales_rep_numbers = fields.Char(string='Sales Rep Numbers')  # JSON list

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_staff_sales_rep.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_staff_sales_rep(self, data):
        """
        Prepare staff sales rep values from API response.
        
        Args:
            data (dict): Staff sales rep data from Mindbody API (from /staff/salesreps endpoint)
            
        Returns:
            dict: Values ready for mindbody.staff.sales.rep create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        sales_rep_vals = {
            'id': data.get('Id'),
            'first_name': data.get('FirstName'),
            'last_name': data.get('LastName'),
            'sales_rep_numbers': str(data.get('SalesRepNumbers', [])),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            sales_rep_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        sales_rep_vals = {k: v for k, v in sales_rep_vals.items() if v is not None and v is not False}

        return sales_rep_vals

    # mindbody_staff_sales_rep.py

    def synchronize(self, from_date=None, to_date=None, limit=None, staff_sales_rep_ids=None):
        """
        Synchronize staff sales reps from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified staff sales reps
            to_date (str, optional): End date for modified staff sales reps
            limit (int, optional): Maximum number of records to fetch
            staff_sales_rep_ids (list, optional): Specific staff sales rep IDs to sync
            
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
            if staff_sales_rep_ids:
                params['StaffSalesRepIDs'] = ','.join(map(str, staff_sales_rep_ids)) if isinstance(staff_sales_rep_ids,
                                                                                                   list) else staff_sales_rep_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting staff sales rep sync with params: {params}")

            # Fetch staff sales reps from Mindbody API
            response = api.get_staff_salesreps(params=params)
            sales_reps_data = response.get('SalesReps', []) if isinstance(response, dict) else []

            if not sales_reps_data:
                _logger.info("No staff sales reps found to sync")
                return stats

            _logger.info(f"Fetched {len(sales_reps_data)} staff sales reps from Mindbody")

            # Process each staff sales rep
            for sales_rep_data in sales_reps_data:
                try:
                    rep_id = sales_rep_data.get('Id')
                    if not rep_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping staff sales rep without ID")
                        continue

                    # Check if staff sales rep already exists
                    existing = self.search([('id', '=', rep_id)], limit=1)

                    # Prepare staff sales rep values
                    sales_rep_vals = self._prepare_staff_sales_rep(sales_rep_data)

                    if existing:
                        existing.write(sales_rep_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated staff sales rep {rep_id}")
                    else:
                        self.create(sales_rep_vals)
                        stats['created'] += 1
                        _logger.info(f"Created staff sales rep {rep_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing staff sales rep {sales_rep_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Staff sales rep sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync staff sales reps")
            stats['errors'] += 1
            raise UserError(f"Staff sales rep sync failed: {str(e)}")

        return stats

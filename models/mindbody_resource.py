import logging

_logger = logging.getLogger(__name__)
# mindbody_resource.py
from odoo import models, fields


class MindbodyResource(models.Model):
    _name = 'mindbody.resource'
    _description = 'Mindbody Resource'

    resource_id = fields.Integer(string='Resource ID')
    name = fields.Char(string='Name')

    # mindbody_resource.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_resource(self, data):
        """
        Prepare resource values from API response.
        
        Args:
            data (dict): Resource data from Mindbody API (from /site/resources endpoint)
            
        Returns:
            dict: Values ready for mindbody.resource create/write
        """
        self.ensure_one()

        resource_vals = {
            'resource_id': data.get('Id'),
            'name': data.get('Name'),
        }

        # Remove None values
        resource_vals = {k: v for k, v in resource_vals.items() if v is not None and v is not False}

        return resource_vals

    # mindbody_resource.py

    def synchronize(self, from_date=None, to_date=None, limit=None, resource_ids=None):
        """
        Synchronize resources from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Start date for modified resources
            to_date (str, optional): End date for modified resources
            limit (int, optional): Maximum number of records to fetch
            resource_ids (list, optional): Specific resource IDs to sync
            
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
            if resource_ids:
                params['ResourceIDs'] = ','.join(map(str, resource_ids)) if isinstance(resource_ids,
                                                                                       list) else resource_ids
            if from_date:
                params['ModifiedDateTime'] = from_date
                if to_date:
                    params['ModifiedDateTime'] = f"{from_date},{to_date}"

            _logger.info(f"Starting resource sync with params: {params}")

            # Fetch resources from Mindbody API
            response = api.get_site_resources(params=params)

            # Handle response - this endpoint might return a list directly
            resources_data = response if isinstance(response, list) else []

            if not resources_data:
                _logger.info("No resources found to sync")
                return stats

            _logger.info(f"Fetched {len(resources_data)} resources from Mindbody")

            # Process each resource
            for resource_data in resources_data:
                try:
                    resource_id = resource_data.get('Id')
                    if not resource_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping resource without ID")
                        continue

                    # Check if resource already exists
                    existing = self.search([('resource_id', '=', resource_id)], limit=1)

                    # Prepare resource values
                    resource_vals = self._prepare_resource(resource_data)

                    if existing:
                        existing.write(resource_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated resource {resource_id}: {resource_data.get('Name')}")
                    else:
                        self.create(resource_vals)
                        stats['created'] += 1
                        _logger.info(f"Created resource {resource_id}: {resource_data.get('Name')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing resource {resource_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            _logger.info(f"Resource sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync resources")
            stats['errors'] += 1
            raise UserError(f"Resource sync failed: {str(e)}")

        return stats

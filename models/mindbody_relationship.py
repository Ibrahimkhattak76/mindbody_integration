import logging

_logger = logging.getLogger(__name__)
# mindbody_relationship.py
from odoo import models, fields


class MindbodyRelationship(models.Model):
    _name = 'mindbody.relationship'
    _description = 'Mindbody Relationship'

    relationship_id = fields.Integer(string='Relationship ID')
    relationship_name1 = fields.Char(string='Relationship Name 1')
    relationship_name2 = fields.Char(string='Relationship Name 2')

    pagination_response_id = fields.Many2one('mindbody.pagination.response', string='Pagination Response')

    # mindbody_relationship.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_relationship(self, data):
        """
        Prepare relationship values from API response.
        
        Args:
            data (dict): Relationship data from Mindbody API (from /site/relationships endpoint)
            
        Returns:
            dict: Values ready for mindbody.relationship create/write
        """
        self.ensure_one()

        # Prepare pagination (Many2one)
        pagination_vals = None
        if data.get('PaginationResponse'):
            pagination_vals = self.env['mindbody.pagination.response']._prepare_pagination_response(
                data['PaginationResponse']
            )

        relationship_vals = {
            'relationship_id': data.get('Id'),
            'relationship_name1': data.get('RelationshipName1'),
            'relationship_name2': data.get('RelationshipName2'),
        }

        # Add Many2one fields with create commands
        if pagination_vals:
            relationship_vals['pagination_response_id'] = (0, 0, pagination_vals)

        # Remove None values
        relationship_vals = {k: v for k, v in relationship_vals.items() if v is not None and v is not False}

        return relationship_vals

    # mindbody_relationship.py

    def synchronize(self, from_date=None, to_date=None, limit=None, relationship_ids=None):
        """
        Synchronize relationships from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            relationship_ids (list, optional): Specific relationship IDs to sync
            
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
            if relationship_ids:
                params['RelationshipIDs'] = ','.join(map(str, relationship_ids)) if isinstance(relationship_ids,
                                                                                               list) else relationship_ids

            _logger.info(f"Starting relationship sync with params: {params}")

            # Fetch relationships from Mindbody API
            response = api.get_site_relationships(params=params)
            relationships_data = response.get('Relationships', []) if isinstance(response, dict) else []

            if not relationships_data:
                _logger.info("No relationships found to sync")
                return stats

            _logger.info(f"Fetched {len(relationships_data)} relationships from Mindbody")

            # Process each relationship
            for relationship_data in relationships_data:
                try:
                    relationship_id = relationship_data.get('Id')
                    if not relationship_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping relationship without ID")
                        continue

                    # Check if relationship already exists
                    existing = self.search([('relationship_id', '=', relationship_id)], limit=1)

                    # Prepare relationship values
                    relationship_vals = self._prepare_relationship(relationship_data)

                    if existing:
                        existing.write(relationship_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated relationship {relationship_id}")
                    else:
                        self.create(relationship_vals)
                        stats['created'] += 1
                        _logger.info(f"Created relationship {relationship_id}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing relationship {relationship_data.get('Id')}: {str(e)}",
                                  exc_info=True)
                    continue

            # Save pagination info if available
            if isinstance(response, dict) and response.get('PaginationResponse'):
                self.env['mindbody.pagination.response'].create(
                    self.env['mindbody.pagination.response']._prepare_pagination_response(
                        response['PaginationResponse'])
                )

            _logger.info(f"Relationship sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync relationships")
            stats['errors'] += 1
            raise UserError(f"Relationship sync failed: {str(e)}")

        return stats

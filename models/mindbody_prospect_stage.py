import logging

_logger = logging.getLogger(__name__)
# mindbody_prospect_stage.py
from odoo import models, fields


class MindbodyProspectStage(models.Model):
    _name = 'mindbody.prospect.stage'
    _description = 'Mindbody Prospect Stage'

    stage_id = fields.Integer(string='Stage ID')
    active = fields.Boolean(string='Active')
    description = fields.Char(string='Description')

    # mindbody_prospect_stage.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_prospect_stage(self, data):
        """
        Prepare prospect stage values from API response.
        
        Args:
            data (dict): Prospect stage data from Mindbody API (from /site/prospectstages endpoint)
            
        Returns:
            dict: Values ready for mindbody.prospect.stage create/write
        """
        self.ensure_one()

        stage_vals = {
            'stage_id': data.get('Id'),
            'active': data.get('Active', True),
            'description': data.get('Description'),
        }

        # Remove None values
        stage_vals = {k: v for k, v in stage_vals.items() if v is not None and v is not False}

        return stage_vals

    # mindbody_prospect_stage.py

    def synchronize(self, from_date=None, to_date=None, limit=None, prospect_stage_ids=None):
        """
        Synchronize prospect stages from Mindbody to Odoo.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Maximum number of records to fetch
            prospect_stage_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        api = self.env['mindbody.api']
        stats = {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

        try:
            _logger.info("Starting prospect stage sync")

            # Fetch prospect stages from Mindbody API
            response = api.get_site_prospectstages()
            stages_data = response.get('ProspectStages', []) if isinstance(response, dict) else []

            if not stages_data:
                _logger.info("No prospect stages found to sync")
                return stats

            _logger.info(f"Fetched {len(stages_data)} prospect stages from Mindbody")

            # Process each prospect stage
            for stage_data in stages_data:
                try:
                    stage_id = stage_data.get('Id')
                    if not stage_id:
                        stats['skipped'] += 1
                        _logger.warning("Skipping prospect stage without ID")
                        continue

                    # Check if prospect stage already exists
                    existing = self.search([('stage_id', '=', stage_id)], limit=1)

                    # Prepare prospect stage values
                    stage_vals = self._prepare_prospect_stage(stage_data)

                    if existing:
                        existing.write(stage_vals)
                        stats['updated'] += 1
                        _logger.info(f"Updated prospect stage {stage_id}: {stage_data.get('Description')}")
                    else:
                        self.create(stage_vals)
                        stats['created'] += 1
                        _logger.info(f"Created prospect stage {stage_id}: {stage_data.get('Description')}")

                except Exception as e:
                    stats['errors'] += 1
                    _logger.error(f"Error processing prospect stage {stage_data.get('Id')}: {str(e)}", exc_info=True)
                    continue

            _logger.info(f"Prospect stage sync completed: {stats['created']} created, {stats['updated']} updated, "
                         f"{stats['errors']} errors, {stats['skipped']} skipped")

        except Exception as e:
            _logger.exception("Failed to sync prospect stages")
            stats['errors'] += 1
            raise UserError(f"Prospect stage sync failed: {str(e)}")

        return stats

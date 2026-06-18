import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MindbodyContactLogComment(models.Model):
    _name = 'mindbody.contact.log.comment'
    _description = 'Mindbody Contact Log Comment'

    contact_log_id = fields.Many2one('mindbody.contact.log', string='Contact Log')

    comment_id = fields.Integer(string='Comment ID')
    text = fields.Text(string='Text')
    created_date_time = fields.Datetime(string='Created Date Time')
    created_by_id = fields.Many2one('mindbody.staff', string='Created By')

    # mindbody_contact_log_comment.py

    # ============================================
    # Prepare Methods
    # ============================================

    def _prepare_contact_log_comment(self, data):
        """
        Prepare contact log comment values from API response.
        
        Args:
            data (dict): Contact log comment data from Mindbody API
            
        Returns:
            dict: Values ready for mindbody.contact.log.comment create/write
        """

        # Prepare created by (Many2one)
        created_by_vals = None
        if data.get('CreatedBy'):
            created_by_vals = self.env['mindbody.staff']._prepare_staff(data['CreatedBy'])

        comment_vals = {
            'comment_id': data.get('Id'),
            'text': data.get('Text'),
            'created_date_time': data.get('CreatedDateTime'),
        }

        # Add Many2one fields with create commands
        if created_by_vals:
            comment_vals['created_by_id'] = (0, 0, created_by_vals)

        # Remove None values
        comment_vals = {k: v for k, v in comment_vals.items() if v is not None and v is not False}

        return comment_vals

    # mindbody_contact_log_comment.py

    def synchronize(self, from_date=None, to_date=None, limit=None, comment_ids=None):
        """
        Synchronize contact log comments from Mindbody to Odoo.
        Note: Contact log comments are typically synced as part of contact log sync.
        
        Args:
            from_date (str, optional): Not used for this endpoint
            to_date (str, optional): Not used for this endpoint
            limit (int, optional): Not used for this endpoint
            comment_ids (list, optional): Not used for this endpoint
            
        Returns:
            dict: Statistics of created/updated records
        """
        _logger.info("Contact log comments are synced automatically during contact log sync")
        return {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

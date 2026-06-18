# -*- coding: utf-8 -*-
from odoo import models, fields


class SessionTypeWizard(models.TransientModel):
    _name = 'session.type.selection.wizard'
    _description = 'Select Session Types'

    session_type_ids = fields.Many2many(
        'mindbody.session.type',
        string='Session Types',
        required=True
    )

    limit = fields.Integer(string='Limit')
    bookable_item_ids = fields.Char(string='Bookable Item IDs')

    def action_confirm(self):
        self.ensure_one()

        session_ids = self.session_type_ids.mapped('session_type_id')

        return self.env['mindbody.bookable.item'].synchronize(
            session_type_ids=session_ids,
            limit=self.limit,
            bookable_item_ids=self.bookable_item_ids
        )

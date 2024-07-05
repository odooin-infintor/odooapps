from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HelpdeskOnHoldReason(models.Model):
    _name = 'helpdesk.on_hold_reason'
    _description = 'Helpdesk On-Hold Reason'

    name = fields.Char('Reason', required=True, translate=True)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    on_hold_reason_id = fields.Many2one('helpdesk.on_hold_reason', string='On-Hold Reasons')
    is_on_hold_wizard_applied = fields.Boolean(string='On Hold Wizard Applied', default=False, readonly=True)

    def write(self, values):
        on_hold_stage = self.env['helpdesk.stage'].search([('name', '=', 'On Hold')], limit=1)

        if 'stage_id' in values:
            new_stage_id = values.get('stage_id')
            if new_stage_id == on_hold_stage.id and self.is_on_hold_wizard_applied is False:

                raise ValidationError(_('You need to apply the On-Hold Reason through the wizard!'))

            # Set is_on_hold_wizard_applied to False for all stages other than 'On Hold'
            values[
                'is_on_hold_wizard_applied'] = False if new_stage_id != on_hold_stage.id else self.is_on_hold_wizard_applied
        return super(HelpdeskTicket, self).write(values)

    def action_set_on_hold(self):
        return {
            'name': 'On-Hold Reasons',
            'view_mode': 'form',
            'res_model': 'helpdesk.on_hold_reason_wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            },
        }


class HelpdeskOnHoldReasonWizard(models.TransientModel):
    _name = 'helpdesk.on_hold_reason_wizard'
    _description = 'Helpdesk On-Hold Reason Wizard'

    on_hold_reason_ids = fields.Many2one('helpdesk.on_hold_reason', string='On-Hold Reasons', required=True)
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', required=True)

    def action_hold_reason_apply(self):
        on_hold_stage = self.env['helpdesk.stage'].search([('name', '=', 'On Hold')], limit=1)

        if on_hold_stage and self.ticket_id:
            self.ticket_id.is_on_hold_wizard_applied = True
            self.ticket_id.on_hold_reason_id = self.on_hold_reason_ids
            self.ticket_id.stage_id = on_hold_stage.id
            return {'type': 'ir.actions.act_window_close'}
        else:
            return {'type': 'ir.actions.act_window_close'}

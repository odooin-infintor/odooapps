# -*- coding: utf-8 -*-

from odoo import models, fields,_, api
from lxml import etree
from markupsafe import Markup


class PoInherit(models.Model):
    _inherit = 'purchase.order'

    approver = fields.Many2one('res.users', string="Approver")
    is_approver = fields.Boolean(compute='is_approver_compute', default=False)

    def is_approver_compute(self):
        if self.approver == self.env.user:
            self.is_approver = True
        else:
            self.is_approver = False


    def rfq_approver_wizard(self):
        return {
            'name': _('Quotation Approver'),
            'type': 'ir.actions.act_window',
            'res_model': 'rfq.approver.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context':{
                'default_quotation': self.id,
            }
        }

class RFQWizard(models.TransientModel):
    _name =  'rfq.approver.wizard'
    _description = 'RFQ approver request wizard'

    approver = fields.Many2one('res.users', string="Approver", domain=[('share', '=', False)])
    quotation = fields.Many2one('purchase.order')

    def confirm(self):
        if self.approver:
            self.quotation.approver = self.approver
            action_id = self.env.ref('purchase.purchase_rfq').id
            rec_id = str(self.quotation.id)
            active_id = "web#id=%s&action=%s&model=purchase.order&view_type=form" %(rec_id, action_id) 
            message =  f'<strong>RFQ Approval Request</strong> ' \
                       f"<p>You have a RFQ approval (RFQ-ID : {self.quotation.name}) request from {self.env.user.name}  <a href={active_id}>click here</a></p>"
            self.env['odoobot.chat'].inbox_message(self.quotation.approver.partner_id.id,message)
    
    def cancel(self):
        if self.quotation:
            self.quotation = False
            self.approver = False
        return {'type': 'ir.actions.act_window_close'}
    
class OdooChatBot(models.Model):
    _name = 'odoobot.chat'
    _inherit = ['mail.thread']
    _description = 'Send user chat notification'

    def inbox_message(self, partner_id, message):
        """
        Send user chat notification on picking validation.
        """

        query = """
                SELECT c.id
                FROM discuss_channel c
                INNER JOIN discuss_channel_member cc ON c.id = cc.channel_id
                WHERE cc.partner_id = %s
                AND c.name LIKE '%s' LIMIT 1;
                """% (partner_id, 'OdooBot%')
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        if result:
            channel_id = result[0]['id']
        else:
            user = self.env['res.users'].search([('partner_id', '=', partner_id)])
            odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
            channel_info = self.env['discuss.channel'].sudo().with_user(user).channel_get([odoobot_id, partner_id])
            channel = self.env['discuss.channel'].browse(channel_info['id'])
            channel_id = channel.id
            user.odoobot_state = 'onboarding_emoji'

        # odoo runbot
        odoobot_id = self.env['ir.model.data'].sudo()._xmlid_to_res_id("base.partner_root")
        # find if a channel was opened for this user before
        
        channel = self.env['discuss.channel'].sudo().search([
            ('id', '=', channel_id),
            ('channel_partner_ids', 'in', [partner_id])
        ],
            limit=1,
        )

        message = Markup(message)
         
        if channel:
            # send a message to the related user
            channel.sudo().message_post(
                body=message,
                author_id=odoobot_id,
                message_type="comment",
                subtype_id=1,
            )


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    is_verified = fields.Boolean(default=False)

    def verify_bill(self):
        self.is_verified = True
        self.message_post(body=f"Bill is verified by {self.env.user.name}")

    @api.model 
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(AccountMoveInherit, self).get_view(view_id=view_id, view_type=view_type,**options)
        is_bill_creator = self.env.user.has_group('vendor_approver.group_bill_creation')
        is_base_user = self.env.user.has_group('base.group_system') 
        if not is_base_user:
            if not is_bill_creator: 
                if view_type == 'form': 
                    doc = etree.XML(res['arch']) 
                    for node in doc.xpath("//form[@string='Account Entry']"): 
                        node.set('create', '0') 
                    res['arch'] = etree.tostring(doc) 
                elif view_type == 'tree': 
                    doc = etree.XML(res['arch']) 
                    view = self.env['ir.ui.view'].browse(view_id)
                    if view.xml_id == 'account.view_in_invoice_bill_tree':
                        for node in doc.xpath("//tree[@string='Invoices']"): 
                            node.set('create', '0')
                        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    is_verified = fields.Boolean(default=False)

    def verify_bill(self):
        self.is_verified = True
        self.message_post(body=f"Payment is verified by {self.env.user.name}")

    @api.model 
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(AccountPaymentInherit, self).get_view(view_id=view_id, view_type=view_type,**options)
        is_payment_creator = self.env.user.has_group('vendor_approver.group_payment_creation')
        is_base_user = self.env.user.has_group('base.group_system') 
        if not is_base_user:
            if not is_payment_creator: 
                if view_type == 'form': 
                    doc = etree.XML(res['arch']) 
                    for node in doc.xpath("//form[@string='Register Payment']"): 
                        node.set('create', '0') 
                    res['arch'] = etree.tostring(doc) 
                elif view_type == 'tree': 
                    doc = etree.XML(res['arch']) 
                    view = self.env['ir.ui.view'].browse(view_id)
                    if view.xml_id == 'account.view_account_supplier_payment_tree':
                        for node in doc.xpath("//tree"): 
                            node.set('create', '0')
                        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
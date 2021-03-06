# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _


class HrEmployeeDependent(models.Model):
    _name = b'hr.employee.dependent'
    _inherit = ['hr.employee.dependent', 'mail.thread', 'ir.needaction_mixin']

    @api.multi
    def _compute_beneficios(self):
        for record in self:
            record.benefit_ids = self.env['hr.contract.benefit'].search(
                [('partner_id', '=', record.partner_id.id)]
            )
            record.benefit_count = len(record.benefit_ids)

    def action_view_benefits(self, cr, uid, ids, context=None):
        dependent = self.pool.get(
            'hr.employee.dependent').browse(cr, uid, ids)
        return {
            'name': _('Benefícios'),
            'view_type': 'tree,form',
            'view_mode': 'tree,form',
            'res_model': 'hr.contract.benefit',
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', dependent.benefit_ids.ids)]
        }

    benefit_ids = fields.Many2many(
        comodel_name='hr.contract.benefit',
        string='Benefícios ativos',
        readonly=True,
        compute='_compute_beneficios',
        track_visibility='onchange',
    )
    benefit_count = fields.Integer(
        string='Número de benefícios',
        compute='_compute_beneficios',
    )
    state = fields.Selection(
        selection=[
            ('to approve', 'A aprovar'),
            ('approved', 'Aprovada'),
        ],
        track_visibility='onchange',
        default='to approve'
    )
    partner_id = fields.Many2one(
        track_visibility='onchange',
    )
    employee_id = fields.Many2one(
        track_visibility='onchange',
    )
    dependent_dob = fields.Date(
        track_visibility='onchange',
    )
    dependent_type_id = fields.Many2one(
        track_visibility='onchange',
    )
    pension_benefits = fields.Float(
        track_visibility='onchange',
    )
    dependent_verification = fields.Boolean(
        track_visibility='onchange',
    )
    health_verification = fields.Boolean(
        track_visibility='onchange',
    )
    dependent_gender = fields.Selection(
        track_visibility='onchange',
    )
    have_alimony = fields.Boolean(
        track_visibility='onchange',
    )
    partner_id_bank_ids = fields.One2many(
        track_visibility='onchange',
    )
    dep_sf = fields.Boolean(
        track_visibility='onchange',
    )
    inc_trab = fields.Boolean(
        track_visibility='onchange',
    )
    inc_trab_inss_file = fields.Binary(
        track_visibility='onchange',
    )
    precisa_cpf = fields.Boolean(
        track_visibility='onchange',
    )
    relative_file = fields.Binary(
        track_visibility='onchange',
    )

    @api.multi
    def button_approve(self):
        for record in self:
            record.state = 'approved'

    @api.multi
    def button_to_approve(self):
        for record in self:
            record.state = 'to approve'

    @api.model
    def create(self, vals):
        hr_users = self.env.ref('base.group_hr_user').users
        partner_ids = [user.partner_id.id for user in hr_users]
        vals.update({
            'message_follower_ids': partner_ids
        })
        if self.env.user.has_group('base.group_hr_user'):
            vals['state'] = 'approved'
        return super(HrEmployeeDependent, self.sudo()).create(vals)

    @api.multi
    def write(self, vals):
        return super(HrEmployeeDependent, self).write(vals)

    @api.model
    def _needaction_domain_get(self):
        res =super(HrEmployeeDependent, self)._needaction_domain_get()
        return ['|'] + res + [('state', '=', 'to approve')]

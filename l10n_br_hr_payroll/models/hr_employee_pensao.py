# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class HrEmployeePensao(models.Model):
    _name = 'hr.employee.pensao'

    tipo = fields.Selection(
        string=u'Tipo da Pensão',
        selection=[
            ('fixo', 'Valor Fixo'),
            ('porcentagem', 'Porcentagem do Líquido'),
        ],
    )

    valor = fields.Float(
        string='Valor',
    )

    porcentagem = fields.Float(
        string='Porcentagem',
    )

    beneficiario_id = fields.Many2one(
        string=u'Beneficiário',
        comodel_name='res.partner',
    )

    employee_id = fields.Many2one(
        string='Empregado',
        comodel_name='hr.employee',
    )

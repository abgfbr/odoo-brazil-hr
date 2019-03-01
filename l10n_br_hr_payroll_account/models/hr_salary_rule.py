# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# Copyright (C) 2018 ABGF (http://www.abgf.gov.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from __future__ import absolute_import, print_function, unicode_literals

from openerp import fields, models


class HrSalaryRule(models.Model):
    _inherit = b'hr.salary.rule'

    gerar_contabilizacao = fields.Boolean(
        string='Gerar Contabilização?',
        default='True',
        help='Indica se rubrica irá gerar contabilização',
    )

    account_event_template_id = fields.Many2one(
        string='Roteiro Contábil',
        comodel_name='account.event.template',
    )

    account_event_template_line_id = fields.Many2one(
        string='Linha do Roteiro Contábil',
        comodel_name='account.event.template.line',
        domain=
        "[('account_event_template_id', '=', account_event_template_id)]",
    )

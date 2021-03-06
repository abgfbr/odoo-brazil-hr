# -*- coding: utf-8 -*-
# Copyright (C) 2019 ABGF (http://www.abgf.gov.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class HrPayslipeLine(models.Model):
    _inherit = "hr.payslip.line"

    codigo_contabil = fields.Char(
        string=u'Código de Contabilização',
    )

    account_event_line_id = fields.Many2one(
        string='Linha do Evento',
        comodel_name='account.event.line',
    )

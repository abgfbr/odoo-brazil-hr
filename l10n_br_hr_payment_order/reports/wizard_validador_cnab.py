# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import (
    MES_DO_ANO,
)
from openerp.exceptions import ValidationError


class WizardValidadorCnab(models.TransientModel):

    _name = 'wizard.validador.cnab'

    cnab_file = fields.Binary(
        string='CNAB File',
        readonly=True,
    )

    cnab_filename = fields.Char("CNAB Filename")



    @api.multi
    def doit(self):

        pass
        # busca = [
        #     ('company_id', '=', self.company_id.id),
        #     ('mes_do_ano', '=', self.mes_do_ano),
        #     ('ano', '=', self.ano),
        #     ('state', 'in', ['done', 'verify']),
        # ]
        # if self.tipo_de_folha == "('normal', 'rescisao')":
        #     busca.append(('tipo_de_folha', 'in', eval(self.tipo_de_folha)))
        # else:
        #     busca.append(('tipo_de_folha', '=', eval(self.tipo_de_folha)))
        # payslip_ids = self.env['hr.payslip'].search(busca)
        #
        # if not payslip_ids:
        #     raise ValidationError(
        #         _('Não foi encontrado lote de holerite '
        #           'dentro do período selecionado.'))
        #
        # else:
        #     return self.env['report'].get_action(
        #         self, "l10n_br_hr_payroll_report.report_analyticreport")

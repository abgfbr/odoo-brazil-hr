# -*- coding: utf-8 -*-
# Copyright (C) 2019  Luiz Felipe do Divino - ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields
from openerp.exceptions import Warning


TIPO_ACORDOS = [
    ('A', 'Acordo Coletivo de Trabalho'),
    ('B', 'Legislação Federal, Estadual, Municipal ou Distrital'),
    ('C', 'Convenção Coletiva de Trabalho'),
    ('D', 'Setença Normativa - Dissídio'),
    ('E', 'Conversão de Licença Saúde em Acidente de Trabalho'),
    ('F', 'Outras verbas de natureza salarial ou não salarial devidas após o desligamento'),
]


class L10nBrHrAcordoColetivo(models.Model):
    _name = 'l10n.br.hr.acordo.coletivo'

    name = fields.Char(
        string='name',
        compute='_compute_name'
    )
    data_assinatura_acordo = fields.Date(
        string='Data Assinatura Acordo',
    )
    tipo_acordo = fields.Selection(
        string='Tipo do Acordo',
        selection=TIPO_ACORDOS,
    )
    competencia_pagamento = fields.Many2one(
        string='Competência de Pagamento',
        comodel_name='account.period',
        help='Competência em que será preciso pagar os '
             'valores reajustados e retroativos',
    )
    data_efetivacao = fields.Date(
        string='Data da Efetivação Retroativa',
    )
    descricao = fields.Char(
        string=u'Descrição',
    )
    remuneracao_relativa_sucessao = fields.Selection(
        string='Remuneração relativa a sucessão',
        selection=[
            ('S', 'Sim'),
            ('N', u'Não'),
        ],
        help='Indicar se a remuneração é relativa a verbas de natureza salarial '
             'ou não salarial devidas pela empresa sucessora a empregados '
             'desligados ainda na sucedida',
    )
    valor_reajuste_salarial = fields.Float(
        string='Valor Reajuste(%)',
    )

    rubrica_ids = fields.One2many(
        string=u'Rúbricas',
        comodel_name='l10n.br.hr.acordo.coletivo.rubricas',
        inverse_name='acordo_coletivo_id',
    )

    periodo_ids = fields.One2many(
        string='Periodos',
        comodel_name='account.period',
        inverse_name='acordo_coletivo_id',
    )

    diferenca_periodo_ids = fields.One2many(
        string=u'Diferenças nos períodos',
        comodel_name='hr.contract.salary.rule',
        inverse_name='acordo_coletivo_id'
    )

    faixa_ids = fields.One2many(
        string="Faixas Saláriais",
        comodel_name="l10n.br.hr.acordo.coletivo.faixas",
        inverse_name="acordo_coletivo_id"
    )

    tipo_reajuste = fields.Selection(
        string="Tipo de Reajuste",
        selection=[
            ("fixo", "Fixo"),
            ("faixas", "Faixas Salariais"),
        ],
        default="fixo"
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = 'Acordo Coletivo - {}'.format(
                record.competencia_pagamento.code or '--/----')

    @api.multi
    def _get_periodos_retroativos(self):
        for record in self:
            periodos = self.env['account.period'].search(
                [
                    ('date_start', '>=', record.data_efetivacao),
                    ('date_stop', '<', record.competencia_pagamento.date_stop),
                    ('special', '=', False),
                ]
            )

            record.periodo_ids = [(6, 0, periodos.ids)]

    @api.multi
    def _get_dicionario_rubricas(self):
        rubricas = {}
        for rubrica in self.rubrica_ids:
            rubricas[rubrica.rubrica_holerite_id.id] = \
                rubrica.rubrica_diferenca_id.id

        return rubricas

    @api.multi
    def _get_diferencas_retroativas(self):
        for record in self:
            if not record.periodo_ids:
                record._get_periodos_retroativos()

            record.diferenca_periodo_ids.unlink()

            contract_ids = self.env['hr.contract'].search(
                [('date_end', '=', False)])

            rubricas = record._get_dicionario_rubricas()

            for contrato in contract_ids:
                for periodo in record.periodo_ids:
                    payslip_ids = self.env['hr.payslip'].search(
                        [('date_from', '>=', periodo.date_start),
                         ('date_from', '<=', periodo.date_stop),
                         ('tipo_de_folha', 'in', ['normal']),
                         ('contract_id', '=', contrato.id)]
                    )

                    for payslip in payslip_ids:
                        salario_base = payslip.input_line_ids.filtered(
                            lambda v: v.code == "SALARIO_MES").amount
                        for line in payslip.line_ids:
                            if rubricas.get(line.salary_rule_id.id) and line.total and line.code not in ("FERIAS_FERIAS", "1/3_FERIAS_FERIAS", "1/3_FERIAS_S_ONUS_FERIAS", "ABONO_PECUNIARIO_FERIAS", "1/3_ABONO_PECUNIARIO_FERIAS", "ADIANTAMENTO_13", "ADIANTAMENTO_13_FERIAS"):
                                record._gerar_linha_acordo_coletivo(
                                    contrato, line, periodo,
                                    record.competencia_pagamento,
                                    rubricas[line.salary_rule_id.id],
                                    salario_base
                                )

                ferias_mes_corrente = self.env['hr.payslip'].search(
                    [('date_to', '>=', self.data_efetivacao),
                     ('tipo_de_folha', 'in', ['ferias']),
                     ('contract_id', '=', contrato.id),
                     ('state', '=', 'done')]
                )

                for payslip in ferias_mes_corrente:
                    periodo = self.env["account.period"].search([
                        ("code", "=", "{}/{}".format("{0:02d}".format(payslip.mes_do_ano), payslip.ano)),
                    ])
                    salario_base = payslip.input_line_ids.filtered(
                        lambda v: v.code == "SALARIO_MES").amount
                    for line in payslip.line_ids:
                        if rubricas.get(line.salary_rule_id.id) and line.total:
                            record._gerar_linha_acordo_coletivo(
                                contrato, line, periodo,
                                record.competencia_pagamento,
                                rubricas[line.salary_rule_id.id],
                                salario_base
                            )

    def _gerar_linha_acordo_coletivo(
            self, contrato, line, periodo, competencia_pagamento, rubrica_id,
            salario_base):

        valor_bruto = line.total
        porcentagem = 0
        valor_diferenca = 0

        if contrato.category_id.id == self.env.ref("l10n_br_hr_payroll.hr_contract_category_410").id:
            diferenca_salarios_proporcional = \
                (contrato.wage - salario_base) / salario_base

            diferenca_salarios_proporcional += 1

            novo_valor = \
                (valor_bruto * diferenca_salarios_proporcional) - valor_bruto

            vals = {
                'contract_id': contrato.id,
                'rule_id': rubrica_id,
                'tipo_holerite': 'normal',
                'date_start': competencia_pagamento.date_start,
                'date_stop': competencia_pagamento.date_stop,
                'ref': '{}-{}'.format(periodo.code[3:], periodo.code[:2]),
                'specific_quantity': 1,
                'specific_percentual': 100,
                'specific_amount': novo_valor,
                'acordo_coletivo_id': self.id,
            }

            self.env['hr.contract.salary.rule'].create(vals)
        elif line.code == "SALARIO_SUBST":
            salario_antigo_gerente = \
                contrato.gerente_id.contract_id.change_salary_ids.filtered(
                    lambda v: v.change_reason_id.id == 3)[1].wage
            salario_atual_gerente = contrato.gerente_id.contract_id.wage

            diferenca_salarial_antiga = salario_antigo_gerente - salario_base
            diferenca_salarial_atual = salario_atual_gerente - contrato.wage

            proporcao_salario_antigo = valor_bruto / diferenca_salarial_antiga

            salario_substituicao_atual = \
                proporcao_salario_antigo * diferenca_salarial_atual

            diferenca_salario_substituicao_retro = \
                salario_substituicao_atual - valor_bruto

            vals = {
                'contract_id': contrato.id,
                'rule_id': rubrica_id,
                'tipo_holerite': 'normal',
                'date_start': competencia_pagamento.date_start,
                'date_stop': competencia_pagamento.date_stop,
                'ref': '{}-{}'.format(periodo.code[3:], periodo.code[:2]),
                'specific_quantity': 1,
                'specific_percentual': 100,
                'specific_amount': diferenca_salario_substituicao_retro,
                'acordo_coletivo_id': self.id,
            }

            self.env['hr.contract.salary.rule'].create(vals)
        else:
            substituicao_ferias = False
            if line.slip_id.tipo_de_folha == "ferias":
                substituicao_ferias = line.slip_id.line_ids.filtered(
                    lambda x: x.code == "MEDIA_SALARIO_FERIAS" and x.total)

            if not substituicao_ferias:
                if self.tipo_reajuste == "fixo":
                    if line.slip_id.date_from < self.data_efetivacao:
                        current_days = (fields.Date.from_string(line.slip_id.date_to) - fields.Date.from_string(self.data_efetivacao)).days + 1
                        dias_mes_competencia = line.slip_id.worked_days_line_ids.filtered(lambda v: v.code == "DIAS_MES_COMPETENCIA_SEGUINTE").number_of_days
                        valor_bruto = (salario_base/dias_mes_competencia) * current_days
                        if line.code in ('1/3_FERIAS', '1/3_FERIAS_S_ONUS'):
                            valor_bruto /= 3
                        periodo = self.periodo_ids[0]

                    porcentagem = 1 + (self.valor_reajuste_salarial / 100)
                    valor_diferenca = (valor_bruto * porcentagem) - valor_bruto

                    rubrica_ref_id = self.env['hr.contract.salary.rule'].search(
                        [
                            ('contract_id', '=', contrato.id),
                            ('rule_id', '=', rubrica_id),
                            ('tipo_holerite', '=', 'normal'),
                            ('ref', '=', '{}-{}'.format(periodo.code[3:],
                                                        periodo.code[:2])),
                            ('acordo_coletivo_id', '=', self.id)
                        ])

                    if rubrica_ref_id:
                        rubrica_ref_id.write({
                            'specific_amount': rubrica_ref_id.specific_amount + valor_diferenca
                        })
                    else:
                        vals = {
                            'contract_id': contrato.id,
                            'rule_id': rubrica_id,
                            'tipo_holerite': 'normal',
                            'date_start': competencia_pagamento.date_start,
                            'date_stop': competencia_pagamento.date_stop,
                            'ref': '{}-{}'.format(periodo.code[3:], periodo.code[:2]),
                            'specific_quantity': 1,
                            'specific_percentual': 100,
                            'specific_amount': valor_diferenca,
                            'acordo_coletivo_id': self.id,
                        }

                        self.env['hr.contract.salary.rule'].create(vals)
                elif self.tipo_reajuste == "faixas":
                    for faixa in self.faixa_ids:
                        porcentagem = 1 + (faixa.porcentagem / 100)
                        valor_base = 0
                        if faixa.teto == 0:
                            valor_base = salario_base - faixa.piso
                        else:
                            valor_base = faixa.teto - faixa.piso

                        valor_proporcional_base = valor_base/salario_base
                        proporcao_antiga = valor_bruto * valor_proporcional_base
                        valor_diferenca += (proporcao_antiga * porcentagem) - proporcao_antiga

                    vals = {
                        'contract_id': contrato.id,
                        'rule_id': rubrica_id,
                        'tipo_holerite': 'normal',
                        'date_start': competencia_pagamento.date_start,
                        'date_stop': competencia_pagamento.date_stop,
                        'ref': '{}-{}'.format(periodo.code[3:], periodo.code[:2]),
                        'specific_quantity': 1,
                        'specific_percentual': 100,
                        'specific_amount': valor_diferenca,
                        'acordo_coletivo_id': self.id,
                    }

                    self.env['hr.contract.salary.rule'].create(vals)
            else:
                if line.slip_id.date_from > self.data_efetivacao and line.code in ('FERIAS', '1/3_FERIAS'):
                    dias_mes_competencia = line.slip_id.worked_days_line_ids.filtered(lambda v: v.code == "DIAS_MES_COMPETENCIA_ATUAL").number_of_days
                    dias_mes_competencia_seguinte = line.slip_id.worked_days_line_ids.filtered(lambda v: v.code == "DIAS_MES_COMPETENCIA_SEGUINTE").number_of_days
                    ferias_competencia = line.slip_id.line_ids.filtered(lambda v: v.code == "FERIAS_COMPETENCIA_ATUAL").quantity
                    ferias_competencia_seguinte = line.slip_id.line_ids.filtered(lambda v: v.code == "FERIAS_COMPETENCIA_SEGUINTE").quantity
                    valor_bruto = (salario_base / dias_mes_competencia) * ferias_competencia
                    valor_bruto += (salario_base / dias_mes_competencia_seguinte) * ferias_competencia_seguinte
                    if line.code in ('1/3_FERIAS', '1/3_FERIAS_S_ONUS'):
                        valor_bruto /= 3

                valor_diferenca = (valor_bruto * (1 + (self.valor_reajuste_salarial/100))) - valor_bruto

                rubrica_ref_id = self.env['hr.contract.salary.rule'].search([
                    ('contract_id', '=', contrato.id),
                    ('rule_id', '=', rubrica_id),
                    ('tipo_holerite', '=', 'normal'),
                    ('ref', '=', '{}-{}'.format(periodo.code[3:], periodo.code[:2])),
                    ('acordo_coletivo_id', '=', self.id)
                ])

                if rubrica_ref_id:
                    rubrica_ref_id.write({
                        'specific_amount': rubrica_ref_id.specific_amount + valor_diferenca
                    })
                else:
                    vals = {
                        'contract_id': contrato.id,
                        'rule_id': rubrica_id,
                        'tipo_holerite': 'normal',
                        'date_start': competencia_pagamento.date_start,
                        'date_stop': competencia_pagamento.date_stop,
                        'ref': '{}-{}'.format(periodo.code[3:], periodo.code[:2]),
                        'specific_quantity': 1,
                        'specific_percentual': 100,
                        'specific_amount': valor_diferenca,
                        'acordo_coletivo_id': self.id,
                    }

                    self.env['hr.contract.salary.rule'].create(vals)

    @api.multi
    def buscar_periodos_retroativos(self):
        for record in self:
            record._get_periodos_retroativos()

    @api.multi
    def gerar_diferencas_retroativos(self):
        for record in self:
            if record.tipo_reajuste == "faixas" and not record.faixa_ids:
                raise Warning(
                    "É preciso definiar as faixas de reajuste de salário!"
                )

            if record.periodo_ids:
                record._get_diferencas_retroativas()
            else:
                raise Warning(
                    "É preciso primeiro buscar os períodos retroativos!"
                )

    @api.multi
    def unlink(self):
        for record in self:
            record.diferenca_periodo_ids.unlink()

        return super(L10nBrHrAcordoColetivo, self).unlink()


class L10nBrHrAcordoColetivoRubrias(models.Model):
    _name = 'l10n.br.hr.acordo.coletivo.rubricas'

    rubrica_holerite_id = fields.Many2one(
        string=u'Rúbrica do Holerite',
        comodel_name='hr.salary.rule',
    )
    rubrica_diferenca_id = fields.Many2one(
        string=u'Rúbrica da Diferença',
        comodel_name='hr.salary.rule',
    )
    acordo_coletivo_id = fields.Many2one(
        string='Acordo Coletivo',
        comodel_name='l10n.br.hr.acordo.coletivo',
    )


class L10nBrHrAcordoColetivoFaixas(models.Model):
    _name = "l10n.br.hr.acordo.coletivo.faixas"
    _order = "piso ASC"

    acordo_coletivo_id = fields.Many2one(
        string="Acordo Coletivo",
    )
    piso = fields.Float(
        string="Piso",
    )
    teto = fields.Float(
        string="Teto",
    )
    porcentagem = fields.Float(
        string="Porcentagem",
    )

# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Corensult Solutions. (Website: www.corensultsolutions.com).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################
from odoo import fields, models, api, _
import base64
import datetime
from odoo.exceptions import ValidationError
import csv
import calendar
import os
import tempfile
import logging


_logger = logging.getLogger(__name__)


class VatReportWizard(models.TransientModel):
    _name = 'vat.report.wizard'
    _description = "Vat Report"

    month_of = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'Jun'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], string="Month")
    year_of = fields.Char(string="Year")
    tax_id = fields.Many2many('account.tax', string="Tax")

    def print_sale_vat_xlsx_report(self):
        lastDayOfMonth = calendar.monthrange(
            int(self.year_of), int(self.month_of))[1]
        startDate = '%s-%s-01' % (self.year_of, self.month_of)
        endDate = '%s-%s-%s' % (self.year_of, self.month_of, lastDayOfMonth)

        invoice_objs = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('invoice_date', '>=', startDate),
            ('invoice_date', '<=', endDate)
        ])
        file_fd, file_path = tempfile.mkstemp(
            suffix='.csv', prefix='sale_vat_report')
        csv_data = []
        no_vat_amount_total = 0
        # if invoice_objs.filtered(lambda inv: inv.partner_id.vat):
        if invoice_objs:
            _logger.info("inv_objs exist")
            # for inv in invoice_objs.filtered(lambda inv: inv.partner_id.vat):
            for inv in invoice_objs:
                rInv = False
                has_tax = False
                if inv.move_type == 'out_refund' and inv.reversed_entry_id:
                    rInv = self.env['account.move'].search([
                        ('id', '=', inv.reversed_entry_id.id)])
                amount = 0.0
                for invoice_line in inv.line_ids:
                    # price_unit = invoice_line.price_unit * (1 - (invoice_line.discount or 0.0) / 100.0)
                    # taxes = self.tax_id.compute_all(
                    #     price_unit,
                    #     inv.currency_id,
                    #     invoice_line.quantity,
                    #     invoice_line.product_id,
                    #     inv.partner_id)['taxes']
                    for rec in self.tax_id:
                        for tax in invoice_line.tax_ids:
                            if rec.id == tax.id:
                                _logger.info("matching tax")
                                has_tax = True

                                price = invoice_line.price_unit * (1 - (invoice_line.discount or 0.0) / 100.0)
                                taxes = tax.compute_all(price, invoice_line.currency_id, invoice_line.quantity, product=invoice_line.product_id or False, partner=invoice_line.partner_id)
                                if inv.move_type == 'out_refund':
                                    amount += (-1 * taxes['taxes'][0]['base'])
                                else:
                                    amount += taxes['taxes'][0]['base']
                                # for amount in taxes:
                                #     tax_amount += amount['amount']
                if has_tax:
                    _logger.info("has tax")
                    if inv.partner_id.vat:
                        _logger.info("partner has vat %s" % inv.partner_id.vat)
                        data = [inv.partner_id.vat or '',
                                inv.partner_id.name or '',
                                inv.company_id.company_registry or '',
                                inv.invoice_date.strftime("%d/%m/%Y"),
                                inv.name or '',
                                'Sales',
                                amount*inv.exchange_rate,
                                '',
                                inv.reversed_entry_id.name if rInv else '',
#                                 inv.source_document_date.strftime("%d/%m/%Y")
#                                 or inv.reversed_entry_id.invoice_date.strftime("%d/%m/%Y") if rInv else '', ]
                                inv.reversed_entry_id.invoice_date.strftime("%d/%m/%Y") if rInv else '', ]

                        csv_data.append(data)
                    else:
                        _logger.info("partner has no vat")
                        _logger.info("partner name %s" % inv.partner_id.name)
                        _logger.info("partner vat %s" % inv.partner_id.vat)
                        no_vat_amount_total += amount*inv.exchange_rate
            _logger.info("csv data %s" % csv_data)
            no_vat_cash_data = [
                'No VAT',
                'Cash',
                '',
                '',
                '',
                'Sales',
                no_vat_amount_total,
                '',
                '',
                '',
            ]
            csv_data.append(no_vat_cash_data)
            _logger.info("csv data %s" % csv_data)
            with open(file_path, "w") as writeFile:
                writer = csv.writer(writeFile)
                # writer.writerows([[
                #'PIN Number',
                #'Customer Name',
                #'ETR Number',
                #'Invoice Date',
                #'Invoice Number',
                #'Description of Goods/Services',
                #'Taxable Amount',
                #'Amount of VAT',
                #'Relevant Invoice Number',
                #'Relevant Invoice Date'
                # ]])
                writer.writerows(csv_data)
            writeFile.close()

            result_file = open(file_path, 'rb').read()
            attachment_id = self.env['wizard.excel.report'].create({
                'name': 'Sales - %s %s.csv' % (calendar.month_name[int(self.month_of)], self.year_of),
                'report': base64.encodestring(result_file)
            })
            try:
                os.unlink(file_path)
            except (OSError, IOError):
                _logger.error(
                    'Error when trying to remove file %s' % file_path)

            return {
                'name': _('Odoo'),
                'context': self.env.context,
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.excel.report',
                'res_id': attachment_id.id,
                'data': None,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise ValidationError(
                _('Invoice are Not Present in this month!!!'))

    def print_purchase_vat_xlsx_report(self):
        lastDayOfMonth = calendar.monthrange(
            int(self.year_of), int(self.month_of))[1]
        startDate = '%s-%s-01' % (self.year_of, self.month_of)
        endDate = '%s-%s-%s' % (self.year_of, self.month_of, lastDayOfMonth)

        invoice_objs = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('invoice_date', '>=', startDate),
            ('invoice_date', '<=', endDate)
        ])
        file_fd, file_path = tempfile.mkstemp(
            suffix='.csv', prefix='purchase_vat_report')
        csv_data = []
        no_vat_amount_total = 0
        # if invoice_objs.filtered(lambda inv: inv.partner_id.vat):
        if invoice_objs:
            # for inv in invoice_objs.filtered(lambda inv: inv.partner_id.vat):
            for inv in invoice_objs:
                rInv = False
                has_tax = False
                if inv.move_type == 'in_refund' and inv.reversed_entry_id:
                    rInv = self.env['account.move'].search([
                        ('id', '=', inv.reversed_entry_id.id)])
                amount = 0.0
                for invoice_line in inv.line_ids:
                    for rec in self.tax_id:
                        for tax in invoice_line.tax_ids:
                            if rec.id == tax.id:
                                has_tax = True
                                price = invoice_line.price_unit * (1 - (invoice_line.discount or 0.0) / 100.0)
                                taxes = tax.compute_all(price, invoice_line.currency_id, invoice_line.quantity, product=invoice_line.product_id or False, partner=invoice_line.partner_id)
                                if inv.move_type == 'in_refund':
                                    amount += (-1 * taxes['taxes'][0]['base'])
                                else:
                                    amount += taxes['taxes'][0]['base']
                if has_tax:
                    if inv.partner_id.vat:
                        data = [inv.partner_id.category_id.name,
                                inv.partner_id.vat,
                                inv.partner_id.name,
                                inv.invoice_date.strftime("%d/%m/%Y"),
                                inv.credit_note_number if inv.move_type == 'in_refund' else inv.ven_inv_no,
                                'Purchases',
                                inv.custom_entry_number if inv.custom_entry_number else '',
                                amount*inv.exchange_rate,
                                '',
                                inv.ven_inv_no if rInv else '',
                                rInv.invoice_date.strftime("%d/%m/%Y") if rInv and rInv.invoice_date else '', ]

                        csv_data.append(data)
                    else:
                        no_vat_amount_total += amount*inv.exchange_rate

            no_vat_cash_data = [
                'Cash',
                'No VAT',
                'Cash',
                '',
                '',
                'Purchases',
                '',
                no_vat_amount_total,
                '',
                '',
                '',
            ]
            csv_data.append(no_vat_cash_data)
            with open(file_path, "w") as writeFile:
                writer = csv.writer(writeFile)
                # writer.writerows([[
                #'Type of Purchase',
                #'PIN Number',
                #'Vendor Name',
                #'Bill Date',
                #'Invoice Number',
                #'Description of Goods/Services',
                #'Custom Entry Number',
                #'Taxable Amount',
                #'Amount of VAT',
                #'Relevant Invoice Number',
                #'Relevant Invoice Date'
                # ]])
                writer.writerows(csv_data)
            writeFile.close()

            result_file = open(file_path, 'rb').read()
            attachment_id = self.env['wizard.excel.report'].create({
                'name': 'Purchases - %s %s.csv' % (calendar.month_name[int(self.month_of)], self.year_of),
                'report': base64.encodestring(result_file)
            })
            try:
                os.unlink(file_path)
            except (OSError, IOError):
                _logger.error(
                    'Error when trying to remove file %s' % file_path)
            return {
                'name': _('Odoo'),
                'context': self.env.context,
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.excel.report',
                'res_id': attachment_id.id,
                'data': None,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }
        else:
            raise ValidationError(
                _('Invoice are Not Present in this month!!!'))


class WizardExcelReport(models.TransientModel):
    _name = 'wizard.excel.report'
    _description = "Vat Excel Report"

    name = fields.Char('File Name', size=64)
    report = fields.Binary('Excel Report', readonly=True)

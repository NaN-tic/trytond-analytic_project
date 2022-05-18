# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If

from trytond.modules.analytic_account import AnalyticMixin


class Work(AnalyticMixin, metaclass=PoolMeta):
    __name__ = 'project.work'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.analytic_accounts.domain = [
            ('company', '=', If(~Eval('company'),
                    Eval('context', {}).get('company', -1),
                    Eval('company', -1))),
            ]
        cls.analytic_accounts.depends.add('company')

    def _get_invoice_line(self, key, invoice, lines):
        "Return a invoice line for the lines"
        pool = Pool()
        AnalyticAccountEntry = pool.get('analytic.account.entry')

        invoice_line = super(Work, self)._get_invoice_line(key, invoice, lines)
        if self.analytic_accounts:
            new_entries = AnalyticAccountEntry.copy(self.analytic_accounts,
                default={
                    'origin': None,
                    })
            invoice_line.analytic_accounts = new_entries
        return invoice_line


class AnalyticAccountEntry(metaclass=PoolMeta):
    __name__ = 'analytic.account.entry'

    @classmethod
    def _get_origin(cls):
        origins = super(AnalyticAccountEntry, cls)._get_origin()
        return origins + ['project.work']

    @fields.depends('origin')
    def on_change_with_company(self, name=None):
        pool = Pool()
        ProjectWork = pool.get('project.work')

        company = super(AnalyticAccountEntry, self).on_change_with_company(
            name)
        if isinstance(self.origin, ProjectWork) and self.origin.company:
            company = self.origin.company.id
        return company

    @classmethod
    def search_company(cls, name, clause):
        domain = super(AnalyticAccountEntry, cls).search_company(name, clause),
        return ['OR',
            domain,
            (('origin.' + clause[0],) + tuple(clause[1:3])
                + ('project.work',) + tuple(clause[3:])),
            ]

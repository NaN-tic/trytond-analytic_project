# This file is part analytic_project module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import project

def register():
    Pool.register(
        project.Work,
        project.AnalyticAccountEntry,
        module='analytic_project', type_='model')

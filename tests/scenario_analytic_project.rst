===================================
Analytic Project Timesheet Scenario
===================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_chart, \
    ...     get_accounts
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     create_payment_term
    >>> today = datetime.date.today()
    >>> yesterday = today - datetime.timedelta(days=1)

Activate modules::

    >>> config = activate_modules('analytic_project')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create project user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> project_user = User()
    >>> project_user.name = 'Project'
    >>> project_user.login = 'project'
    >>> project_group, = Group.find([('name', '=', 'Project Administration')])
    >>> timesheet_group, = Group.find([('name', '=', 'Timesheet Administration')])
    >>> project_user.groups.extend([project_group, timesheet_group])
    >>> project_user.save()

Create project invoice user::

    >>> project_invoice_user = User()
    >>> project_invoice_user.name = 'Project Invoice'
    >>> project_invoice_user.login = 'project_invoice'
    >>> project_invoice_group, = Group.find([('name', '=', 'Project Invoice')])
    >>> project_group, = Group.find([('name', '=', 'Project Administration')])
    >>> project_invoice_user.groups.extend(
    ...     [project_invoice_group, project_group])
    >>> project_invoice_user.save()

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']

Create analytic accounts::

    >>> AnalyticAccount = Model.get('analytic_account.account')
    >>> root = AnalyticAccount(type='root', name='Root')
    >>> root.save()
    >>> analytic_account = AnalyticAccount(root=root, parent=root,
    ...     name='Analytic')
    >>> analytic_account.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.customer_payment_term = payment_term
    >>> customer.save()

Create employee::

    >>> Employee = Model.get('company.employee')
    >>> employee = Employee()
    >>> party = Party(name='Employee')
    >>> party.save()
    >>> employee.party = party
    >>> employee.company = company
    >>> employee.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_revenue = revenue
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> hour, = ProductUom.find([('name', '=', 'Hour')])
    >>> ProductTemplate = Model.get('product.template')

    >>> template = ProductTemplate()
    >>> template.name = 'Service'
    >>> template.default_uom = hour
    >>> template.type = 'service'
    >>> template.list_price = Decimal('20')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

Create a Project::

    >>> ProjectWork = Model.get('project.work')
    >>> project = ProjectWork()
    >>> project.name = 'Test timesheet'
    >>> project.type = 'project'
    >>> project.party = customer
    >>> project.project_invoice_method = 'timesheet'
    >>> project.product = product
    >>> project.timesheet_available = True
    >>> entry, = project.analytic_accounts
    >>> entry.root == root
    True
    >>> entry.account = analytic_account
    >>> task = ProjectWork()
    >>> task.name = 'Task 1'
    >>> task.timesheet_available = True
    >>> task.type = 'task'
    >>> task.product = product
    >>> entry, = task.analytic_accounts
    >>> entry.root == root
    True
    >>> entry.account = analytic_account
    >>> project.children.append(task)
    >>> project.save()
    >>> task, = project.children

Create timesheets::

    >>> TimesheetLine = Model.get('timesheet.line')
    >>> line = TimesheetLine()
    >>> line.date = yesterday
    >>> line.employee = employee
    >>> line.duration = datetime.timedelta(hours=3)
    >>> line.work, = task.timesheet_works
    >>> line.save()
    >>> line = TimesheetLine()
    >>> line.date = today
    >>> line.employee = employee
    >>> line.duration = datetime.timedelta(hours=2)
    >>> line.work, = project.timesheet_works
    >>> line.save()

Check project amounts::

    >>> project.reload()
    >>> project.amount_to_invoice
    Decimal('100.00')
    >>> project.invoiced_amount
    Decimal('0.00')

Invoice project up to yesterday::

    >>> project.project_invoice_timesheet_up_to = yesterday
    >>> project.save()
    >>> project.click('invoice')
    >>> project.amount_to_invoice
    Decimal('40.00')
    >>> project.invoiced_amount
    Decimal('60.00')

Check Invoice Lines::

    >>> InvoiceLine = Model.get('account.invoice.line')
    >>> line1, line2 = InvoiceLine.find([])
    >>> len(line1.analytic_accounts) == 1
    True
    >>> analytic_account1, = line1.analytic_accounts
    >>> (analytic_account1.root, analytic_account1.account) == (root, analytic_account)
    True

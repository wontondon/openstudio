# -*- coding: utf-8 -*-

from general_helpers import max_string_length
from general_helpers import get_ajax_loader

from openstudio.os_workshop_product import WorkshopProduct
from openstudio.os_invoice import Invoice

from os_upgrade import set_version


def to_login(var=None):
    redirect(URL('default', 'user', args=['login']))


def index():
    """
        This function executes commands needed for upgrades to new versions
    """
    # first check if a version is set
    if not db.sys_properties(Property='Version'):
        db.sys_properties.insert(Property='Version',
                                 PropertyValue=0)
        db.sys_properties.insert(Property='VersionRelease',
                                 PropertyValue=0)

    # check if a version is set and get it
    if db.sys_properties(Property='Version'):
        version = float(db.sys_properties(Property='Version').PropertyValue)

        if version < 2018.1:
            print version
            session.flash = T("Please upgrade to at least 2018.1 before running upgrade for any later versions")

        if version < 2018.2:
            print version
            upgrade_to_20182()
            session.flash = T("Upgraded db to 2018.2")
        else:
            session.flash = T('Already up to date')

        if version < 2018.3:
            print version
            upgrade_to_20183()
            session.flash = T("Upgraded db to 2018.3")
        else:
            session.flash = T('Already up to date')

        if version < 2018.4:
            print version
            upgrade_to_20184()
            session.flash = T("Upgraded db to 2018.4")
        else:
            session.flash = T('Already up to date')

        if version < 2018.5:
            print version
            upgrade_to_20185()
            session.flash = T("Upgraded db to 2018.5")
        else:
            session.flash = T('Already up to date')

        if version < 2018.6:
            print version
            upgrade_to_20186()
            session.flash = T("Upgraded db to 2018.6")
        else:
            session.flash = T('Already up to date')

        if version < 2018.7:
            print version
            upgrade_to_20187()
            session.flash = T("Upgraded db to 2018.7")
        else:
            session.flash = T('Already up to date')

        if version < 2018.8:
            print version
            upgrade_to_20188()
            session.flash = T("Upgraded db to 2018.8")
        else:
            session.flash = T('Already up to date')

        if version < 2018.81:
            print version
            upgrade_to_201881()
            session.flash = T("Upgraded db to 2018.81")
        else:
            session.flash = T('Already up to date')

        if version < 2018.82:
            print version
            upgrade_to_201882()
            session.flash = T("Upgraded db to 2018.82")
        else:
            session.flash = T('Already up to date')

        if version < 2018.83:
            print version
            upgrade_to_201883()
            session.flash = T("Upgraded db to 2018.83")
        else:
            session.flash = T('Already up to date')

        # always renew permissions for admin group after update
        set_permissions_for_admin_group()

    set_version()

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')

    # Back to square one
    to_login()


def upgrade_to_20181():
    """
        Upgrade operations to 2018.1
    """
    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')

    ##
    # Set sorting order for subscriptions
    ##
    query = (db.school_subscriptions.SortOrder == None)
    db(query).update(SortOrder = 0)

    ##
    # Create default subscription group, add all subscriptions to it and give the group full permissions for each class
    # to maintain similar behaviour compared to before the update
    ##

    # Subscriptions
    ssgID = db.school_subscriptions_groups.insert(
        Name = 'All subscriptions',
        Description = 'All subscriptions',
    )

    query = (db.school_subscriptions.Archived == False)
    rows = db(query).select(db.school_subscriptions.ALL)
    for row in rows:
        db.school_subscriptions_groups_subscriptions.insert(
            school_subscriptions_id = row.id,
            school_subscriptions_groups_id = ssgID
        )

    # Class cards
    scgID = db.school_classcards_groups.insert(
        Name = 'All class cards',
        Description = 'All class cards'
    )

    query = (db.school_classcards.Archived == False)
    rows = db(query).select(db.school_classcards.ALL)
    for row in rows:
        db.school_classcards_groups_classcards.insert(
            school_classcards_id = row.id,
            school_classcards_groups_id = scgID
        )

    # Link subscription & class card groups to classes and give permissions
    rows = db(db.classes).select(db.classes.ALL)
    for row in rows:
        db.classes_school_subscriptions_groups.insert(
            classes_id = row.id,
            school_subscriptions_groups_id = ssgID,
            Enroll = True,
            ShopBook = True,
            Attend = True
        )

        db.classes_school_classcards_groups.insert(
            classes_id = row.id,
            school_classcards_groups_id = scgID,
            Enroll = True,
            ShopBook = True,
            Attend = True
        )

    ##
    # set Booking status to attending for all historical data in classes_attendance
    ##
    query = (db.classes_attendance.BookingStatus == None)
    db(query).update(BookingStatus='attending')
    # TODO: repeat the 2 lines above for all coming upgrades


def upgrade_to_20182():
    """
        Upgrade operations to 2018.2
    """
    ##
    # Set archived customers to deleted
    ##
    query = (db.auth_user.archived == True)
    db(query).update(trashed = True)

    ##
    # Set archived for all users to False
    ##
    db(db.auth_user).update(archived = False)

    ##
    # Migrate links to invoices
    ##
    query = (db.invoices)
    rows = db(query).select(db.invoices.ALL)
    for row in rows:
        iID = row.id
        db.invoices_customers.insert(
            invoices_id = iID,
            auth_customer_id = row.auth_customer_id
        )

        if row.customers_subscriptions_id:
            db.invoices_customers_subscriptions.insert(
                invoices_id = iID,
                customers_subscriptions_id = row.customers_subscriptions_id
            )

    db(query).update(auth_customer_id = None,
                     customers_subscriptions_id = None)

    ##
    # Set default values for createdOn fields
    ##
    # auth_user
    now = datetime.datetime.now()
    query = (db.auth_user.created_on == None)
    db(query).update(created_on = now)

    # workshops_products_customers
    query = (db.workshops_products_customers.CreatedOn == None)
    db(query).update(CreatedOn = now)

    ##
    # Clean up old tables
    ##
    tables = [
        'paymentsummary',
        'overduepayments',
        'customers_payments',
        'workshops_messages',
        'workshops_products_messages',
        'customers_subscriptions_exceeded'
    ]

    for table in tables:
        try:
            db.executesql('''DROP TABLE '{table'}'''.format(table=table))
        except:
            pass

    ##
    # Remove email from merges customers
    ##
    query = (db.auth_user.merged_into != None)
    db(query).update(email=None)

    ##
    # set Booking status to attending for all historical data in classes_attendance
    ##
    query = (db.classes_attendance.BookingStatus == None)
    db(query).update(BookingStatus='attending')

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_20183():
    """
        Upgrade operations to 2018.3
    """
    ##
    # Set invoice customer data
    ##
    query = (db.invoices_customers.id > 0)

    rows = db(query).select(db.invoices_customers.ALL)
    for row in rows:
        invoice = Invoice(row.invoices_id)
        invoice.set_customer_info(row.auth_customer_id)

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_20184():
    """
        Upgrade operations to 2018.4
    """
    ##
    # Set default value for db.classes.AllowShopTrial
    ##
    query = (db.classes.AllowShopTrial == None)
    db(query).update(AllowShopTrial = False)

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_20185():
    """
        Upgrade operations to 2018.5
    """
    ##
    # Set default group for teacher credit invoices
    ##
    db.invoices_groups_product_types.insert(
        ProductType='teacher_payments',
        invoices_groups_id=100
    )

    ##
    # Set current global default values as group terms & footer
    ##
    footer = get_sys_property('invoices_default_footer')
    terms = get_sys_property('invoices_default_terms')

    query = (db.invoices_groups.id > 0)
    db(query).update(Footer=footer, Terms=terms)

    ##
    # Set batch type for all current payment batches
    ##
    query = (db.payment_batches.payment_categories_id == None)
    db(query).update(BatchTypeDescription = 'invoices')

    query = (db.payment_batches.payment_categories_id != None)
    db(query).update(BatchTypeDescription='category')

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_20186():
    """
        Upgrade operations to 2018.6
    """
    ##
    # Membership upgrade operations
    ##
    db.invoices_groups_product_types.insert(
        ProductType = 'membership',
        invoices_groups_id = 100
    )

    query = (db.school_subscriptions.MembershipRequired == None)
    db(query).update(MembershipRequired = False)

    query = (db.school_classcards.MembershipRequired == None)
    db(query).update(MembershipRequired = False)


    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_20187():
    """
        Upgrade operations to 2018.7
    """
    ##
    # Delete duplicate entries in invoices_customers
    ##
    db.executesql("""
    DELETE `a`
    FROM
    `invoices_customers` AS `a`,
    `invoices_customers` AS `b`
    WHERE
    -- IMPORTANT: Ensures one version remains
    -- Change "ID" to your unique column's name
    `a`.`id` < `b`.`id`

    -- Any duplicates you want to check for
    AND `a`.`invoices_id` <=> `b`.`invoices_id`
    AND `a`.`auth_customer_id` <=> `b`.`auth_customer_id`
    """)

    ##
    # Migrate customers_orders_items and invoices_items field to float
    ##
    db.executesql("""ALTER TABLE invoices_items MODIFY Quantity float;""")
    db.executesql("""ALTER TABLE customers_orders_items MODIFY Quantity float;""")

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_20188():
    """
        Upgrade operations to 2018.8
    """
    ##
    # Run this again
    ##
    upgrade_to_20187()

    ##
    # Insert notification for order created
    ##
    from openstudio.os_setup import OsSetup
    setup = OsSetup()
    setup._setup_sys_notifications()

    ##
    # clear cache
    ##
    cache.ram.clear(regex='.*')


def upgrade_to_201881():
    """
        Upgrade operations to 2018.81
    """
    from openstudio.os_customer import Customer

    ##
    # Link enrollments to subscriptions, where possible.
    ##

    # List all active enrollments
    query = ((db.classes_reservation.Enddate >= TODAY_LOCAL) |
             (db.classes_reservation.Enddate == None)) & \
            (db.classes_reservation.ResType == 'recurring')
    rows = db(query).select(db.classes_reservation.ALL)
    for row in rows:
        customer = Customer(row.auth_customer_id)
        # Check if customer has subscriptions today
        subscriptions = customer.get_subscriptions_on_date(TODAY_LOCAL)
        # If 1: link
        # Else pass; 0 - nothing to link & 2 - no way to be certain which one
        if subscriptions and len(subscriptions) == 1:
            row.customers_subscriptions_id = subscriptions.first().customers_subscriptions.id
            row.update_record()


    # set CustomerMembership field for db.classes_attendance
    query = (db.classes_attendance.CustomerMembership == None)
    db(query).update(CustomerMembership = False)

    ##
    # Migrate teachers_payment_fixed_rate_travel to
    # teachers_payment_travel
    ##
    define_teachers_payment_fixed_rate_travel()

    rows = db(db.teachers_payment_fixed_rate_travel).select(
        db.teachers_payment_fixed_rate_travel.ALL
    )

    for row in rows:
        db.teachers_payment_travel.insert(
            auth_teacher_id = row.auth_teacher_id,
            school_locations_id = row.school_locations_id,
            TravelAllowance = row.TravelAllowance,
            tax_rates_id = row.tax_rates_id
        )

    ##
    # Set fixed rate as default payment system
    ##
    from openstudio.os_setup import OsSetup
    setup = OsSetup()
    setup._setup_teachers_payment_rate_type()


def upgrade_to_201882():
    """
        Upgrade operations to 2018.82
    """
    ##
    # Set default payment method for subscriptions in shop
    # This is a new setting in this release
    ##
    from openstudio.os_setup import OsSetup
    setup = OsSetup()
    setup._setup_shop_subscriptions_payment_method()

    ##
    # Migrate MandateSignatureDate field from customers_payment_info
    # to customers_payment_info_mandates table
    ##
    query = (db.customers_payment_info.MandateSignatureDate != None)
    rows = db(query).select(db.customers_payment_info.ALL)

    for row in rows:
        db.customers_payment_info_mandates.insert(
            customers_payment_info_id = row.id,
            MandateReference = unicode(row.auth_customer_id),
            MandateSignatureDate = row.MandateSignatureDate
        )

    ##
    # Migrate email templates from sys_properties to sys_email_templates
    ##
    row = db.sys_properties(Property='email_template_order_received')
    db.sys_email_templates.insert(
        Name='order_received',
        Title=T('Order received'),
        TemplateContent=row.PropertyValue
    )
    row = db.sys_properties(Property='email_template_order_delivered')
    db.sys_email_templates.insert(
        Name='order_delivered',
        Title=T('Order delivered'),
        TemplateContent=row.PropertyValue
    )
    row = db.sys_properties(Property='email_template_payment_recurring_failed')
    db.sys_email_templates.insert(
        Name='payment_recurring_failed',
        Title=T('Recurring payment failed'),
        TemplateContent=row.PropertyValue
    )
    row = db.sys_properties(Property='email_template_sys_footer')
    db.sys_email_templates.insert(
        Name='sys_email_footer',
        Title=T('System email footer'),
        TemplateContent=row.PropertyValue
    )
    row = db.sys_properties(Property='email_template_sys_reset_password')
    db.sys_email_templates.insert(
        Name='sys_reset_password',
        Title=T('System reset password'),
        TemplateContent=row.PropertyValue
    )
    row = db.sys_properties(Property='email_template_sys_verify_email')
    db.sys_email_templates.insert(
        Name='sys_verify_email',
        Title=T('System verify email'),
        TemplateContent=row.PropertyValue
    )


def upgrade_to_201883():
    """
        Upgrade operations to 2018.83
    """
    ###
    # Enable AutoResetPrefixYear for invoice groups by default.
    ###
    query = (db.invoices_groups.AutoResetPrefixYear == None)
    db(query).update(AutoResetPrefixYear = True)
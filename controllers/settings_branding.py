# -*- coding: utf-8 -*-
"""
    This file holds the settings for branding
"""

def branding_get_menu(page):
    """
        Menu for system settings pages
    """
    pages = [['logos',
              T('Logos'),
              URL('logos')],
             ['default_templates',
              T('Default templates'),
              URL('default_templates')]
             ]

    return os_gui.get_submenu(pages, page, horizontal=True, htype='tabs')



@auth.requires(auth.has_membership(group_id='Admins') or
               auth.has_permission('read', 'settings'))
def logos():
    """
        Change OpenStudio branding for
        - back-end
        - self check-in
        - login screen
    """
    response.title = T('Settings')
    response.subtitle = T('Branding')
    response.view = 'general/tabs_menu.html'

    content = DIV(DIV(logos_get_logo('branding_logo_login'),
                      logos_get_logo('branding_logo_header'),
                      logos_get_logo('branding_logo_invoices'),
                      _class='col-md-12'),
                  DIV(logos_get_logo('branding_logo_selfcheckin'),
                      _class='col-md-12'),
                  _class='row',
                  _id='settings_branding_logos')

    menu = branding_get_menu(request.function)

    return dict(content=content,
                menu=menu)


@auth.requires(auth.has_membership(group_id='Admins') or
               auth.has_permission('read', 'settings'))
def logos_remove_logo():
    """
        Remove logo
    """
    sfID = request.vars['sfID']

    row = db.sys_files(sfID)

    # first delete the image copied by branding_logos_set_logo
    logo_path = logos_get_logo_path(row)
    import os
    try:
        os.remove(logo_path)
    except OSError:
        # just continue of the file has already been removed
        pass

    # now remove the record from the database
    query = (db.sys_files.id == sfID)
    db(query).delete()

    redirect(URL('logos'))


def logos_get_logo(name):
    """
        Returns form and display of small logo
    """
    name = request.vars['Name'] if request.vars['Name'] else name
    db.sys_files.Name.default = name
    db.sys_files.SysFile.label = ''

    # set image requirements
    db.sys_files.SysFile.requires = IS_IMAGE(extensions=('png'),
        error_message = T("png file required"))

    crud.messages.submit_button = T("Save")
    crud.messages.record_created = T("Saved")
    crud.messages.record_updated = T("Saved")
    crud.settings.create_next = URL()
    crud.settings.update_next = URL()
    crud.settings.update_onaccept = [logos_set_logo]
    crud.settings.create_onaccept = [logos_set_logo]

    row = db.sys_files(Name=name)
    if row:
        form = crud.update(db.sys_files, row.id)
    else:
        form = crud.create(db.sys_files)

    # remove not needed stuff from the upload widgets
    form.elements('span', replace=None)
    form.elements('img', replace=None)
    form.elements('br', replace=None)
    form.elements('tr#delete_record__row', replace=None)

    # add hidden input to specify right form
    hidden = INPUT(_type="hidden",
                   _name="Name",
                   value=name)
    form.insert(0, hidden)

    img = ''
    if row:
        img = IMG(_src=URL('default', 'download', row.SysFile),
                  _class='settings_branding_logo')

    if name == 'branding_logo_login':
        h = H3(T('Login screen logo'))
    elif name == 'branding_logo_header':
        h = H3(T('Shop header logo'))
    elif name == 'branding_logo_invoices':
        h = H3(T('Invoice & email logo'))
    elif name == 'branding_logo_selfcheckin':
        h = H3(T('Self check-in logo'))

    if row:
        form.add_button('Remove', URL('logos_remove_logo',
                                      vars={'sfID' : row.id}))

    return DIV(h, img, form, _class='col-md-4')


def logos_set_logo(form):
    """
        Copies the logos to a specific folder in uploads
    """
    id = form.vars.id
    row = db.sys_files(id)

    path = os.path.join(request.folder, 'uploads')

    filename = row.SysFile
    logo = os.path.join(path, filename)

    logo_dest = logos_get_logo_path(row)

    import shutil

    shutil.copy2(logo, logo_dest)


def logos_get_logo_path(row):
    """
        Returns location of a logo on disk
        Takes row from db.sys_files as argument
    """
    logo_path = os.path.join(request.folder,
                             'static',
                             'plugin_os-branding',
                             'logos',
                             row.Name + '.png')

    return logo_path


@auth.requires(auth.has_membership(group_id='Admins') or
               auth.has_permission('read', 'settings'))
def default_templates():
    """
        Set default templates for emails and workshops (pdf)
    """
    response.title = T("Settings")
    response.subtitle = T("Branding")
    response.view = 'general/tabs_menu.html'

    sprop_t_email = 'branding_default_template_email'
    sprop_t_events = 'branding_default_template_events'
    t_email = get_sys_property(sprop_t_email)
    t_events = get_sys_property(sprop_t_events)

    form = SQLFORM.factory(
        Field('t_email',
              default=t_email,
              requires=IS_IN_SET(default_templates_list_templates('email')),
              label=T('Email template')),
        Field('t_events',
              default=t_events,
              requires=IS_IN_SET(default_templates_list_templates('events')),
              label=T('Events pdf template')),
        submit_button=T("Save"),
        separator=' ',
        formstyle='bootstrap3_stacked'
    )

    form_id = "MainForm"
    form_element = form.element('form')
    form['_id'] = form_id

    elements = form.elements('input, select, textarea')
    for element in elements:
        element['_form'] = form_id

    submit = form.element('input[type=submit]')

    if form.accepts(request.vars, session):
        print 'process template storage'
        # Check email template
        t_email = request.vars['t_email']
        row = db.sys_properties(Property=sprop_t_email)
        if not row:
            db.sys_properties.insert(Property=sprop_t_email,
                                     PropertyValue=t_email)
        else:
            row.PropertyValue = t_email
            row.update_record()

        # Check events template
        t_events = request.vars['t_events']
        row = db.sys_properties(Property=sprop_t_events)
        if not row:
            db.sys_properties.insert(Property=sprop_t_events,
                                     PropertyValue=t_events)
        else:
            row.PropertyValue = t_events
            row.update_record()

        session.flash = T('Saved')
        # Clear cache
        cache_clear_sys_properties()
        # reload so the user sees how the values are stored in the db now
        redirect(URL('default_templates'))

    content = DIV(DIV(form, _class='col-md-6'),
                  _class='row')

    menu = branding_get_menu(request.function)

    return dict(content=content,
                save=submit,
                menu=menu)


def default_templates_list_templates(template_type):
    """
        :param template_type: can be 'email' or 'workshops' for now
        :return: list of files in view/templates/<template_type> folder
    """
    template_types = ['email', 'invoices', 'events']
    if template_type not in template_types:
        return ''

    os_template_dir = os.path.join(
        request.folder,
        'views',
        'templates',
        template_type
    )
    os_templates = [ os.path.join(template_type, i)
                     for i in sorted(os.listdir(os_template_dir))
                     if not i == '.gitignore' ]

    custom_template_dir = os.path.join(
        request.folder,
        'views',
        'templates',
        'custom',
        template_type
    )

    custom_templates = [ os.path.join('custom', template_type, i)
                         for i in sorted(os.listdir(custom_template_dir))
                         if not  i == '.gitignore' ]

    os_templates.extend(custom_templates)

    return os_templates
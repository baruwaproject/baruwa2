# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

import os

production_config = '/home/baruwa/config/production.ini'
temp_dir = '/var/tmp'

os.environ['TMPDIR'] = temp_dir
os.environ['PYTHON_EGG_CACHE'] = temp_dir

if __name__.startswith('_mod_wsgi_'):
    # Set up logging under mod_wsgi
    from paste.script.util.logging_config import fileConfig
    fileConfig(production_config)
    # Load the app!
    from paste.deploy import loadapp
    application = loadapp('config:'+production_config)
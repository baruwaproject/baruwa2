# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

production_config = '/etc/baruwa/production.ini'
temp_dir = '/var/tmp'

import os
os.environ['TMPDIR'] = temp_dir

# Set up logging under mod_wsgi
from paste.script.util.logging_config import fileConfig
fileConfig(production_config)
# Load the app!
from paste.deploy import loadapp
application = loadapp('config:'+production_config)
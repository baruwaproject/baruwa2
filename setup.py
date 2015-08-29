# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages, Extension

required_packages = [
        "Pylons>=1.0",
        "SQLAlchemy>=0.7,<0.8",
        "wtforms",
        "reportlab",
        "python-dateutil<2.0",
        "pyparsing<2.0",
        "IPy",
        "pytz",
        "Pillow",
        "Mako",
        "Babel",
        "lxml",
        "pyzmail",
        "cssutils",
        "celery",
        "py-bcrypt",
        "cracklib",
        "psutil",
        "pyrad",
        "arrow",
        "python-cdb",
        "python-ldap",
        "psycopg2",
        "mysql-python",
        "eventlet",
        "pylibmc",
        "M2Crypto",
        "sqlparse",
        "tinycss",
        "oauthlib",
        "marrow.mailer",
        "repoze.what",
        "repoze.what-pylons",
        "repoze.what.plugins.config",
        "repoze.what.plugins.sql",
        "repoze.who>=1.0,<=1.99",
        "repoze.who.plugins.sa",
        "repoze.who.plugins.ldap",
        "repoze.who-friendlyform",
]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='baruwa',
    version='2.0.9',
    description='Ajax enabled MailScanner web frontend',
    long_description=read('README.rst'),
    author='Andrew Colin Kissa',
    author_email='andrew@topdog.za.net',
    url='http://www.baruwa.com',
    install_requires=required_packages,
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    scripts=['bin/import-mbox.py',
            'bin/eximqf2mbox.py',
            'bin/test-smtpauth.py',
            'bin/recon-mbox.py'],
    test_suite='nose.collector',
    package_data={'baruwa': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors={'baruwa': [
           ('**.py', 'python', None),
           ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
           ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
           ('public/css/**', 'ignore', None),
           ('public/imgs/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = baruwa.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller

    [paste.global_paster_command]
    update-sa-rules = baruwa.commands.updatesarules:UpdateSaRules
    update-queue-stats = baruwa.commands.queuestats:QueueStats
    celeryd = baruwa.lib.mq.commands:CeleryDaemonCommand
    camqadm = baruwa.lib.mq.commands:CAMQPAdminCommand
    celerybeat = baruwa.lib.mq.commands:CeleryBeatCommand
    celeryev = baruwa.lib.mq.commands:CeleryEventCommand
    send-pdf-reports = baruwa.commands.pdfreportsng:SendPdfReports
    send-pdf-reports-ng = baruwa.commands.pdfreportsng:SendPdfReports
    send-quarantine-reports = baruwa.commands.quarantinereportsng:QuarantineReports
    send-quarantine-reports-ng = baruwa.commands.quarantinereportsng:QuarantineReports
    prune-database = baruwa.commands.dbclean:DBCleanCommand
    prune-quarantine = baruwa.commands.cleanquarantine:CleanQuarantineCommand
    update-delta-index = baruwa.commands.updatedelta:UpdateDeltaIndex
    create-admin-user = baruwa.commands.createadmin:CreateAdminUser
    change-user-password = baruwa.commands.changepassword:ChangePassword
    check-user-password = baruwa.commands.checkpassword:CheckPassword
    send-top-spammer-list = baruwa.commands.topspammers:TopSpammersCommand
    send-whitelist-data = baruwa.commands.buildwhitelist:BuildWhiteList
    update-rulesets = baruwa.commands.updaterulesets:UpdateRulesetsCommand
    update-mta-lookup = baruwa.commands.createcdb:CreateCDBCommand
    dump-mta-lookup-file = baruwa.commands.cdbdump:DumpCDBFileCommand
    routes = pylons.commands:RoutesCommand
    shell = pylons.commands:ShellCommand
    """,
    classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Web Environment',
            'Framework :: Pylons',
            'Intended Audience :: System Administrators',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Telecommunications Industry',
            'Intended Audience :: Customer Service',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Natural Language :: English',
            'Natural Language :: Bulgarian',
            'Natural Language :: Catalan',
            'Natural Language :: Chinese (Simplified)',
            'Natural Language :: Czech',
            'Natural Language :: Danish',
            'Natural Language :: Dutch',
            'Natural Language :: French',
            'Natural Language :: German',
            'Natural Language :: Greek',
            'Natural Language :: Hebrew',
            'Natural Language :: Hindi',
            'Natural Language :: Indonesian',
            'Natural Language :: Italian',
            'Natural Language :: Japanese',
            'Natural Language :: Norwegian',
            'Natural Language :: Polish',
            'Natural Language :: Portuguese',
            'Natural Language :: Romanian',
            'Natural Language :: Russian',
            'Natural Language :: Spanish',
            'Natural Language :: Swedish',
            'Natural Language :: Thai',
            'Natural Language :: Turkish',
            'Natural Language :: Ukranian',
            'Natural Language :: Vietnamese',
            'Operating System :: POSIX :: Linux',
            'Operating System :: POSIX :: BSD',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Communications :: Email :: Filters',
            'Topic :: System :: Monitoring',
            'Topic :: Multimedia :: Graphics :: Presentation',
            'Topic :: System :: Systems Administration', ],
)

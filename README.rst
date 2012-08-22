
Installation and Setup
======================

Install ``baruwa``::

    git clone git://github.com/akissa/baruwa2.git
    cd baruwa2
    python setup.py install

Make a config file as follows::

    paster make-config baruwa config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Run the paste server

	paster serve config.ini

You can then deploy the application using any WSGI server.


Support
=======

Subscribe to the Baruwa `mailing list`_

.. _`mailing list`: http://lists.baruwa.org/mailman/listinfo/baruwa

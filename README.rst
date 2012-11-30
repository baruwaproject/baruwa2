
Installation and Setup
======================

Install ``baruwa``::

    git clone git://github.com/akissa/baruwa2.git
    cd baruwa2
    ./extras/scripts/build.sh full
    pip install -r requirements.txt
    pip install sdist/baruwa-2.0.0.tar.bz2

Make a config file as follows::

    paster make-config baruwa config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Run the paste server::

	paster serve config.ini

You can then deploy the application using any WSGI server.


Detailed documentation
======================

Detailed documentation is available in the ``docs`` folder. To generate
HTML run::

	cd docs && make html

Support
=======

Subscribe to the Baruwa `mailing list`_

.. _`mailing list`: http://lists.baruwa.org/mailman/listinfo/baruwa

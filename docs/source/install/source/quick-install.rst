.. _install_overview:

===========================
Quick Installation Overview
===========================

If you're already familiar with installing Pylons apps, here's a
ten-step run-down of how to install Baruwa.

If you're not already familiar with the process, head to the main
:ref:`source_install` page for a more detailed description of the process.

1. Create and activate a new ``virtualenv``.
2. Run ``pip install -r requirements.txt`` to install Baruwa and its dependencies.
3. For production, run ``paster make-config baruwa production.ini``
   and to create a unique ``production.ini`` config. On development
   machines there's already a ``development.ini`` file for you to use.
4. Install the sphinx api which is not on PyPi run
   ``curl https://sphinxsearch.googlecode.com/svn/trunk/api/sphinxapi.py -o \``
   ``path/to/virtualenv/lib/python2.6/site-packages/sphinxapi.py``
5. :ref:`apply_patches`
6. Configure your database credentials in the ini config file.
7. Run ``paster setup-app path/to/your/production.ini`` to set up the database
   tables and create the admin user.
8. Start the celeryd daemon ``paster celeryd path/to/your/production.ini``
9. Run ``paster serve path/to/your/production.ini`` and test it out!
10. Open your browser and point to http://127.0.0.1:8000

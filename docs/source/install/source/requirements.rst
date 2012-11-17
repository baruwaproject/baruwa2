.. _source_requirements:

================================
Source installation requirements
================================
.. include:: ../../includes/source-note.rst

The following preliminary packages are required to install Baruwa from source

  * gcc
  * git
  * subversion
  * wget
  * patch

Step 1a: Preliminary Requirements for CentOS/RHEL/SL
----------------------------------------------------

Depending on how you configured your CentOS Distro at install time you may need
to install extra packages:

EPEL Requirements 

**You need to install this repo in order to access certain packages that are
required by Baruwa.**
::

	rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm


Run the following command to install the required packages.

.. sourcecode:: bash

   # install the necessary tools compiling
   yum install gcc git gcc-c++ svn wget patch -y

System Libraries

You will also need to make sure certain system libraries are installed.
Running the following command will install any libraries that are missing.

.. sourcecode:: bash

    # install the necessary libraries for compiling
    yum install install libxml2-devel libxslt-devel Cython postgresql-devel \
	freetype-devel libjpeg-devel zlib-devel openldap-devel openssl-devel swig \
	cracklib-devel GeoIP-devel -y

**NOTE: You need to install libmemcached from source as the version shipped in
the repositories is too old, You need atleast version 0.32 or newer**

Python Requirements

Baruwa supports Python 2.x versions 2.6 and up. CentOS/RHEL 6.x ships with
Python 2.6, so you should be OK with the system default as a base for your
operations.

Now you can proceed with :ref:`installing_setuptools`.

Step 1b: Preliminary Requirements for Debian/Ubuntu
---------------------------------------------------

You have to install the required tools and python libraries.

.. sourcecode:: bash

   # install the necessary tools compiling
   sudo apt-get install gcc g++ git subversion wget patch

   # install the necessary libraries for compiling
   sudo apt-get install libjpeg-dev libxml2-dev libxslt1-dev cython \
	postgresql-server-dev-all libfreetype6-dev libldap2-dev libssl-dev \
	swig2.0 libcrack2-dev libmemcached-dev libgeoip-dev -y

Now you can proceed with :ref:`installing_setuptools`.

Step 1c: Preliminary Requirements for FreeBSD
---------------------------------------------

TODO

Now you can proceed with installing Setuptools and Virtualenv as below.

.. _installing_setuptools:

Step 2: Installing Setuptools
-----------------------------

The Python setuptools package is what we'll use to automate the rest of the
installation of Python packages.

If you're using a package manager to handle your Python installation, you can
use your package manager to install setuptools (0.6c9 or higher), like so:

CentOS/RHEL/SL::

   yum install python-setuptools -y

Debian/Ubuntu::

   sudo apt-get install python-setuptools -y

FreeBSD::

   pkg_add py-setuptools

Others, in the main Baruwa package directory, there is an install script
to help get setuptools installed for you.

.. sourcecode:: bash

   # Run the setuptools install script in your Baruwa directory:
   sudo python ez_setup.py

Step 3: Installing Virtualenv
-----------------------------

First, check if you have virtualenv installed:

.. sourcecode:: bash

   # Check if you have virtualenv installed:
   python -c 'import virtualenv'

If you get no error, virtualenv is already installed. You can skip the rest
of this step and proceed to :ref:`source_install`;

If you get an error like the following, you'll need to install virtualenv:

.. sourcecode:: text

   Traceback (most recent call last):
     File "<string>", line 1, in <module>
   ImportError: No module named virtualenv

If you're using a package manager to handle your Python installation, you can
use your package manager to install virtualenv, like so:

CentOS/RHEL/SL::

   yum install python-virtualenv -y

Debian/Ubuntu::

   sudo apt-get install python-virtualenv -y

FreeBSD::

   cd /usr/ports/devel/py-virtualenv && make install clean

Others, you can get setuptools to automatically install virtualenv for you:

.. sourcecode:: bash

   # Install virtualenv via setuptools:
   sudo easy_install virtualenv

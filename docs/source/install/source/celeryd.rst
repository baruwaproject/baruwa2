
==================
Celeryd Deployment
==================


CentOS/RHEL/SL
--------------

Create a user to run celeryd as, then give them ownership of the directories
Baruwa writes to::

	getent group baruwa >/dev/null || groupadd -r baruwa
	getent passwd baruwa >/dev/null || \
	    useradd -r -g baruwa -d /var/lib/baruwa \
	    -s /sbin/nologin -c "Baruwa user" baruwa
	chown baruwa.baruwa -R /var/lib/baruwa \
		/var/run/baruwa /var/log/baruwa

A CentOS init file is provided in the source tar ball. Extract the init file
from the tar ball and install to the init directory ``/etc/init.d`` ::

	tar xjvf baruwa-2.0.0.tar.bz2 --strip-components=5 \
		baruwa-2.0.0/extras/scripts/init/centos/baruwa.init
	mv baruwa.init /etc/init.d/baruwa

Create a configuration file for celeryd in ``/etc/sysconfig/baruwa`` with the
following contents:

.. sourcecode:: bash

	CELERYD_CHDIR="/home/baruwa"
	CELERYD="$CELERYD_CHDIR/px/bin/paster celeryd /etc/baruwa/production.ini"
	CELERYD_LOG_LEVEL="INFO"
	CELERYD_LOG_FILE="/var/log/baruwa/celeryd.log"
	CELERYD_PID_FILE="/var/run/baruwa/celeryd.pid"
	CELERYD_USER="baruwa"
	CELERYD_GROUP="baruwa"

::

	cat > /etc/sysconfig/baruwa << 'EOF'
	CELERYD_CHDIR="/home/baruwa"
	CELERYD="$CELERYD_CHDIR/px/bin/paster celeryd /etc/baruwa/production.ini"
	CELERYD_LOG_LEVEL="INFO"
	CELERYD_LOG_FILE="/var/log/baruwa/celeryd.log"
	CELERYD_PID_FILE="/var/run/baruwa/celeryd.pid"
	CELERYD_USER="baruwa"
	CELERYD_GROUP="baruwa"
	EOF

Enable and start the service::

	chmod +x /etc/init.d/baruwa
	chkconfig --level 3 baruwa on
	service baruwa start

Debian/Ubuntu
-------------

Create a user to run celeryd as, then give them ownership of the directories
Baruwa writes to::

	getent group baruwa >/dev/null || addgroup --system baruwa
	getent passwd baruwa >/dev/null || adduser --system --ingroup \
		baruwa --home /var/lib/baruwa \
        --no-create-home --gecos "Baruwa user" \
        --disabled-login baruwa
	chown baruwa.baruwa -R /var/lib/baruwa \
		/var/run/baruwa /var/log/baruwa

A Debian init file is provided in the source tar ball. Extract it and install
to the init directory ``/etc/init.d`` ::

	tar xjvf baruwa-2.0.0.tar.bz2 --strip-components=5 \
		baruwa-2.0.0/extras/scripts/init/debian/baruwa.init
	sudo mv baruwa.init /etc/init.d/baruwa
	sudo chmod +x /etc/init.d/baruwa

Create a configuration file for celeryd in ``/etc/default/baruwa`` with the following
contents:

.. sourcecode:: bash

	CELERYD_CHDIR="/home/baruwa"
	CELERYD="$CELERYD_CHDIR/px/bin/paster celeryd /etc/baruwa/production.ini"
	CELERYD_LOG_LEVEL="INFO"
	CELERYD_LOG_FILE="/var/log/baruwa/celeryd.log"
	CELERYD_PID_FILE="/var/run/baruwa/celeryd.pid"
	CELERYD_USER="baruwa"
	CELERYD_GROUP="baruwa"

::

	cat > /etc/default/baruwa << 'EOF'
	CELERYD_CHDIR="/home/baruwa"
	CELERYD="$CELERYD_CHDIR/px/bin/paster celeryd /etc/baruwa/production.ini"
	CELERYD_LOG_LEVEL="INFO"
	CELERYD_LOG_FILE="/var/log/baruwa/celeryd.log"
	CELERYD_PID_FILE="/var/run/baruwa/celeryd.pid"
	CELERYD_USER="baruwa"
	CELERYD_GROUP="baruwa"
	EOF

Enable and start the service::

	update-rc.d baruwa defaults
	sudo service baruwa start

FreeBSD
-------

TODO
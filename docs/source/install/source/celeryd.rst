
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

Download the CentOS init file from the celery repository on github::

	wget https://raw.github.com/celery/celery/3.0/extra/centos/celeryd.init \
		-O /etc/init.d/baruwa

Create a configuration file for celeryd in ``/etc/sysconfig/baruwa`` with the
following contents:

.. sourcecode:: bash

	CELERYD_CHDIR="/home/baruwa"
	ENV_PYTHON="$CELERYD_CHDIR/px/bin/python"
	CELERYD_MULTI="$CELERYD_CHDIR/px/bin/paster celeryd /etc/baruwa/production.ini"
	CELERYD_LOG_LEVEL="INFO"
	CELERYD_LOG_FILE="/var/log/baruwa/celeryd.log"
	CELERYD_PID_FILE="/var/run/baruwa/celeryd.pid"
	CELERYD_USER="baruwa"
	CELERYD_GROUP="baruwa"

::

	cat > /etc/sysconfig/baruwa << 'EOF'
	CELERYD_CHDIR="/home/baruwa"
	ENV_PYTHON="$CELERYD_CHDIR/px/bin/python"
	CELERYD_MULTI="$CELERYD_CHDIR/px/bin/paster celeryd /etc/baruwa/production.ini"
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

Download the generic init file from the celery repository on github::

	sudo wget https://raw.github.com/celery/celery/3.0/extra/generic-init.d/celeryd \
		-O /etc/init.d/baruwa

Create a configuration file for celeryd in ``/etc/default/celeryd`` with the following
contents:

.. sourcecode:: bash

	CELERYD_NODES="w1"
	CELERYD_CHDIR="/home/baruwa"
	ENV_PYTHON="$CELERYD_CHDIR/px/bin/python"
	CELERYD_MULTI="$ENV_PYTHON paster celeryd /etc/baruwa/production.ini"
	CELERYCTL="$ENV_PYTHON paster celeryctl /etc/baruwa/production.ini"
	CELERYD_OPTS="--time-limit=300 --concurrency=8"
	CELERY_CONFIG_MODULE="baruwa.lib.mq.loader.PylonsLoader"
	CELERYD_LOG_FILE="/var/log/baruwa/celeryd.log"
	CELERYD_PID_FILE="/var/run/baruwa/celeryd.pid"
	CELERYD_USER="baruwa"
	CELERYD_GROUP="baruwa"

::

	cat > /etc/default/celeryd << 'EOF'
	CELERYD_NODES="w1"
	CELERYD_CHDIR="/home/baruwa"
	ENV_PYTHON="$CELERYD_CHDIR/px/bin/python"
	CELERYD_MULTI="$ENV_PYTHON paster celeryd /etc/baruwa/production.ini"
	CELERYCTL="$ENV_PYTHON paster celeryctl /etc/baruwa/production.ini"
	CELERYD_OPTS="--time-limit=300 --concurrency=8"
	CELERY_CONFIG_MODULE="baruwa.lib.mq.loader.PylonsLoader"
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

============
Known Issues
============

.. _m2crypto_symbol:

ImportError: M2Crypto/__m2crypto.so: undefined symbol: SSLv2_method
-------------------------------------------------------------------

If you run across is issue (Ubuntu/Debian) you need to apply the patch
from Debian, then install M2Crypto manually.

The patch is included in the Baruwa patches directory, extract, apply
and build and install::

	tar xjvf baruwa-2.0.0.tar.bz2 --strip-components=4 \
		baruwa-2.0.0/extras/patches/0002-Disable-SSLv2_method-when-disabled-in-OpenSSL-iself.patch
	wget wget http://pypi.python.org/packages/source/M/M2Crypto/M2Crypto-0.21.1.tar.gz
	tar xzvf M2Crypto-0.21.1.tar.gz
	cd M2Crypto-0.21.1/
	patch -p1 -i ../0002-Disable-SSLv2_method-when-disabled-in-OpenSSL-iself.patch
	python setup.py install
	cd -

.. _eventlet_subprocess:

TypeError: wait() got an unexpected keyword argument 'timeout'
--------------------------------------------------------------

You need to apply a patch to eventlet to fix this issue::

	cd /home/baruwa/px/lib/python2.6/site-packages/
	patch -p1 -i /home/baruwa/patches/subprocess_timeout.patch
	cd /home/baruwa




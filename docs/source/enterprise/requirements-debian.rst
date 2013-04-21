Step 1: Installation requirements
=================================

You need a valid Baruwa enterprise subscription, which provides you with
a server entitlement as well as an activation key to activate the entitlement.

Baruwa uses packages from only the main and universe repos, you should disable
the other repos such as the multiverse and backports repos.

Set the hostname
----------------

The Debian/Ubuntu installer does not set the full host name, you need to
manually set the full hostname by running the following commands. Be sure
to change ``host.example.com`` to your actual hostname::

	cat > /etc/hostname << 'EOF'
	host.example.com
	EOF
	hostname host.example.com

Install Spacewalk client packages
---------------------------------

Baruwa Enterprise Edition entitlements are managed by the Baruwa Network.
The Baruwa Network uses the Spacewalk server to manage entitlements.
In order to access the Baruwa Enterprise Edition repository you need to
install the Spacewalk client tools::

	apt-get install apt-transport-spacewalk rhnsd

Install Baruwa signing keys
---------------------------

The packages in the Baruwa Ubuntu enterprise repository are cryptographically
signed using GPG keys. The package containing these GPG keys needs to be manually
installed before continuing to the next step::

	curl -O https://www.baruwa.com/downloads/baruwa-enterprise-keyring_0.2-1_all.deb
	dpkg -i baruwa-enterprise-keyring_0.2-1_all.deb

Activate Entitlement
--------------------

The Baruwa Ubuntu enterprise repository is available to subscribers
only. To install from this repo you need to activate the entitlement
for the server that you are installing.

The server entitlement ``activation key`` is emailed to you when you purchase
a subscription. Use the ``activation key`` to register your server with the
Baruwa Network using the command below::

	rhnreg_ks --serverUrl=https://bn.baruwa.com/XMLRPC --activationkey=<activation-key>

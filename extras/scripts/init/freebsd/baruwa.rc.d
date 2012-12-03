#!/bin/sh

# baruwa Baruwa Celeryd worker daemon
#
# PROVIDE: baruwa
# REQUIRE: DAEMON
# BEFORE: LOGIN
# KEYWORD: shutdown
#
# Add the following line to /etc/rc.conf to enable Baruwa Celeryd
#
#  baruwaceleryd_enable="YES"

. /etc/rc.subr

name=baruwaceleryd
rcvar=baruwaceleryd_enable

load_rc_config $name

# Set some defaults
: ${baruwaceleryd_enable="NO"}
: ${baruwaceleryd_user="baruwa"}

baruwaceleryd_user="baruwa"
baruwaceleryd_dir="/usr/home/baruwa"
baruwaceleryd_server="px/bin/paster"
baruwaceleryd_config="/usr/local/etc/baruwa/production.ini"
baruwaceleryd_log="/var/log/baruwa/celeryd.log"
pidfile="/var/run/baruwa/baruwaceleryd.pid"
baruwaceleryd_args="${baruwaceleryd_config} -f ${baruwaceleryd_log} --pidfile=${pidfile}"

start_cmd="${name}_start"
stop_postcmd="wait_for_pids $rc_pid"

baruwaceleryd_start()
{
    env HOME="${baruwaceleryd_dir}" \
    su -m ${baruwaceleryd_user} -c "${baruwaceleryd_dir}/${baruwaceleryd_server} celeryd ${baruwaceleryd_args} &"
}

run_rc_command "$1"
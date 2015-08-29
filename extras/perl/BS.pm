# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2014  Andrew Colin Kissa <andrew@topdog.za.net>
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
package MailScanner::CustomConfig;

use DBI;
use POSIX;
use strict;
use IO::Socket;
use Time::Local;
use MIME::Parser;
use String::CRC32;
use Sys::Hostname;
use Fcntl ':flock';
use MailScanner::Config;
use Digest::MD5 qw(md5_hex);
use Encode qw(decode is_utf8);
use Storable(qw[freeze thaw retrieve store]);
# use Encoding::FixLatin qw(fix_latin);

our ($debug);

my ( $shutdown, $server,  $WantLintOnly, $errormsg );
my ( $work_dir, $socket,  $pidfile, $sqlite_db );
my ( $conn,     $bconn,   $sphinx, $sth, $bsth, $spth );
my ( $db_user,  $db_pass, $baruwa_dsn );
my ( $sphinx_host, $sphinx_port,  $lock_file, $lock_handle, $restore_dir);
my $hostname = hostname;
my $ConfFile = $MailScanner::ConfigSQL::ConfFile;

$Storable::accept_future_minor = 1;
$work_dir    = MailScanner::Config::QuickPeek( $ConfFile, 'incomingworkdir' );
$socket      = "$work_dir/baruwa.sock";
$pidfile     = "$work_dir/baruwa-bs.pid";
$sqlite_db   = "$work_dir/baruwa2.db";
$lock_file   = "$work_dir/baruwa.lock";
$restore_dir = "$work_dir/restoredb";

$sphinx_host = MailScanner::Config::QuickPeek( $ConfFile, 'sphinxhost' );
$sphinx_port = int( MailScanner::Config::QuickPeek( $ConfFile, 'sphinxport' ) );

$sphinx_host = '127.0.0.1' unless ( defined($sphinx_host) and $sphinx_host );
$sphinx_port = 9306        unless ( defined($sphinx_port) and $sphinx_port );

sub lock {
    open($lock_handle, '>>', $lock_file) or exit;
    flock($lock_handle, LOCK_EX|LOCK_NB) or exit;
}

sub unlock {
    flock($lock_handle, LOCK_UN) or exit;
    close($lock_handle);
    unlink($lock_file) if (-e $lock_file);
}

sub store_record {
    my ($message) = @_;
    eval {
        mkdir $restore_dir, 0700 unless(-e $restore_dir);
        my $md5sum = md5_hex("$$message{messageid}$$message{to_address}");
        store $message, "$restore_dir/$md5sum";
    };
    if ($@) {
        $errormsg = $@;
        $errormsg =~ s/ at .*? line \d+.$//;
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: storage failed: $errormsg");
        print STDERR "BaruwaSQL[$$]: $$message{messageid}: storage failed: $@\n" if $debug;
    }
}

sub read_record {
    my ($filename) = @_;
    my $message = retrieve "$filename";
    return $message;
}

sub create_lock {
    my ($filename) = @_;
    mkdir $restore_dir, 0700 unless(-e $restore_dir);
    open FILE, ">${restore_dir}/${filename}.lock";
    close FILE;
}

sub insert_record {
    my ($message) = @_;
    $sth->execute(
        $$message{messageid},     $$message{actions},
        $$message{clientip},      $$message{date},
        $$message{from_address},  $$message{from_domain},
        $$message{headers},       $$message{hostname},
        $$message{highspam},      $$message{rblspam},
        $$message{saspam},        $$message{spam},
        $$message{nameinfected},  $$message{otherinfected},
        $$message{isquarantined}, $$message{isarchived},
        $$message{sascore},       $$message{scaned},
        $$message{size},          $$message{blacklisted},
        $$message{spamreport},    $$message{whitelisted},
        $$message{subject},       $$message{time},
        $$message{timestamp},     $$message{to_address},
        $$message{to_domain},     $$message{virusinfected},
        $$message{msgfiles}
    );
    my $id = $conn->last_insert_id( undef, undef, "messages", undef );
    return $id;
}

sub index_record {
    my ($message) = @_;
    return unless defined $$message{id};
    eval {
        $spth->execute(
            $$message{id},                  $$message{messageid},
            $$message{subject},             $$message{headers},
            $$message{hostname},            crc32( $$message{from_address} ),
            crc32( $$message{to_address} ), crc32( $$message{from_domain} ),
            crc32( $$message{to_domain} ),  $$message{indexerts},
            $$message{isquarantined}
        );
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: Indexed");
        print STDERR "BaruwaSQL[$$]: $$message{messageid}: Indexed\n" if $debug;
    };
    if ($@) {
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: indexing failed");
        print STDERR "BaruwaSQL[$$]: $$message{messageid}: indexing failed: $@\n" if $debug;
    }
}

sub restore_from_file {
    opendir(DIR, $restore_dir) or return;
    my $count = 0;
    while (defined(my $file = readdir(DIR))) {
        next if $file =~ /^\.\.?$/;
        last if $count >= 25;
        $file =~ m/^([a-zA-Z0-9\._]+)$/;
        $file = $1;
        open(RESTORE, '>>', "$restore_dir/$file") or next;
        flock(RESTORE, LOCK_EX|LOCK_NB) or do {
            close(RESTORE);
            next;
        };
        my $message = retrieve "$restore_dir/$file";
        my $md5sum = md5_hex("$$message{messageid}$$message{to_address}");
        my $lockfile = "${restore_dir}/${md5sum}.lock";
        if (! -e $lockfile) {
            eval {
                insert_record($message);
                MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: restored from file");
                print STDERR "BaruwaSQL[$$]: $$message{messageid}: restored from file\n" if $debug;
            };
            if ($@) {
                $errormsg = $@;
                $errormsg =~ s/ at .*? line \d+.$//;
                MailScanner::Log::InfoLog("BaruwaSQL: Backup file insert Fail: $errormsg\n");
                print STDERR "BaruwaSQL: Backup file insert Fail: $@\n" if $debug;
            } else {
                unlink("$restore_dir/$file") if (-e "$restore_dir/$file");
            }
        } else {
            # locked
            MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: is a stale file");
            print STDERR "BaruwaSQL[$$]: $$message{messageid}: is a stale file\n" if $debug;
            unlink($lockfile) if (-e $lockfile);
        }
        $count++;
        flock(RESTORE, LOCK_UN) or next;
        close(RESTORE);
    }
    closedir(DIR);
}

sub restore_from_backup {
    my $st;
    eval {
        $st = $bconn->prepare("SELECT * FROM tm LIMIT 100");
        $st->execute();
    };
    if ($@) {
        MailScanner::Log::InfoLog("BaruwaSQL: Backup DB recovery Failure");
        print STDERR "BaruwaSQL[$$]: Backup DB recovery Failure: $@\n" if $debug;
        return;
    }

    while ( my $message = $st->fetchrow_hashref ) {
        my $md5sum = md5_hex("$$message{messageid}$$message{to_address}");
        my $lockfile = "${restore_dir}/${md5sum}.lock";
        if (! -e $lockfile) {
            eval {
                insert_record($message);
                MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: restored from backup");
                print STDERR "BaruwaSQL[$$]: $$message{messageid}: restored from backup\n" if $debug;
            };
            if ($@) {
                MailScanner::Log::InfoLog("BaruwaSQL: Backup DB insert Fail");
                print STDERR "BaruwaSQL: Backup DB insert Fail: $@\n" if $debug;
            } else {
                eval {
                    my @bind_values = ( $$message{messageid}, $$message{to_address} );
                    $bconn->do( "DELETE FROM tm WHERE messageid=? AND to_address=?", undef, @bind_values );
                };
                if ($@) {
                    MailScanner::Log::WarnLog("BaruwaSQL: Backup DB clean temp Fail");
                    print STDERR "BaruwaSQL[$$]: Backup DB clean temp Fail: $@\n" if $debug;
                    create_lock($md5sum);
                }
            }
        } else {
            # lock file found
            MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: is a stale record");
            print STDERR "BaruwaSQL[$$]: $$message{messageid}: is a stale record\n" if $debug;
            eval {
                my @bind_values = ( $$message{messageid}, $$message{to_address} );
                $bconn->do( "DELETE FROM tm WHERE messageid=? AND to_address=?", undef, @bind_values );
            };
            if (!$@) {
                unlink($lockfile) if (-e $lockfile);
            }
        }
    }
}

sub create_sqlite_tables {
    $bconn->do(
        "CREATE TABLE IF NOT EXISTS tm (
            timestamp TEXT NOT NULL,
            messageid TEXT NOT NULL,
            size INT NOT NULL,
            from_address TEXT NOT NULL,
            from_domain TEXT NOT NULL,
            to_address TEXT NOT NULL,
            to_domain TEXT NOT NULL,
            subject TEXT NOT NULL,
            clientip TEXT NOT NULL,
            spam INT NOT NULL,
            highspam INT NOT NULL,
            saspam INT NOT NULL,
            rblspam INT NOT NULL,
            whitelisted INT NOT NULL,
            blacklisted INT NOT NULL,
            sascore REAL NOT NULL,
            spamreport TEXT NOT NULL,
            virusinfected TEXT NOT NULL,
            nameinfected INT NOT NULL,
            otherinfected INT NOT NULL,
            hostname TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            headers TEXT NOT NULL,
            actions TEXT NOT NULL,
            isquarantined INT NOT NULL,
            isarchived INT NOT NULL,
            scaned INT NOT NULL,
            msgfiles TEXT NOT NULL
        )"
    );
}


sub create_backupdb_tables {
    eval {
        $bconn->do("PRAGMA default_synchronous = OFF");
        # check if table tm exists
        my $handle = $bconn->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='tm'");
        my $result = $handle->execute();
        if ($result eq '0E0') {
            # result returned
            my $found = $handle->fetch();
            if ($found) {
                # table tm found
                $found = 0;
                $handle = $bconn->prepare("PRAGMA table_info(tm)");
                $handle->execute();
                while ( my @row = $handle->fetchrow_array() ) {
                    if ( $row[1] eq 'msgfiles' ) {
                        $found = 1;
                        last;
                    }
                }
                unless ($found) {
                    # column msgfiles not found create it
                    $bconn->do("ALTER TABLE tm ADD COLUMN msgfiles TEXT NOT NULL DEFAULT ''");
                }
            }else{
                # table tm not found
                create_sqlite_tables();
            }
        } else {
            # no result returned try creation
            create_sqlite_tables();
        }
    };
    if ($@) {
        $errormsg = $@;
        $errormsg =~ s/ at .*? line \d+.$//;
        MailScanner::Log::InfoLog("BaruwaSQL: Backup DB creation Fail: $errormsg");
        print STDERR "BaruwaSQL[$$]: Backup DB creation Failure: $@\n" if $debug;
    }
}

sub openbackupdb {
    eval {
        unless ($bconn) {
            $bconn = DBI->connect_cached(
                "dbi:SQLite:$sqlite_db",
                "", "",
                {
                    PrintError           => 0,
                    AutoCommit           => 1,
                    private_foo_cachekey => 'baruwa_backup',
                    RaiseError           => 1
                }
            );
            # $bconn->sqlite_busy_timeout(5000);
        }
    };
    if ($@) {
        $errormsg = $@;
        $errormsg =~ s/ at .*? line \d+.$//;
        MailScanner::Log::WarnLog("BaruwaSQL: Backup DB init Fail: $errormsg");
        print STDERR "BaruwaSQL[$$]: Backup DB init Fail: $@\n" if $debug;
    }

    create_backupdb_tables();

    eval {
        $bsth = $bconn->prepare(
            "INSERT INTO tm (
            messageid,actions,clientip,date,from_address,from_domain,headers,
            hostname,highspam,rblspam,saspam,spam,nameinfected,otherinfected,
            isquarantined,isarchived,sascore,scaned,size,blacklisted,spamreport,
            whitelisted,subject,time,timestamp,to_address,to_domain,
            virusinfected,msgfiles
        )  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        ) unless $bsth;
    };
    if ($@) {
        MailScanner::Log::WarnLog("BaruwaSQL: Backup DB prep Fail");
        print STDERR "BaruwaSQL[$$]: Backup DB prep Fail: $@\n" if $debug;
    }
}

sub log2backup {
    my ($message) = @_;
    my @addrs = split( ',', $$message{to_address} );
    foreach(@addrs){
        $$message{to_address} = $_;
        eval {
            $bsth->execute(
                $$message{messageid},     $$message{actions},
                $$message{clientip},      $$message{date},
                $$message{from_address},  $$message{from_domain},
                $$message{headers},       $$message{hostname},
                $$message{highspam},      $$message{rblspam},
                $$message{saspam},        $$message{spam},
                $$message{nameinfected},  $$message{otherinfected},
                $$message{isquarantined}, $$message{isarchived},
                $$message{sascore},       $$message{scaned},
                $$message{size},          $$message{blacklisted},
                $$message{spamreport},    $$message{whitelisted},
                $$message{subject},       $$message{time},
                $$message{timestamp},     $$message{to_address},
                $$message{to_domain},     $$message{virusinfected},
                $$message{msgfiles}
            );
        };
        if ($@) {
            MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: => $_ Backup logging failed");
            print STDERR "BaruwaSQL[$$]: $$message{messageid}: => $_ Backup logging failed\n" if $debug;
            eval {
                store_record($message);
            };
            if ($@) {
                $errormsg = $@;
                $errormsg =~ s/ at .*? line \d+.$//;
                MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: prestorage failed: $errormsg");
                print STDERR "BaruwaSQL[$$]: $$message{messageid}: prestorage failed: $@\n" if $debug;
            }
        } else {
            MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: => $_ Logged to Backup");
            print STDERR "BaruwaSQL[$$]: $$message{messageid}: => $_ Logged to Backup\n" if $debug;
        }
    }
}

sub connect2db {
    $db_user = MailScanner::Config::Value('dbusername') if ( !defined($db_user) );
    $db_pass = MailScanner::Config::Value('dbpassword') if ( !defined($db_pass) );
    $baruwa_dsn = MailScanner::Config::Value('dbdsn') if ( !defined($baruwa_dsn) );
    eval {
        local $SIG{ALRM} = sub { die "TIMEOUT\n" };
        eval {
            alarm(10);
            $conn = DBI->connect_cached(
                $baruwa_dsn,
                $db_user, $db_pass,
                {
                    PrintError           => 0,
                    AutoCommit           => 1,
                    private_foo_cachekey => 'baruwa',
                    RaiseError           => 1,
                    ShowErrorStatement   => 1,
                    pg_enable_utf8       => 1
                }
            ) unless $conn && $conn->ping;

            #$conn->do("SET NAMES 'utf8'");
            $sth = $conn->prepare(
                "INSERT INTO messages (
                    messageid,actions,clientip,date,from_address,from_domain,
                    headers,hostname,highspam,rblspam,saspam,spam,
                    nameinfected,otherinfected,isquarantined,isarchived,
                    sascore,scaned,size,blacklisted,spamreport,whitelisted,
                    subject,time,timestamp,to_address,to_domain,
                    virusinfected,msgfiles
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            );
            alarm(0);
        };
        alarm(0);
        die $@ if $@;
    };
    if ($@) {
        $errormsg = $@;
        $errormsg =~ s/ at .*? line \d+.$//;
        MailScanner::Log::WarnLog("BaruwaSQL: DB init Failed: $errormsg");
        print STDERR "BaruwaSQL[$$]: DB init Failed: $@\n" if $debug;
    }
}

sub connect2sphinxql {
    eval {
        local $SIG{ALRM} = sub { die "TIMEOUT\s" };
        eval {
            alarm(10);
            $sphinx = DBI->connect_cached(
                "DBI:mysql:database=sphinx;host=$sphinx_host;port=$sphinx_port",
                '', '',
                {
                    PrintError           => 0,
                    AutoCommit           => 1,
                    private_foo_cachekey => 'baruwasphinx',
                    RaiseError           => 1
                }
            ) unless $sphinx && $sphinx->ping;

            #$sphinx->do("SET NAMES 'utf8'");
            $spth = $sphinx->prepare(
                "INSERT INTO messages_rt (
                id, messageid, subject, headers, hostname, from_addr,
                to_addr, from_dom, to_dom, timestamp, isquarantined)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            );
            alarm(0);
        };
        alarm(0);
        die $@ if $@;
    };
    if ($@) {
        $errormsg = $@;
        $errormsg =~ s/ at .*? line \d+.$//;
        MailScanner::Log::WarnLog("BaruwaSQL: Search DB connection Failed: $errormsg");
        print STDERR "BaruwaSQL[$$]: Search DB connection Failed: $@\n" if $debug;
    }
}

sub ExitBS {
    $conn->disconnect   unless ( !$conn );
    $sphinx->disconnect unless ( !$sphinx );
    $shutdown->send;
    unlock();
}

sub client_connection {
    my $client = IO::Socket::UNIX->new(
        Peer     => $socket,
        Type     => SOCK_STREAM,
        Timeout  => 10,
        Blocking => 0,
    );
    return $client;
}

sub read_pid {
    my $currentpid;
    open PID, "<$pidfile"
      or die "unable to read pid file $pidfile, check permissions";
    $currentpid = <PID>;
    close PID;
    $currentpid =~ m|(\d+)|;
    $currentpid = $1;
    return $currentpid;
}

sub write_pid {
    open PID, ">$pidfile";
    my $currentpid = $$;
    print PID $currentpid;
    close PID;
}

sub handle_conn {
    my ($sock) = @_ or print STDERR "Connection ERROR: $!\n";
    my $handle;
    my @incoming;
    my $cleanup = sub {
        $handle->destroy();
        print STDERR "Closed client connection\n" if $debug;
    };
    my $errorhandle = sub {
        $handle->destroy();
        print STDERR "Socket error occured: $!\n" if $debug;
    };
    use EV;
    use AnyEvent::Handle;
    $handle = AnyEvent::Handle->new(
        fh       => $sock,
        on_error => $errorhandle,
        on_eof   => $cleanup,
    );
    $handle->push_read(
        line => 'END',
        sub {
            my $line = $_[1];
            if ( $line =~ /^EXIT$/ ) {
                print STDERR "\nShutdown requested, shutting down\n" if $debug;
                $shutdown->send;
                return $cleanup->();
            }

            my $tmp = unpack( "u", $line );
            my $message = thaw $tmp;
            return unless defined $$message{messageid};

            connect2db()       unless $conn   && $conn->ping;
            connect2sphinxql() unless $sphinx && $sphinx->ping;

            my @addrs = split( ',', $$message{to_address} );
            my $sentry = 0;
            foreach (@addrs) {
                $$message{to_address} = $_;
                eval {
                    my $id = insert_record($message);
                    MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: => $_ Logged");
                    print STDERR "BaruwaSQL[$$]: $$message{messageid}: => $_ Logged\n" if $debug;
                    $$message{id} = $id;
                };
                if ($@) {
                    # log to sqlite
                    $sentry = 0;
                    log2backup($message);
                } else {
                    # success recover from sqlite
                    $sentry = 1;
                    index_record($message);
                    $$message{id} = undef;
                }
            }
            $message = undef;
            if ($sentry) {
                restore_from_backup();
                restore_from_file();
            }
            return $cleanup->();
        }
    );
    return;
}

sub InitBaruwaLog {
    ($WantLintOnly) = @_;
    my $pid = fork();
    if ($pid) {
        #mailscanner child / bs parent
        waitpid $pid, 0;
    } else {
        # BS process
        POSIX::setsid();
        if ( !fork() ) {
            exit if ($WantLintOnly);
            lock();
            if ( -e $pidfile ) {
                my $currentpid = read_pid();
                if ( kill 0, int($currentpid) ) {
                    if ( -e $socket ) {
                      # bail a process already running with valid pid and socket
                        MailScanner::Log::InfoLog("BaruwaSQL: Alive with PID: $currentpid");
                        exit;
                    } else {
                        # kill hung server process
                        kill -9, int($currentpid);
                    }
                }
                MailScanner::Log::InfoLog("BaruwaSQL: Removing stale PID: $currentpid");
                unlink($pidfile);
            }
            MailScanner::Log::InfoLog("BaruwaSQL: starting up with PID: $$");
            write_pid();
            open STDIN,  "</dev/null";
            open STDOUT, ">/dev/null";
            # open STDERR, ">/dev/null";
            $SIG{HUP} = $SIG{INT} = $SIG{PIPE} = $SIG{TERM} = \&ExitBS;
            $0 = "BSQL";
            use EV;
            use AnyEvent;
            use AnyEvent::Socket;
            $shutdown = AnyEvent->condvar;
            openbackupdb();
            connect2db();
            connect2sphinxql();
            eval { $server = tcp_server 'unix/', $socket, \&handle_conn; };

            if ($@) {
                $errormsg = $@;
                $errormsg =~ s/ at .*? line \d+.$//;
                MailScanner::Log::WarnLog("BaruwaSQL: server error: $errormsg");
                print STDERR "BaruwaSQL[$$]: server error: $@\n" if $debug;
            }
            $shutdown->recv;
            ExitBS();
        }
        exit;
    }
}

sub EndBaruwaLog {
    if ($WantLintOnly) {
        MailScanner::Log::InfoLog("BaruwaSQL: Shutdown lint process");
        print STDERR "BaruwaSQL[$$]: Lint request no shutdown required\n" if $debug;
        return;
    }
    MailScanner::Log::InfoLog("BaruwaSQL: shutdown requested by child: $$");
    print STDERR "BaruwaSQL[$$]: shutdown requested by child: $$\n" if $debug;
}

sub BaruwaLog {
    my ($message) = @_;

    return unless $message;

    my (%rcpts);
    map { $rcpts{ lc($_) } = 1; } @{ $message->{to} };
    @{ $message->{to} } = keys %rcpts;

    my $spamreport = $message->{spamreport};
    $spamreport =~ s/\n/ /g;
    $spamreport =~ s/\t//g;

    my ( $quarantined, $archived, $msgfiles );
    $quarantined = 0;
    $archived    = 0;

    if ( ( scalar( @{ $message->{quarantineplaces} } ) ) +
        ( scalar( @{ $message->{spamarchive} } ) ) > 0 )
    {
        $quarantined = 1;
    }

    if ( scalar( @{ $message->{archiveplaces} } ) ) {
        $archived = 1;
    }

    if ( scalar( @{ $message->{quarantineplaces} } ) ) {
        $msgfiles = join( ":", @{ $message->{quarantineplaces} } );
    }
    elsif ( scalar( @{ $message->{spamarchive} } ) ) {
        $msgfiles = join( ":", @{ $message->{spamarchive} } );
    }
    else {
        $msgfiles = "";
    }

    my ( $sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst ) =
      gmtime();
    my ($timestamp) = sprintf(
        "%d-%02d-%02d %02d:%02d:%02d",
        $year + 1900,
        $mon + 1, $mday, $hour, $min, $sec
    );

    my $sphinxts = timegm( $sec, $min, $hour, $mday, $mon, $year );

    my ($date) = sprintf( "%d-%02d-%02d",   $year + 1900, $mon + 1, $mday );
    my ($time) = sprintf( "%02d:%02d:%02d", $hour,        $min,     $sec );

    my $clientip = $message->{clientip};
    $clientip =~ s/^(\d+\.\d+\.\d+\.\d+)(\.\d+)$/$1/;

    if ( $spamreport =~ /USER_IN_WHITELIST/ ) {
        $message->{whitelisted} = 1;
    }
    if ( $spamreport =~ /USER_IN_BLACKLIST/ ) {
        $message->{blacklisted} = 1;
    }

    my ( $todomain, @todomain );
    @todomain = @{ $message->{todomain} };
    $todomain = $todomain[0];

    unless ( defined( $$message{actions} ) and $$message{actions} ) {
        $$message{actions} = 'deliver';
    }

    unless ( defined( $$message{isrblspam} ) and $$message{isrblspam} ) {
        $$message{isrblspam} = 0;
    }
    unless ( defined( $$message{isspam} ) and $$message{isspam} ) {
        $$message{isspam} = 0;
    }

    unless ( defined( $$message{issaspam} ) and $$message{issaspam} ) {
        $$message{issaspam} = 0;
    }

    unless ( defined( $$message{ishigh} ) and $$message{ishigh} ) {
        $$message{ishigh} = 0;
    }

    unless ( defined( $$message{spamblacklisted} )
        and $$message{spamblacklisted} )
    {
        $$message{spamblacklisted} = 0;
    }

    unless ( defined( $$message{spamwhitelisted} )
        and $$message{spamwhitelisted} )
    {
        $$message{spamwhitelisted} = 0;
    }

    unless ( defined( $$message{sascore} ) and $$message{sascore} ) {
        $$message{sascore} = 0;
    }

    unless ( defined( $$message{utf8subject} ) and $$message{utf8subject} ) {
        $$message{subject} = '';
    }

    unless ( defined($spamreport) and $spamreport ) {
        $spamreport = '';
    }

    unless ( defined( $$message{from} ) and $$message{from} ) {
        $$message{from} = '<>';
    }

    my ($headers, $subject, $rawheaders, $tmpm, $head, $encoding, $parser);
    $rawheaders = join("\n", @{$message->{headers}});

    if (is_utf8($rawheaders) and is_utf8($message->{utf8subject})) {
        $headers = $rawheaders;
        $subject = $message->{utf8subject};
    }else{
        $parser = MIME::Parser->new();
        $parser->output_to_core(1);
        $tmpm = $parser->parse_data($rawheaders);
        $head = $tmpm->head();
        $encoding = $head->mime_attr('content-type.charset');
        $encoding = 'ascii' unless($encoding);
        if (is_utf8($rawheaders)) {
            $headers = $rawheaders;
        }else{
            eval {
                $headers = decode($encoding, $rawheaders);
            };
            if ($@) {
                $headers = $rawheaders;
            }
        }
        if (is_utf8($message->{utf8subject})) {
            $subject = $message->{utf8subject};
        }else{
            eval {
                $subject = decode($encoding, $message->{utf8subject});
            };
            if ($@) {
                $subject = $message->{utf8subject};
            }
        }
        undef($parser);
    }

    my %msg;
    $msg{timestamp}     = $timestamp;
    $msg{messageid}     = $message->{id};
    $msg{size}          = $message->{size};
    $msg{from_address}  = lc( $message->{from} );
    $msg{from_domain}   = lc( $message->{fromdomain} );
    $msg{to_address}    = join( ",", @{ $message->{to} } );
    $msg{to_domain}     = lc($todomain);
    $msg{subject}       = $subject;
    $msg{clientip}      = $clientip;
    $msg{spam}          = $message->{isspam};
    $msg{highspam}      = $message->{ishigh};
    $msg{saspam}        = $message->{issaspam};
    $msg{rblspam}       = $message->{isrblspam};
    $msg{whitelisted}   = $message->{spamwhitelisted};
    $msg{blacklisted}   = $message->{spamblacklisted};
    $msg{sascore}       = $message->{sascore};
    $msg{spamreport}    = $spamreport;
    $msg{virusinfected} = $message->{virusinfected};
    $msg{nameinfected}  = $message->{nameinfected};
    $msg{otherinfected} = $message->{otherinfected};
    $msg{hostname}      = $hostname;
    $msg{date}          = $date;
    $msg{time}          = $time;
    $msg{headers}       = $headers;
    $msg{actions}       = $message->{actions};
    $msg{isquarantined} = $quarantined;
    $msg{isarchived}    = $archived;
    $msg{scaned}        = $message->{scanmail};
    $msg{indexerts}     = $sphinxts;
    $msg{msgfiles}      = $msgfiles;

    my $f = freeze \%msg;
    my $p = pack( "u", $f );

    my $client = client_connection();
    if ($client) {
        MailScanner::Log::InfoLog("BaruwaSQL: $msg{messageid} send to logger");
        print STDERR "BaruwaSQL[$$]: $msg{messageid} send to logger\n" if $debug;
        print $client $p;
        print $client "END\n";
        close $client;
        print STDERR "BaruwaSQL[$$]: $msg{messageid} SENT\n" if $debug;
    }
    else {
        MailScanner::Log::InfoLog("BaruwaSQL: $msg{messageid} sent to backup");
        print STDERR "BaruwaSQL[$$]: $msg{messageid}: Using backup\n" if $debug;
        openbackupdb() unless $bconn;
        log2backup( \%msg );
        print STDERR "BaruwaSQL[$$]: $msg{messageid}: BACKEDUP\n" if $debug;
    }
}

1;

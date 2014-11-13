# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2012  Andrew Colin Kissa <andrew@topdog.za.net>
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
use String::CRC32;
use Sys::Hostname;
use MailScanner::Config;
use Storable(qw[freeze thaw]);
use Encoding::FixLatin qw(fix_latin);

my ($shutdown, $server, $WantLintOnly);
my ($work_dir, $socket, $pidfile, $sqlite_db);
my ($conn, $bconn, $sphinx, $sth, $bsth, $spth);
my ($db_user, $db_pass, $baruwa_dsn);
my $hostname = hostname;

$Storable::accept_future_minor = 1;
$work_dir                      = '/var/spool/MailScanner/incoming';
$socket                        = "$work_dir/baruwa.sock";
$pidfile                       = "$work_dir/baruwa-bs.pid";
$sqlite_db                     = "$work_dir/baruwa2.db";
# $host = '127.0.0.1';
# $port = 11553;

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
        $$message{to_domain},     $$message{virusinfected}
    );
    my $id = $conn->last_insert_id(undef,undef,"messages",undef);
    return $id;
}

sub index_record {
    my ($message) = @_;
    return unless defined $$message{id};
    eval {
        $spth->execute(
            $$message{id},       $$message{messageid},
            $$message{subject},  $$message{headers},
            $$message{hostname}, crc32($$message{from_address}),
            crc32($$message{to_address}),  crc32($$message{from_domain}),
            crc32($$message{to_domain}),   $$message{indexerts},
            $$message{isquarantined}
        );
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: Indexed");
        print STDERR "BaruwaSQL: $$message{messageid}: Indexed\n";
    };
    if ($@) {
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: indexing failed");
        print STDERR "BaruwaSQL: $$message{messageid}: indexing failed: $@\n";
    }
}

sub restore_from_backup {
    my $st;
    eval {
        $st = $bconn->prepare("SELECT * FROM tm");
        $st->execute();
    };
    if ($@) {
        MailScanner::Log::InfoLog("BaruwaSQL: Backup DB recovery Failure");
        print STDERR "BaruwaSQL: Backup DB recovery Failure: $@\n";
        return;
    }

    while ( my $message = $st->fetchrow_hashref ) {
        eval {
            insert_record($message);
            MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: restored from backup");
            print STDERR "BaruwaSQL: $$message{messageid}: restored from backup\n";
        };
        if ($@) {
            MailScanner::Log::InfoLog("BaruwaSQL: Backup DB insert Fail");
            print STDERR "BaruwaSQL: Backup DB insert Fail: $@\n";
        } else {
        eval {
                my @bind_values = ($$message{messageid}, $$message{to_address});
                $bconn->do("DELETE FROM tm WHERE messageid=? AND to_address=?", undef, @bind_values)
        };
        if ($@) {
            MailScanner::Log::WarnLog("BaruwaSQL: Backup DB clean temp Fail");
            print STDERR "BaruwaSQL: Backup DB clean temp Fail: $@\n";
        }
    }
    }
}

sub create_backupdb_tables {
    eval {
        $bconn->do("PRAGMA default_synchronous = OFF");
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
                scaned INT NOT NULL
            )"
        );
    };
}

sub openbackupdb {
    eval {
        $bconn = DBI->connect_cached(
            "dbi:SQLite:$sqlite_db",
            "", "",
            {
                PrintError           => 0,
                AutoCommit           => 1,
                private_foo_cachekey => 'baruwa_backup',
                RaiseError           => 1
            }
        ) unless ($bconn);
    };
    if ($@) {
        MailScanner::Log::WarnLog("BaruwaSQL: Backup DB init Fail: $@");
        print STDERR "BaruwaSQL: Backup DB init Fail: $@\n";
    }

    create_backupdb_tables();

    eval {
        $bsth = $bconn->prepare(
            "INSERT INTO tm (
            messageid,actions,clientip,date,from_address,from_domain,headers,
            hostname,highspam,rblspam,saspam,spam,nameinfected,otherinfected,
            isquarantined,isarchived,sascore,scaned,size,blacklisted,spamreport,
            whitelisted,subject,time,timestamp,to_address,to_domain,
            virusinfected
        )  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        ) unless $bsth;
    };
    if ($@) {
        MailScanner::Log::WarnLog("BaruwaSQL: Backup DB prep Fail");
        print STDERR "BaruwaSQL: Backup DB prep Fail: $@\n";
    }
}

sub log2backup {
    my ($message) = @_;
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
            $$message{to_domain},     $$message{virusinfected}
        );
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid} Logged using Backup");
        print STDERR "BaruwaSQL: $$message{messageid} Logged using Backup\n";
    };
    if ($@) {
        MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: Backup logging failed");
        print STDERR "BaruwaSQL: $$message{messageid}: Backup logging failed\n";
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
                    virusinfected
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            );
            alarm(0);
        };
        alarm(0);
        die $@ if $@;
    };
    if ($@) {
        MailScanner::Log::WarnLog("BaruwaSQL: DB init Failed: $@");
        print STDERR "BaruwaSQL: DB init Failed: $@\n";
    }
}

sub connect2sphinxql {
    eval {
        local $SIG{ALRM} = sub { die "TIMEOUT\s" };
        eval {
            alarm(10);
            $sphinx = DBI->connect_cached(
                "DBI:mysql:database=sphinx;host=127.0.0.1;port=9306",
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
        MailScanner::Log::WarnLog("BaruwaSQL: Search DB connection Failed: $@");
        print "BaruwaSQL: Search DB connection Failed: $@\n";
    }
}

sub ExitBS {
    $conn->disconnect unless (!$conn);
    $sphinx->disconnect unless (!$sphinx);
    $shutdown->send;
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
    open PID, "<$pidfile" or die "unable to read pid file $pidfile, check permissions";
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
    my($sock) = @_ or print STDERR "Connection ERROR: $!\n";
    my $handle;
    my @incoming;
    my $cleanup = sub {
        $handle->destroy();
        print STDERR "Closed client connection\n";
    };
    my $errorhandle = sub {
        $handle->destroy();
        print STDERR "Socket error occured: $!\n";
    };
    use EV;
    use AnyEvent::Handle;
    $handle = AnyEvent::Handle->new(
        fh  => $sock,
        on_error => $errorhandle,
        on_eof => $cleanup,
    );
    $handle->push_read(
        line => 'END',
        sub {
        my $line = $_[1];
        if ($line =~ /^EXIT$/) {
            print STDERR "\nShutdown requested, shutting down\n";
            $shutdown->send;
            return $cleanup->();
        }

        my $tmp = unpack("u", $line);
        my $message = thaw $tmp;
        return unless defined $$message{messageid};

        connect2db() unless $conn && $conn->ping;
        connect2sphinxql() unless $sphinx && $sphinx->ping;

            my @addrs = split( ',', $$message{to_address} );
            foreach (@addrs) {
                $$message{to_address} = $_;
        eval {
            my $id = insert_record($message);
                    MailScanner::Log::InfoLog("BaruwaSQL: $$message{messageid}: to: $_ Logged");
                    print STDERR "BaruwaSQL: $$message{messageid}: to: $_ Logged\n";
            $$message{id} = $id;
            index_record($message);
                    $$message{id} = undef;
        };
        if ($@) {
            # log to sqlite
            log2backup($message);
                }
                else {
            # success recover from sqlite
            restore_from_backup();
        }
            }
        $message = undef;
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
        if (!fork()) {
            exit if ( $WantLintOnly );
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
            open STDERR, ">/dev/null";
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
                MailScanner::Log::WarnLog("BaruwaSQL: server error: $@");
            }
            $shutdown->recv;
            ExitBS();
        }
        exit;
    }
}

sub EndBaruwaLog {
    if ( $WantLintOnly ) {
        MailScanner::Log::InfoLog("BaruwaSQL: Shutdown lint process");
        print STDERR "BaruwaSQL: Lint request no shutdown required\n";
        return;
    }
    MailScanner::Log::InfoLog("BaruwaSQL: shutdown requested by child: $$");
    print STDERR "BaruwaSQL: shutdown requested by child: $$\n";
}

sub BaruwaLog {
    my ($message) = @_;

    return unless $message;

    my (%rcpts);
    map { $rcpts{lc($_)} = 1; } @{ $message->{to} };
    @{ $message->{to} } = keys %rcpts;

    my $spamreport = $message->{spamreport};
    $spamreport =~ s/\n/ /g;
    $spamreport =~ s/\t//g;

    my ( $quarantined, $archived);
    $quarantined = 0;
    $archived = 0;

    if ( ( scalar( @{ $message->{quarantineplaces} } ) ) +
        ( scalar( @{ $message->{spamarchive} } ) ) > 0 )
    {
        $quarantined = 1;
    }

    if ( scalar( @{ $message->{archiveplaces} } ) ) {
        $archived = 1;
    }

    my ( $sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst ) =
      gmtime();
    my ($timestamp) = sprintf(
        "%d-%02d-%02d %02d:%02d:%02d",
        $year + 1900,
        $mon + 1, $mday, $hour, $min, $sec
    );

    my $sphinxts = timegm($sec, $min, $hour, $mday, $mon, $year); 
    
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

    unless ( defined($$message{from}) and $$message{from} ){
        $$message{from} = '<>';
    }

    my %msg;
    $msg{timestamp}     = $timestamp;
    $msg{messageid}     = $message->{id};
    $msg{size}          = $message->{size};
    $msg{from_address}  = lc($message->{from});
    $msg{from_domain}   = lc($message->{fromdomain});
    $msg{to_address}    = join(",", @{$message->{to}});
    $msg{to_domain}     = lc($todomain);
    $msg{subject}       = fix_latin($message->{utf8subject});
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
    $msg{headers}       = fix_latin(join("\n", @{$message->{headers}}));
    $msg{actions}       = $message->{actions};
    $msg{isquarantined} = $quarantined;
    $msg{isarchived}    = $archived;
    $msg{scaned}        = $message->{scanmail};
    $msg{indexerts}     = $sphinxts;

    my $f = freeze \%msg;
    my $p = pack( "u", $f );

    my $client = client_connection();
    if ($client) {
        MailScanner::Log::InfoLog("BaruwaSQL: $msg{messageid} send to logger");
        print STDERR "BaruwaSQL: $msg{messageid} send to logger\n";
        print $client $p;
        print $client "END\n";
        close $client;
        print STDERR "BaruwaSQL: $msg{messageid} SENT\n";
    } else {
        MailScanner::Log::InfoLog("BaruwaSQL: $msg{messageid} sent to backup");
        print STDERR "$msg{messageid}: Using backup\n";
        openbackupdb() unless $bconn;
        log2backup( \%msg );
        print STDERR "$msg{messageid}: BACKEDUP\n";
    }
}

1;

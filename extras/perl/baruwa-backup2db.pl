#!/usr/bin/perl -I/usr/share/MailScanner
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
use DBI;
use strict;
use MailScanner::Config;
use Encoding::FixLatin qw(fix_latin);

my ($sqlite_db, $work_dir);
my ($conn, $bconn, $sth, $bsth);
my ($db_user, $db_pass, $baruwa_dsn);

my $ConfFile = '/etc/MailScanner/MailScanner.conf';

$work_dir                      = '/var/spool/MailScanner/incoming';
$sqlite_db                     = "$work_dir/baruwa2.db";

sub insert_record {
    my ($message) = @_;
    my $headers = fix_latin($$message{headers});
    my $subject = fix_latin($$message{subject});
    $sth->execute(
        $$message{messageid},     $$message{actions},
        $$message{clientip},      $$message{date},
        $$message{from_address},  $$message{from_domain},
        $headers,       $$message{hostname},
        $$message{highspam},      $$message{rblspam},
        $$message{saspam},        $$message{spam},
        $$message{nameinfected},  $$message{otherinfected},
        $$message{isquarantined}, $$message{isarchived},
        $$message{sascore},       $$message{scaned},
        $$message{size},          $$message{blacklisted},
        $$message{spamreport},    $$message{whitelisted},
        $subject,       $$message{time},
        $$message{timestamp},     $$message{to_address},
        $$message{to_domain},     $$message{virusinfected}
    );
    my $id = $conn->last_insert_id(undef,undef,"messages",undef);
    return $id;
}

sub restore_from_backup {
    my $st;
    eval {
        $st = $bconn->prepare("SELECT * FROM tm");
        $st->execute();
    };
    if ($@) {
        print STDERR "BaruwaSQL: Backup DB recovery Failure: $@\n";
        return;
    }

    my @ids;
    while ( my $message = $st->fetchrow_hashref ) {
        eval {
            insert_record($message);
            print STDERR "BaruwaSQL: $$message{messageid}: restored from backup\n";
            push @ids, $$message{messageid};
        };
        if ($@) {
            print STDERR "BaruwaSQL: Backup DB insert Fail: $@\n";
        }
    }

    # delete messages that have been logged
    while (@ids) {
        my @tmp_ids = splice( @ids, 0, 50 );
        my $del_ids = join q{,}, map { '?' } @tmp_ids;
        eval {
            $bconn->do( "DELETE FROM tm WHERE messageid IN ($del_ids)", undef, @tmp_ids );
        };
        if ($@) {
            print STDERR "BaruwaSQL: Backup DB clean temp Fail: $@\n";
        }
    }
    undef @ids;
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
        print STDERR "BaruwaSQL: Backup DB init Fail: $@\n";
    }

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
        print STDERR "BaruwaSQL: Backup DB prep Fail: $@\n";
    }
}


sub connect2db {
    $db_user = MailScanner::Config::QuickPeek($ConfFile, 'dbusername');
    $db_pass = MailScanner::Config::QuickPeek($ConfFile, 'dbpassword');
    $baruwa_dsn = MailScanner::Config::QuickPeek($ConfFile, 'dbdsn');
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
        print STDERR "BaruwaSQL: DB init Failed: $@\n";
    }
}

print "Connecting to DB\n";
connect2db();
print "Connecting to SQLite\n";
openbackupdb();
print "Restoring messages\n";
restore_from_backup();
print "Exiting\n";

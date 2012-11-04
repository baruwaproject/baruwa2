# -*- coding: utf-8 -*-
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2011  Andrew Colin Kissa <andrew@topdog.za.net>
# vim: ai ts=4 sts=4 et sw=4

use Authen::Passphrase::BlowfishCrypt;

sub check_password {
    my ($hash, $password) = @_;
    return 'false' unless ($hash and $password);
    if (Authen::Passphrase::BlowfishCrypt->from_crypt($hash)->match($password)) {
        return 'true';
    } else {
        return 'false';
    }
}
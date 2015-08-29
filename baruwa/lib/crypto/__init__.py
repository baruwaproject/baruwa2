# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# Baruwa - Web 2.0 MailScanner front-end.
# Copyright (C) 2010-2015  Andrew Colin Kissa <andrew@topdog.za.net>
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
"""Crypto functions"""

import os

from M2Crypto import Rand, RSA, BIO, SMIME


def blank_callback():
    "Replace the default dashes"
    return


def make_key_pair(key_length=2048):
    "Make public/private keys"
    Rand.rand_seed(os.urandom(key_length))
    key = RSA.gen_key(key_length, 65537, blank_callback)
    pri_mem = BIO.MemoryBuffer()
    pub_mem = BIO.MemoryBuffer()
    key.save_key_bio(pri_mem, None)
    key.save_pub_key_bio(pub_mem)
    return pub_mem.getvalue(), pri_mem.getvalue()


def remove_pub_pem_headers(pub):
    """String comments for display"""
    pub = pub.replace("-----BEGIN PUBLIC KEY-----\n", "")
    pub = pub.replace("\n-----END PUBLIC KEY-----\n", "")
    return pub


def bio_from_file_path(file_path):
    """Returns a BIO object for OpenSSL from input file path"""
    try:
        fdsc = open(file_path, 'rb')
        file_bio = BIO.File(fdsc)
    except IOError:
        file_bio = None
    return file_bio


def sign(filename, pkey, cert, signed_file):
    """Sign a text file"""
    try:
        handle = open(filename, 'rb')
        filebio = BIO.File(handle)
        signer = SMIME.SMIME()
        signer.load_key(pkey, cert)
        Rand.rand_seed(os.urandom(2048))
        p7f = signer.sign(filebio)
        data = BIO.MemoryBuffer(None)
        p7f.write_der(data)
        with open(signed_file, 'wb') as handle:
            handle.write(data.read())
        return True
    except (IOError, SMIME.SMIME_Error, SMIME.PKCS7_Error), msg:
        raise ValueError(str(msg))

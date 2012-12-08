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
"""SSL functions"""

import os

from M2Crypto import Rand, RSA, BIO


def blank_callback():
    "Replace the default dashes"
    return


def make_key_pair(key_length=2048):
    "Make public/private keys"
    Rand.rand_seed (os.urandom (key_length))
    key = RSA.gen_key (key_length, 65537, blank_callback)
    pri_mem = BIO.MemoryBuffer()
    pub_mem = BIO.MemoryBuffer()
    key.save_key_bio(pri_mem, None)
    key.save_pub_key_bio(pub_mem)
    return pub_mem.getvalue(), pri_mem.getvalue()

    # M2Crypto.Rand.rand_seed (os.urandom (key_length))
    # key = M2Crypto.RSA.gen_key (key_length, 65537, blank_callback)
    # tmpfile = StringIO('')
    # key.save_key (tmpfile, None)
    # pri_key = tmpfile.read()
    # tmpfile.close()
    # key.save_pub_key (tmpfile)
    # pub_key = tmpfile.read()
    # tmpfile.close()
    # return pub_key, pri_key

    # key = crypto.PKey()
    # key.generate_key(crypto.TYPE_RSA, key_length)
    # 
    # cert = crypto.X509()
    # cert.set_pubkey(key)
    # cert.sign(key, hash_algo)
    # 
    # pub_key = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    # pri_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    # return pub_key, pri_key


def remove_pub_pem_headers(pub):
    pub = pub.replace("-----BEGIN PUBLIC KEY-----\n","")
    pub = pub.replace("\n-----END PUBLIC KEY-----\n","")
    return pub
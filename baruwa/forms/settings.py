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
"Settings forms"

from wtforms import BooleanField, validators, TextField
from wtforms import IntegerField, SelectField, TextAreaField
from wtforms import SelectMultipleField
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form, REQ_MSG
from baruwa.lib.regex import HOST_OR_IPV4_RE


YES_NO = (('yes', _('Yes')), ('no', _('No')))
TNEF_ACTIONS = (('replace', _('Replace')),
                ('add', _('Add')),
                ('no', _('No')))
HEADER_ACTIONS = (('add', _('Add')),
                ('append', _('Append')),
                ('replace', _('Replace')))
CODE_SUPPORT = (('supported', _('Supported')),
                ('none', _('None')), 
                ('unsupported', _('Unsupported')),
                ('alpha', _('Alpha')),
                ('beta', _('Beta')))
START_END = (('start', _('Start')),
            ('end', _('End')),
            ('yes', _('Yes')),
            ('no', _('No')))
CONVERT = (('convert', _('Disarm')),
            ('yes', _('Yes')),
            ('no', _('No')))
MTAS = (('exim', 'Exim'),
    ('sendmail', 'Sendmail'),
    ('postfix', 'Postfix'),
    ('zmailer', 'Zmailer'))
VIRUS_SCANNERS = (
    ('auto', _('Auto detect')),
    #('sophos', 'Sophos'),
    #('sophossavi', 'Sophossavi'),
    #('mcafee', 'Mcafee'),
    #('command', 'Command line'),
    #('bitdefender', 'Bitdefender'),
    #('drweb', 'Drweb'),
    #('kaspersky-4.5', 'Kaspersky version 4.5'),
    #('kaspersky', 'Kaspersky'),
    #('kavdaemonclient', 'Kavdaemonclient'),
    #('etrust', 'Etrust'),
    #('inoculate', 'Inoculate'),
    #('inoculan', 'Inoculan'),
    #('nod32', 'Nod32'),
    #('nod32-1.99', 'Nod32-1.99'),
    #('f-secure', 'F-secure'),
    #('f-prot', 'F-prot'),
    #('f-prot-6', 'F-prot 6'),
    ('f-protd-6', 'F-prot Daemon 6'),
    #('panda', 'Panda'),
    #('rav', 'Rav'),
    #('antivir', 'Antivir'),
    #('clamav', 'Clamav'),
    #('clamavmodule', 'Clamav module'),
    ('clamd', 'Clamav Daemon'),
    #('trend', 'Trend'),
    #('norman', 'Norman'),
    #('css', 'Css'),
    #('avg', 'Avg'),
    #('vexira', 'Vexira'),
    #('symscanengine', 'Symscanengine'),
    #('avast', 'Avast'),
    #('avastd', 'Avast Daemon'),
    #('esets', 'Esets'),
    #('vba32', 'Vba32'),
    #('generic', 'Generic'),
    ('none', 'None'))
SPAM_LISTS = (
    #('spamhaus.org', 'sbl.spamhaus.org.'),
    #('spamhaus-XBL', 'xbl.spamhaus.org.'),
    #('spamhaus-PBL', 'pbl.spamhaus.org.'),
    ('spamhaus-ZEN', 'zen.spamhaus.org.'),
    #('SBL+XBL', 'sbl-xbl.spamhaus.org.'),
    ('spamcop.net', 'bl.spamcop.net.'),
    ('NJABL', 'dnsbl.njabl.org.'),
    #('MAPS-RBL', 'blackholes.mail-abuse.org.'),
    #('MAPS-DUL', 'dialups.mail-abuse.org.'),
    #('MAPS-RSS', 'relays.mail-abuse.org.'),
    #('MAPS-RBL+', 'rbl-plus.mail-abuse.ja.net.'),
    #('RFC-IGNORANT-DSN', 'dsn.rfc-ignorant.org.'),
    #('RFC-IGNORANT-POSTMASTER', 'postmaster.rfc-ignorant.org.'),
    #('RFC-IGNORANT-ABUSE', 'abuse.rfc-ignorant.org.'),
    #('RFC-IGNORANT-WHOIS', 'whois.rfc-ignorant.org.'),
    #('RFC-IGNORANT-IPWHOIS', 'ipwhois.rfc-ignorant.org.'),
    #('RFC-IGNORANT-BOGUSMX', 'bogusmx.rfc-ignorant.org.'),
    #('Easynet-DNSBL', 'blackholes.easynet.nl.'),
    #('Easynet-Proxies', 'proxies.blackholes.easynet.nl.'),
    #('Easynet-Dynablock', 'dynablock.easynet.nl.'),
    ('SORBS-DNSBL', 'dnsbl.sorbs.net.'),
    #('SORBS-HTTP', 'http.dnsbl.sorbs.net.'),
    #('SORBS-SOCKS', 'socks.dnsbl.sorbs.net.'),
    #('SORBS-MISC', 'misc.dnsbl.sorbs.net.'),
    #('SORBS-SMTP', 'smtp.dnsbl.sorbs.net.'),
    #('SORBS-WEB', 'web.dnsbl.sorbs.net.'),
    #('SORBS-SPAM', 'spam.dnsbl.sorbs.net.'),
    #('SORBS-BLOCK', 'block.dnsbl.sorbs.net.'),
    #('SORBS-ZOMBIE', 'zombie.dnsbl.sorbs.net.'),
    #('SORBS-DUL', 'dul.dnsbl.sorbs.net.'),
    #('SORBS-RHSBL', 'rhsbl.sorbs.net.'),
    #('SORBS-BADCONF', 'badconf.rhsbl.sorbs.net.'),
    #('SORBS-NOMAIL', 'nomail.rhsbl.sorbs.net.'),
    ('CBL', 'cbl.abuseat.org.'))
WATERMARK_OPTIONS = (
    ("nothing", _('Do nothing')),
    ('delete', _("Delete")),
    ('spam', _("Flag as spam")),
    ("high-scoring spam", _('Flag as high spam')),
)
SYSLOG_FACILITIES = (
    ('mail', 'mail'),
    ('daemon', 'daemon'),
    ('syslog', 'syslog'),
    ('local0', 'local0'),
    ('local1', 'local1'),
    ('local2', 'local2'),
    ('local3', 'local3'),
    ('local4', 'local4'),
    ('local5', 'local5'),
    ('local6', 'local6'),
    ('local7', 'local7'),
)
# CODE_STATUS = (
#     ('Supported', 'supported'),
#     ('None', 'none'),
#     ('Unsupported', 'unsupported'),
#     ('Alpha', 'alpha'),
#     ('Beta', 'beta')
# )
global_settings_dict = {
    'org_name': '%org-name%',
    'org_fullname': '%org-long-name%',
    'org_website': '%web-site%',
    'etc_dir': '%etcdir%',
    'report_dir': '%reportdir%',
    'rules_dir': '%rulesdir%',
    'mcp_dir': '%mcpdir%'
}


class ServerForm(Form):
    "Server form"
    hostname = TextField(_('Hostname'),
                        [validators.Required(message=REQ_MSG),
                        validators.Regexp(HOST_OR_IPV4_RE,
                        message=_('Invalid Domain name or IPv4 address'))])
    enabled = BooleanField(_('Enabled'))


class GeneralSettings(Form):
    "Global settings form"
    org_name = TextField(_('Sitename'), default='BARUWA')
    org_fullname = TextField(_('Your Organisation Name'),
                            default='BARUWA MAIL GATEWAY')
    org_website = TextField(_('Organisation website'),
                            default='www.baruwa.org')
    children = IntegerField(_('Max Children'),
                            default=5)
    queuescaninterval = IntegerField(_('Queue Scan Interval'),
                            default=6)
    restartevery = IntegerField(_('Restart Every'),
                            default=7200)
    usedefaultswithmanyrecips = SelectField(_('Use Default Rules With Multiple Recipients'),
                            choices=YES_NO,
                            default='yes')
    getipfromheader = SelectField(_('Read IP Address From Received Header'),
                            choices=YES_NO,
                            default='no')
    debug = SelectField(_('Debug'),
                            choices=YES_NO,
                            default='no')
    debugspamassassin = SelectField(_('Debug SpamAssassin'),
                            choices=YES_NO,
                            default='no')
    deliverinbackground = SelectField(_('Deliver In Background'),
                            choices=YES_NO,
                            default='yes')
    deliverymethod = SelectField(_('Delivery Method'),
                            choices=[('batch', 'Batch'), ('queue', 'Queue')],
                            default='batch')
    syntaxcheck = SelectField(_('Automatic Syntax Check'),
                            choices=YES_NO,
                            default='yes')
    minimumcodestatus = SelectField(_('Minimum Code Status'),
                            choices=CODE_SUPPORT,
                            default='supported')


class ProcessingSettings(Form):
    "Processing settings"
    maxunscannedbytes = IntegerField(_('Max Unscanned Bytes Per Scan'),
                            default=100000000)
    maxdirtybytes = IntegerField(_('Max Unsafe Bytes Per Scan'),
                            default=50000000)
    maxunscannedmessages = IntegerField(_('Max Unscanned Messages Per Scan'),
                            default=30)
    maxdirtymessages = IntegerField(_('Max Unsafe Messages Per Scan'),
                            default=30)
    criticalqueuesize = IntegerField(_('Max Normal Queue Size'),
                            default=800)
    procdbattempts = IntegerField(_('Maximum Processing Attempts'),
                            default=6)
    maxparts = IntegerField(_('Maximum Attachments Per Message'),
                            default=200)
    expandtnef = SelectField(_('Expand TNEF'),
                            choices=YES_NO,
                            default='yes')
    replacetnef = SelectField(_('Use TNEF Contents'),
                            choices=TNEF_ACTIONS,
                            default='replace')
    deliverunparsabletnef = SelectField(_('Deliver Unparsable TNEF'),
                            choices=YES_NO,
                            default='yes')
    tneftimeout = IntegerField(_('TNEF Timeout'),
                            default=120)
    filetimeout = IntegerField(_('File Timeout'),
                            default=20)
    gunziptimeout = IntegerField(_('Gunzip Timeout'),
                            default=50)
    unrartimeout = IntegerField(_('Unrar Timeout'),
                            default=50)
    maxzipdepth = IntegerField(_('Maximum Archive Depth'),
                            default=2)
    findarchivesbycontent = SelectField(_('Find Archives By Content'),
                            choices=YES_NO,
                            default='yes')
    unpackole = SelectField(_('Unpack Microsoft Documents'),
                            choices=YES_NO,
                            default='yes')
    zipattachments = SelectField(_('Zip Attachments'),
                            choices=YES_NO,
                            default='yes')
    attachzipname = TextField(_('Attachments Zip Filename'),
                            default='MessageAttachments.zip')
    attachzipminsize = IntegerField(_('Attachments Min Total Size To Zip'),
                            default=100000)
    attachzipignore = TextField(_('Attachment Extensions Not To Zip'),
                            default='.zip .rar .gz .tgz .mpg .mpe .mpeg .mp3 .rpm')
    addtextofdoc = SelectField(_('Add Text Of Doc'),
                            choices=YES_NO,
                            default='yes')
    antiwordtimeout = IntegerField(_('Antiword Timeout'),
                            default=50)
    unzipmaxmembers = IntegerField(_('Unzip Maximum Files Per Archive'),
                            default=0)
    unzipmaxsize = IntegerField(_('Unzip Maximum File Size'),
                            default=50000)
    unzipmembers = TextField(_('Unzip Filenames'),
                            default='*.txt *.ini *.log *.csv')
    unzipmimetype = TextField(_('Unzip MimeType'),
                            default='text/plain')
    mailheader = TextField(_('Mail Header'),
                            default='X-Baruwa:')
    infoheader = TextField(_('Information Header'),
                            default='X-Baruwa-Information:')
    addenvfrom = SelectField(_('Add Envelope From Header'),
                            choices=YES_NO,
                            default='yes')
    addenvto = SelectField(_('Add Envelope To Header'),
                            choices=YES_NO,
                            default='no')
    envfromheader = TextField(_('Envelope From Header'),
                            default='X-Baruwa-Envelope-From:')
    envtoheader = TextField(_('Envelope To Header'),
                            default='X-Baruwa-Envelope-To:')
    idheader = TextField(_('ID Header'),
                            default='X-Baruwa-ID:')
    ipverheader = TextField(_('IP Protocol Version Header'),
                            default='X-Baruwa-IP-Protocol:')
    cleanheader = TextField(_('Clean Header Value'),
                            default='Found to be clean')
    dirtyheader = TextField(_('Infected Header Value'),
                            default='Found to be infected')
    disinfectedheader = TextField(_('Disinfected Header Value'),
                            default='Disinfected')
    infoPlease = TextField(_('Information Header Value'))
    multipleheaders = SelectField(_('Multiple Headers'),
                            choices=list(HEADER_ACTIONS),
                            default='add')
    newheadersattop = SelectField(_('Place New Headers At Top Of Message'),
                            choices=YES_NO,
                            default='yes')
    hostname = TextField(_('Hostname'),
                            default='the %org-name% ($HOSTNAME) Baruwa')
    signalreadyscanned = SelectField(_('Sign Messages Already Processed'),
                            choices=YES_NO,
                            default='no')
    allowmultsigs = SelectField(_('Allow Multiple HTML Signatures'),
                            choices=YES_NO,
                            default='no')
    isareply = TextField(_('Dont Sign HTML If Headers Exist'))
    markinfectedmessages = SelectField(_('Mark Infected Messages'),
                            choices=YES_NO,
                            default='no')
    signunscannedmessages = SelectField(_('Mark Unscanned Messages'),
                            choices=YES_NO,
                            default='yes')
    unscannedheader = TextField(_('Unscanned Header Value'),
                            default='Not scanned: please contact your Internet E-Mail Service Provider for details')
    removeheaders = TextField(_('Remove These Headers'),
                            default='X-Mozilla-Status: X-Mozilla-Status2:')
    delivercleanedmessages = SelectField(_('Deliver Cleaned Messages'),
                            choices=YES_NO,
                            default='yes')
    scannedmodifysubject = SelectField(_('Scanned Modify Subject'),
                            choices=START_END,
                            default='no')
    scannedsubjecttext = TextField(_('Scanned Subject Text'),
                            default='{Scanned}')
    virusmodifysubject = SelectField(_('Virus Modify Subject'),
                            choices=START_END,
                            default='no')
    virussubjecttext = TextField(_('Virus Subject Text'),
                            default='{Virus?}')
    namemodifysubject = SelectField(_('Filename Modify Subject'),
                            choices=START_END,
                            default='no')
    namesubjecttext = TextField(_('Filename Subject Text'),
                            default='{Filename?}')
    contentmodifysubject = SelectField(_('Content Modify Subject'),
                            choices=START_END,
                            default='no')
    contentsubjecttext = TextField(_('Content Subject Text'),
                            default='{Dangerous Content?}')
    sizemodifysubject = SelectField(_('Size Modify Subject'),
                            choices=START_END,
                            default='no')
    sizesubjecttext = TextField(_('Size Subject Text'),
                            default='{Allowed Message Size Exceeded}')
    disarmmodifysubject = SelectField(_('Disarmed Modify Subject'),
                            choices=START_END,
                            default='no')
    disarmsubjecttext = TextField(_('Disarmed Subject Text'),
                            default='{Message Disarmed}')
    tagphishingsubject = SelectField(_('Phishing Modify Subject'),
                            choices=START_END,
                            default='no')
    phishingsubjecttag = TextField(_('Phishing Subject Text'),
                            default='{Suspected Fraud?}')
    spammodifysubject = SelectField(_('Spam Modify Subject'),
                            choices=START_END,
                            default='no')
    spamsubjecttext = TextField(_('Spam Subject Text'),
                            default='{Probable Spam?}')
    highspammodifysubject = SelectField(_('High Scoring Spam Modify Subject'),
                            choices=START_END,
                            default='no')
    highspamsubjecttext = TextField(_('High Scoring Spam Subject Text'),
                            default='{Definate Spam?}')
    warningisattachment = SelectField(_('Warning Is Attachment'),
                            choices=YES_NO,
                            default='yes')
    attachmentwarningfilename = TextField(_('Attachment Warning Filename'),
                            default='VirusWarning.txt')
    attachmentcharset = TextField(_('Attachment Encoding Charset'),
                            default='UTF-8')


class VirusSettings(Form):
    "Virus settings"
    virusscanners = SelectMultipleField(_('Virus Scanners'),
                            choices=list(VIRUS_SCANNERS))
    virusscannertimeout = IntegerField(_('Virus Scanner Timeout'),
                            default=300)
    deliverdisinfected = SelectField(_('Deliver Disinfected Files'),
                            choices=YES_NO,
                            default='yes')
    silentviruses = TextField(_('Silent Viruses'),
                            default='HTML-IFrame All-Viruses')
    deliversilent = SelectField(_('Still Deliver Silent Viruses'),
                            choices=YES_NO,
                            default='yes')
    nonforgingviruses = TextField(_('Non-Forging Viruses'))
    spamvirusheader = TextField(_('Spam-Virus Header'),
                            default='X-Baruwa-SpamVirus-Report:')
    spaminfected = TextField(_('Virus Names Which Are Spam'),
                            default='Sane*UNOFFICIAL HTML/* *Phish*')
    blockencrypted = SelectField(_('Block Encrypted Messages'),
                            choices=YES_NO,
                            default='yes')
    blockunencrypted = SelectField(_('Block Unencrypted Messages'),
                            choices=YES_NO,
                            default='yes')
    allowpasswordprotectedarchives = TextField(_('Allow Password-Protected Archives'))
    checkfilenamesinpasswordprotectedarchives = TextField(_('Check Filenames In Password-Protected Archives'))
    clamdusethreads = SelectField(_('Clamd Use Threads'),
                            choices=YES_NO,
                            default='yes')
    clamavspam = SelectField(_('ClamAV Full Message Scan'),
                            choices=YES_NO,
                            default='yes')
    fprotd6port = IntegerField(_('Fpscand Port'),
                            default=10200)
    # sophosallowederrors = TextField(_('Allowed Sophos Error Messages'))


class ContentSettings(Form):
    "Content settings"
    allowpartial = SelectField(_('Allow Partial Messages'),
                            choices=YES_NO,
                            default='no')
    allowexternal = SelectField(_('Allow External Message Bodies'),
                            choices=YES_NO,
                            default='no')
    phishingnumbers = SelectField(_('Also Find Numeric Phishing'),
                            choices=YES_NO,
                            default='yes')
    strictphishing = SelectField(_('Use Stricter Phishing Net'),
                            choices=YES_NO,
                            default='yes')
    phishinghighlight = SelectField(_('Highlight Phishing Fraud'),
                            choices=YES_NO,
                            default='yes')
    allowiframetags = SelectField(_('Allow IFrame Tags'),
                            choices=CONVERT,
                            default='convert')
    allowformtags = SelectField(_('Allow Form Tags'),
                            choices=CONVERT,
                            default='convert')
    allowscripttags = SelectField(_('Allow Script Tags'),
                            choices=CONVERT,
                            default='convert')
    allowwebbugtags = SelectField(_('Allow WebBugs'),
                            choices=CONVERT,
                            default='convert')
    webbugwhitelist = TextField(_('Ignored Web Bug Filenames'),
                            default='spacer pixel.gif pixel.png gap shim')
    webbugblacklist = TextField(_('Known Web Bug Servers'),
                            default='msgtag.com')
    webbugurl = TextField(_('Web Bug Replacement'),
                            default='http://www.baruwa.org/1x1spacer.gif')
    allowobjecttags = SelectField(_('Allow Object Codebase Tags'),
                            choices=CONVERT,
                            default='convert')
    stripdangeroustags = SelectField(_('Convert Dangerous HTML To Text'),
                            choices=YES_NO,
                            default='no')
    htmltotext = SelectField(_('Convert HTML To Text'),
                            choices=YES_NO,
                            default='no')
    archivesare = TextField(_('Archives Are'),
                            default='zip rar ole')
    allowfilenames = TextField(_('Allow Filenames'))
    denyfilenames = TextField(_('Deny Filenames'))
    allowfiletypes = TextField(_('Allow Filetypes'))
    allowfilemimetypes = TextField(_('Allow File MIME Types'))
    denyfiletypes = TextField(_('Deny Filetypes'))
    denyfilemimetypes = TextField(_('Deny File MIME Types'))
    aallowfilenames = TextField(_('Archives: Allow Filenames'))
    adenyfilenames = TextField(_('Archives: Deny Filenames'))
    aallowfiletypes = TextField(_('Archives: Allow Filetypes'))
    aallowfilemimetypes = TextField(_('Archives: Allow File MIME Types'))
    adenyfiletypes = TextField(_('Archives: Deny Filetypes'))
    adenyfilemimetypes = TextField(_('Archives: Deny File MIME Types'))


class ReportsSettings(Form):
    "Reports and responses settings"
    quarantineinfections = SelectField(_('Quarantine Infections'),
                            choices=YES_NO,
                            default='yes')
    quarantinesilent = SelectField(_('Quarantine Silent Viruses'),
                            choices=YES_NO,
                            default='no')
    quarantinemodifiedbody = SelectField(_('Quarantine Modified Body'),
                            choices=YES_NO,
                            default='no')
    keepspamarchiveclean = SelectField(_('Keep Spam And MCP Archive Clean'),
                            choices=YES_NO,
                            default='no')
    hideworkdir = SelectField(_('Hide Incoming Work Dir'),
                            choices=YES_NO,
                            default='yes')
    showscanner = SelectField(_('Include Scanner Name In Reports'),
                            choices=YES_NO,
                            default='no')


class NoticeSettings(Form):
    "Notice settings"
    warnsenders = SelectField(_('Notify Senders'),
                            choices=YES_NO,
                            default='yes')
    warnvirussenders = SelectField(_('Notify Senders Of Viruses'),
                            choices=YES_NO,
                            default='no')
    warnnamesenders = SelectField(_('Notify Senders Of Blocked Filenames Or Filetypes'),
                            choices=YES_NO,
                            default='yes')
    warnsizesenders = SelectField(_('Notify Senders Of Blocked Size Attachments'),
                            choices=YES_NO,
                            default='no')
    warnothersenders = SelectField(_('Notify Senders Of Other Blocked Content'),
                            choices=YES_NO,
                            default='yes')
    nosenderprecedence = TextField(_('Never Notify Senders Of Precedence'),
                            default='list bulk')
    sendnotices = SelectField(_('Send Notices'),
                            choices=YES_NO,
                            default='no')
    noticefullheaders = SelectField(_('Notices Include Full Headers'),
                            choices=YES_NO,
                            default='yes')
    hideworkdirinnotice = SelectField(_('Hide Incoming Work Dir in Notices'),
                            choices=YES_NO,
                            default='no')
    noticesignature = TextAreaField(_('Notice Signature'),
                            default='-- \nBaruwa\nEmail Security\n%website%')
    noticesfrom = TextField(_('Notices From'),
                            default='Baruwa')
    noticerecipient = TextField(_('Notices To'),
                            default='postmaster')
    localpostmaster = TextField(_('Local Postmaster'),
                            default='postmaster')


class SpamSettings(Form):
    "Spam settings"
    maxspamassassinsize = TextField(_('Max SpamAssassin Size'),
                            default='200k')
    spamassassinautowhitelist = SelectField(_('SpamAssassin Auto Whitelist'),
                            choices=YES_NO,
                            default='yes')
    spamassassintimeout = IntegerField(_('SpamAssassin Timeout'),
                            default=75)
    maxspamassassintimeouts = IntegerField(_('Max SpamAssassin Timeouts'),
                            default=10)
    satimeoutlen = IntegerField(_('SpamAssassin Timeouts History'),
                            default=30)
    checksaifonspamlist = SelectField(_('Check SpamAssassin If On Spam List'),
                            choices=YES_NO,
                            default='yes')
    sadecodebins = SelectField(_('Include Binary Attachments In SpamAssassin'),
                            choices=YES_NO,
                            default='no')
    spamstars = SelectField(_('Spam Score'),
                            choices=YES_NO,
                            default='yes')
    usesacache = SelectField(_('Cache SpamAssassin Results'),
                            choices=YES_NO,
                            default='yes')
    bayesrebuild = IntegerField(_('Rebuild Bayes Every'),
                            default=86400)
    bayeswait = SelectField(_('Wait During Bayes Rebuild'),
                            choices=YES_NO,
                            default='yes')
    # spamchecks = SelectField(_('Spam Checks'),
                            # choices=YES_NO, default='yes')
    spamlist = SelectMultipleField(_('Spam List'),
                            choices=list(SPAM_LISTS))
    spamdomainlist = SelectMultipleField(_('Spam Domain List'),
                            choices=list(SPAM_LISTS))
    normalrbls = IntegerField(_('Spam Lists To Be Spam'),
                            default=1)
    highrbls = IntegerField(_('Spam Lists To Reach High Score'),
                            default=3)
    spamlisttimeout = IntegerField(_('Spam List Timeout'),
                            default=10)
    maxspamlisttimeouts = IntegerField(_('Max Spam List Timeouts'),
                            default=7)
    rbltimeoutlen = IntegerField(_('Spam List Timeouts History'),
                            default=10)
    blacklistedishigh = SelectField(_('Definite Spam Is High Scoring'),
                            choices=YES_NO,
                            default='yes')
    whitelistmaxrecips = IntegerField(_('Ignore Spam Whitelist If Recipients Exceed'),
                            default=20)
    maxspamchecksize = IntegerField(_('Max Spam Check Size'),
                            default=150000)
    enablespambounce = SelectField(_('Enable Spam Bounce'),
                            choices=YES_NO,
                            default='no')
    bouncespamasattachment = SelectField(_('Bounce Spam As Attachment'),
                            choices=YES_NO,
                            default='yes')
    spamdetail = SelectField(_('Detailed Spam Report'),
                            choices=YES_NO,
                            default='yes')
    listsascores = SelectField(_('Include Scores In SpamAssassin Report'),
                            choices=YES_NO,
                            default='yes')
    includespamheader = SelectField(_('Always Include SpamAssassin Report'),
                            choices=YES_NO,
                            default='no')
    spamheader = TextField(_('Spam Header'),
                            default='X-Baruwa-SpamCheck:')
    spamstarsheader = TextField(_('Spam Score Header'),
                            default='X-Baruwa-SpamScore:')
    scoreformat = TextField(_('Spam Score Number Format'),
                            default='%d')
    spamstarscharacter = TextField(_('Spam Score Character'),
                            default='s')
    spamscorenotstars = SelectField(_('SpamScore Number Instead Of Stars'),
                            choices=YES_NO,
                            default='no')
    minstars = IntegerField(_('Minimum Stars If On Spam List'),
                            default=0)
    usewatermarking = SelectField(_('Use Watermarking'),
                            choices=YES_NO,
                            default='no')
    addmshmac = SelectField(_('Add Watermark'),
                            choices=YES_NO,
                            default='yes')
    checkmshmac = SelectField(_('Check Watermarks With No Sender'),
                            choices=YES_NO,
                            default='no')
    mshmacnull = SelectField(_('Treat Invalid Watermarks With No Sender as Spam'),
                            choices=WATERMARK_OPTIONS,
                            default='nothing')
    checkmshmacskip = SelectField(_('Check Watermarks To Skip Spam Checks'),
                            choices=YES_NO,
                            default='yes')
    mshmac = TextField(_('Watermark Secret'),
                            default='please change this to a secret pass phrase')
    mshmacvalid = IntegerField(_('Watermark Lifetime'),
                            default=604800)
    mshmacheader = TextField(_('Watermark Header'),
                            default='X-%org-name%-Baruwa-Watermark:')


class LoggingSettings(Form):
    "Logging settings"
    logfacility = SelectField(_('Syslog Facility'),
                            choices=SYSLOG_FACILITIES,
                            default='mail')
    logspeed = SelectField(_('Log Speed'),
                            choices=YES_NO,
                            default='no')
    logspam = SelectField(_('Log Spam'),
                            choices=YES_NO,
                            default='no')
    lognonspam = SelectField(_('Log Non Spam'),
                            choices=YES_NO,
                            default='no')
    logdelivery = SelectField(_('Log Delivery And Non-Delivery'),
                            choices=YES_NO,
                            default='no')
    logpermittedfilenames = SelectField(_('Log Permitted Filenames'),
                            choices=YES_NO,
                            default='no')
    logpermittedfiletypes = SelectField(_('Log Permitted Filetypes'),
                            choices=YES_NO,
                            default='no')
    logpermittedfilemimetypes = SelectField(_('Log Permitted File MIME Types'),
                            choices=YES_NO,
                            default='no')
    logsilentviruses = SelectField(_('Log Silent Viruses'),
                            choices=YES_NO,
                            default='no')
    loghtmltags = SelectField(_('Log Dangerous HTML Tags'),
                            choices=YES_NO,
                            default='no')
    logsaactions = SelectField(_('Log SpamAssassin Rule Actions'),
                            choices=YES_NO,
                            default='no')


settings_forms = {
    '1': GeneralSettings,
    '2': ProcessingSettings,
    '3': VirusSettings,
    '4': ContentSettings,
    '5': ReportsSettings,
    '6': NoticeSettings,
    '7': SpamSettings,
    '8': LoggingSettings
}


class SigForm(Form):
    "Domain signature"
    signature_type = SelectField(_('Signature type'),
                        choices=(('1', _('Text signature')),
                        ('2', _('HTML Signature')),),
                        default=1)
    signature_content = TextAreaField(_('Signature'),
                            [validators.Required(message=REQ_MSG)])
    enabled = BooleanField(_('Enabled'))


class DKIMForm(Form):
    "Enable/Disable DKIM signing"
    enabled = BooleanField(_('Enabled'))

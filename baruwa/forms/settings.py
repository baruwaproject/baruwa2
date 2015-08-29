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
"Settings forms"

from wtforms import BooleanField, validators, TextField
from wtforms import IntegerField, SelectField, TextAreaField
from wtforms import SelectMultipleField, HiddenField, DecimalField
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form, REQ_MSG, STATUS_DESC
from baruwa.lib.regex import HOST_OR_IPV4_RE, SCANNER_NAME_RE, \
    DOM_RE, MAIL_X_HEADER_RE, UNZIP_FILENAMES_RE, MAX_SPAMASSASSIN_RE, \
    IPV4_RE

ADDR_TYPES = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
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
CONVERT = (('disarm', _('Disarm')),
            ('yes', _('Yes')),
            ('no', _('No')))
MTAS = (('exim', 'Exim'),
    ('sendmail', 'Sendmail'),
    ('postfix', 'Postfix'),
    ('zmailer', 'Zmailer'))
VIRUS_SCANNERS = (
    ('auto', _('Auto detect')),
    ('f-protd-6', 'F-prot Daemon 6'),
    ('clamd', 'Clamav Daemon'),
    ('f-secure', 'F-Secure'),
    ('esets', 'Esets'),
    ('none', 'None'))
SPAM_LISTS = (
    ('BARUWA-RBL', 'rbl.baruwa.net'),
    ('SEM', 'bl.spameatingmonkey.net'),
    ('HOSTKARMA-RBL', 'hostkarma.junkemailfilter.com'),
    ('spamhaus-ZEN', 'zen.spamhaus.org.'),
    ('spamcop.net', 'bl.spamcop.net.'),
    ('SORBS-DNSBL', 'dnsbl.sorbs.net.'),
    ('CBL', 'cbl.abuseat.org.'))
SPAM_DOMAIN_LISTS = (
    ('BARUWA-DBL', 'dbl.rbl.baruwa.net'),
    ('HOSTKARMA-DBL', 'hostkarma.junkemailfilter.com'),
    ('spamhaus-ZEN', 'zen.spamhaus.org.'))
WATERMARK_OPTIONS = (
    ("nothing", _('Do nothing')),
    ('delete', _("Delete")),
    ('spam', _("Flag as probable spam")),
    ("high-scoring spam", _('Flag as definate spam')),
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

RULE_ACTIONS = (
    ('deny', _('Deny')),
    ('deny+delete', _('Deny and Delete')),
    ('rename', _('Rename')),
    ('renameto', _('Rename To')),
    ('email-addresses', _('Email To')),
    ('allow', _('Allow')),
)

ARCHIVE_RULE_ACTIONS = (
    ('deny', _('Deny')),
    ('deny+delete', _('Deny and Delete')),
    ('email-addresses', _('Email To')),
    ('allow', _('Allow')),
)

SPAM_VIRII = ('Sanesecurity.Spam*UNOFFICIAL '
            'Sanesecurity.Jurlbl*UNOFFICIAL '
            'HTML/* *Phish* '
            '*Suspected-phishing_safebrowsing*')

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
    org_name = TextField(_('Sitename'), default='BARUWA',
                        description=_("""Enter a short identifying name
                        for your organisation below, this is used to
                        make the X-BaruwaFW headers unique for your
                        organisation.
                        Multiple servers within one site should use an
                        identical value here. Don't put "." or "_" in
                        this setting.
                        """),
                        validators=[validators.Regexp(SCANNER_NAME_RE,
                        message=_('Name must not contain "." or "_"'))])
    org_fullname = TextField(_('Your Organisation Name'),
                        default='BARUWA MAILFW',
                        description=_("""Enter the full name of your
                        organisation below, this is used in the signature
                        placed at the bottom of report messages sent by
                        the system."""))
    org_website = TextField(_('Organisation website'),
                            default='www.baruwa.com',
                            description=_("""Enter the location of your
                            organisation's web site below., this is used in
                            the signature placed at the bottom of report
                            messages sent by the system."""),
                            validators=[validators.Regexp(DOM_RE,
                            message=_('Invalid Domain name'))])
    children = IntegerField(_('Max Children'),
                            default=5,
                            description=_("""How many Scanner processes
                            do you want to run at a time? As a rough guide,
                            try 5 children per CPU. Note that each child
                            takes just over 20MB."""))
    queuescaninterval = IntegerField(_('Queue Scan Interval'),
                            default=6,
                            description=_("""How often (in seconds) should
                            each process check the incoming mail queue. If
                            you have a quiet mail server, you might want to
                            increase this value so it causes less load on
                            your server, at the cost of slightly increasing
                            the time taken for an average message to be
                            processed."""))
    restartevery = IntegerField(_('Restart Every'),
                            default=7200,
                            description=_("""To avoid resource leaks,
                            re-start periodically. Forces a re-read of all
                            the configuration files too, so new updates to
                            the various lists are read frequently."""))
    usedefaultswithmanyrecips = SelectField(_('Use Default Rules With Multiple Recipients'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""This controls the behaviour when a
                            rule is checking the "To:" addresses.
                            If this option is set to "yes", then the following
                            happens when checking the ruleset:
                               a) 1 recipient. Same behaviour as normal.
                               b) Several recipients, but all in the same
                                  domain (domain.com for example).
                                  The rules are checked for one that matches
                            	  the string "*@domain.com".
                               c) Several recipients, not all in the same
                                  domain. The rules are checked for one that
                                  matches the string "*@*"."""))
    getipfromheader = SelectField(_('Read IP Address From Received Header'),
                            choices=YES_NO,
                            default='no',
                            description=_("""When working out from IP address the
                            message was sent from,
                            no ==> use the SMTP client address, ie. the address of
                            the system talking to the MailScanner server. This is
                            the normal setting.
                            yes ==> use the first IP address contained in the first
                            "Received:" header at the top of the email message's
                            headers."""))
    debug = SelectField(_('Debug'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Set Debug to "yes" to stop it
                            running as a daemon and just process one batch
                            of messages and then exit."""))
    debugspamassassin = SelectField(_('Debug SpamAssassin'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Set Debug to "yes" to debug
                            SpamAssassin"""))
    deliverinbackground = SelectField(_('Deliver In Background'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""When attempting delivery of
                            outgoing messages, should we do it in the
                            background or wait for it to complete? The
                            danger of doing it in the background is that
                            the machine load goes ever upwards while all the
                            slow sending processes run to completion. However,
                            running it in the foreground may cause the mail
                            server to run too slowly."""))
    deliverymethod = SelectField(_('Delivery Method'),
                            choices=[('batch', 'Batch'), ('queue', 'Queue')],
                            default='batch',
                            description=_("""Attempt immediate delivery of
                            messages, or just place them in the outgoing
                            queue for the sending process to deliver when
                            it wants to?
                            * batch -- attempt delivery of messages, in
                            batches of up to 20 at once.
                            * queue -- just place them in the queue and
                            let the sending process find them."""))
    syntaxcheck = SelectField(_('Automatic Syntax Check'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to automatically
                            do a syntax check of the configuration files
                            when the Scanner is started up?"""))
    minimumcodestatus = SelectField(_('Minimum Code Status'),
                            choices=CODE_SUPPORT,
                            default='supported',
                            description=_("""Don't set it to anything
                            other than "supported" """))


class ProcessingSettings(Form):
    "Processing settings"
    maxunscannedbytes = IntegerField(_('Max Unscanned Bytes Per Scan'),
                            default=100000000,
                            description=_("""Total size of unscanned messages
                            to deliver in Bytes"""))
    maxdirtybytes = IntegerField(_('Max Unsafe Bytes Per Scan'),
                            default=50000000,
                            description=_("""Total size of potentially
                            infected messages to unpack and scan in Bytes"""))
    maxunscannedmessages = IntegerField(_('Max Unscanned Messages Per Scan'),
                            default=30,
                            description=_("""Total number of unscanned messages
                            to deliver"""))
    maxdirtymessages = IntegerField(_('Max Unsafe Messages Per Scan'),
                            default=30,
                            description=_("""Total number of potentially
                            infected messages to unpack and scan"""))
    criticalqueuesize = IntegerField(_('Max Normal Queue Size'),
                            default=800,
                            description=_("""If more messages are found
                            in the queue than this, then switch to an
                            "accelerated" mode of processing messages.
                            This will cause it to stop scanning messages
                            in strict date order, but in the order it finds
                            them in the queue. If your queue is bigger than
                            this size a lot of the time, then some messages
                            could be greatly delayed. So treat this option as
                            "in emergency only"""))
    procdbattempts = IntegerField(_('Maximum Processing Attempts'),
                            default=6,
                            description=_("""Limit the number of attempts
                            made at processing any particular message."""))
    maxparts = IntegerField(_('Maximum Attachments Per Message'),
                            default=200,
                            description=_("""The maximum number of attachments
                            allowed in a message before it is considered to be
                            an error."""))
    expandtnef = SelectField(_('Expand TNEF'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Expand TNEF attachments, This
                            should be yes"""))
    replacetnef = SelectField(_('Use TNEF Contents'),
                            choices=TNEF_ACTIONS,
                            default='replace',
                            description=_("""When the TNEF (winmail.dat)
                            attachments are expanded, should the attachments
                            contained in there be added to the list of
                            attachments in the message?
                            If you set this to "add" or "replace" then
                            recipients of messages sent in
                            "Outlook Rich Text Format" (TNEF) will be able
                            to read the attachments if they are not using
                            Microsoft Outlook.

                            * no => Leave winmail.dat TNEF attachments alone.
                            * add => Add the contents of winmail.dat as extra
                               attachments, but also still include the
                               winmail.dat file itself. This will result in
                               TNEF messages being doubled in size.
                            * replace => Replace the winmail.dat TNEF
                              attachment with the files it contains, and
                              delete the original winmail.dat file itself.
                              This means the message stays the same size,
                              but is usable by non-Outlook recipients."""))
    deliverunparsabletnef = SelectField(_('Deliver Unparsable TNEF'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Some versions of Microsoft
                            Outlook generate unparsable Rich Text
                            format attachments. Do we want to deliver
                            these bad attachments anyway?
                            Setting this to yes introduces the slight risk
                            of a virus getting through, but if you have a
                            lot of troubled Outlook users you might need to
                            set this to yes."""))
    tneftimeout = IntegerField(_('TNEF Timeout'),
                            default=120,
                            description=_("""The maximum length of time the
                            TNEF Expander is allowed to run for 1 message
                            (in seconds)"""))
    filetimeout = IntegerField(_('File Timeout'),
                            default=20,
                            description=_("""The maximum length of time the
                            file checking command is allowed to run for 1
                            batch of messages
                            (in seconds)"""))
    gunziptimeout = IntegerField(_('Gunzip Timeout'),
                            default=50,
                            description=_("""The maximum length of time the
                            gunzip command is allowed to run to expand
                            1 attachment file (in seconds)."""))
    unrartimeout = IntegerField(_('Unrar Timeout'),
                            default=50,
                            description=_("""The maximum length of time the
                            unrar command is allowed to run to expand
                            1 attachment file (in seconds)."""))
    maxzipdepth = IntegerField(_('Maximum Archive Depth'),
                            default=2,
                            description=_("""The maximum depth to which
                            zip archives, rar archives and Microsoft Office
                            documents will be unpacked, to allow for checking
                            filenames and filetypes within zip and rar archives
                            and embedded within Office documents."""))
    findarchivesbycontent = SelectField(_('Find Archives By Content'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Find zip archives by filename or
                            by file contents? Finding them by content is a far
                            more reliable way of finding them"""))
    unpackole = SelectField(_('Unpack Microsoft Documents'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to unpack Microsoft
                            "OLE" documents, such as *.doc, *.xls and *.ppt
                            documents? This will extract any files which have
                            been hidden by being embedded in these documents."""))
    zipattachments = SelectField(_('Zip Attachments'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Should the attachments be compressed
                            and put into a single zip file?"""))
    attachzipname = TextField(_('Attachments Zip Filename'),
                            default='MessageAttachments.zip',
                            description=_("""If the attachments are to be
                            compressed into a single zip file, this is the
                            filename of the zip file."""))
    attachzipminsize = IntegerField(_('Attachments Min Total Size To Zip'),
                            default=100000,
                            description=_("""If the original total size of all
                            the attachments to be compressed is less than this
                            number of bytes, they will not be zipped at all."""))
    attachzipignore = TextField(_('Attachment Extensions Not To Zip'),
                            default='.zip .rar .gz .tgz .mpg .mpe .mpeg .mp3 .rpm',
                            description=_("""Attachments whose filenames end in
                            these strings will not be zipped."""))
    addtextofdoc = SelectField(_('Add Text Of Doc'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to add the plain text
                            contents of Microsoft Word documents?"""))
    antiwordtimeout = IntegerField(_('Antiword Timeout'),
                            default=50,
                            description=_("""The maximum length of time the
                            "antiword" command is allowed to run for 1
                            Word document (in seconds)"""))
    unzipmaxmembers = IntegerField(_('Unzip Maximum Files Per Archive'),
                            default=0,
                            description=_("""This is the maximum number of
                            files in each archive. If an archive contains
                            more files than this, we do not try to unpack
                            it at all. Set this value to 0 to disable this
                            feature."""))
    unzipmaxsize = IntegerField(_('Unzip Maximum File Size'),
                            default=50000,
                            description=_("""The maximum unpacked size of
                            each file in an archive. Bigger than this, and
                            the file will not be unpacked. Setting this
                            value to 0 will disable this feature."""))
    unzipmembers = TextField(_('Unzip Filenames'),
                            default='*.txt *.ini *.log *.csv',
                            description=_("""The list of filename extensions
                            that should be unpacked."""),
                            validators=[validators.Regexp(UNZIP_FILENAMES_RE,
                            message=_('Invalid Format entered'))])
    unzipmimetype = TextField(_('Unzip MimeType'),
                            default='text/plain',
                            description=_("""The Default MIME type of the files
                            unpacked from the archive."""))
    mailheader = TextField(_('Mail Header'),
                            default='X-%org-name%-BaruwaFW:',
                            description=_("""Add this extra header to all mail
                            as it is processed. This *must* include the colon
                            ":" at the end."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    infoheader = TextField(_('Information Header'),
                            default='X-%org-name%-BaruwaFW-Information:',
                            description=_("""Add this extra header to all
                            mail as it is processed. The contents is set by
                            "Information Header Value" and is intended for
                            you to be able to insert a help URL for your
                            users."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    addenvfrom = SelectField(_('Add Envelope From Header'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to add the
                            Envelope-From: header? This is very useful
                            for tracking where spam came from as it
                            contains the envelope sender address."""))
    addenvto = SelectField(_('Add Envelope To Header'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to add the
                            Envelope-To: header? This can be useful for
                            tracking spam destinations, but should be
                            used with care due to possible privacy
                            concerns with the use of Bcc: headers by users.
                            """))
    # envfromheader = TextField(_('Envelope From Header'),
    #                         default='X-%org-name%-Envelope-From:')
    envtoheader = TextField(_('Envelope To Header'),
                            default='X-%org-name%-BaruwaFW-Envelope-To:',
                            description=_("""This is the name of the
                            Envelope To header"""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    idheader = TextField(_('ID Header'),
                            default='X-%org-name%-BaruwaFW-ID:',
                            description=_("""Setting this adds the
                            Scanner message id number to a header
                            in the message."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    ipverheader = TextField(_('IP Protocol Version Header'),
                            default='X-%org-name%-BaruwaFW-IP-Protocol:',
                            description=_("""Was this message transmitted
                            using IPv6 or IPv4 in its last hop?"""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    cleanheader = TextField(_('Clean Header Value'),
                            default='Found to be clean',
                            description=_("""Set the "Mail Header" to
                            this for clean messages"""))
    dirtyheader = TextField(_('Infected Header Value'),
                            default='Found to be infected',
                            description=_("""Set the "Mail Header" to
                            this for infected messages"""))
    disinfectedheader = TextField(_('Disinfected Header Value'),
                            default='Disinfected',
                            description=_("""Set the "Mail Header" to
                            this for disinfected messages"""))
    infovalue = TextField(_('Information Header Value'),
                            default='Please contact %org-long-name% for more information',
                            description=_("""Set the "Information Header"
                            to this value."""))
    multipleheaders = SelectField(_('Multiple Headers'),
                            choices=list(HEADER_ACTIONS),
                            default='add',
                            description=_("""What to do when you get
                            several Scanner headers in one message,
                            from multiple Scanning servers. Values are
                            * "append"  : Append the new data to the existing header
                            * "add"     : Add a new header
                            * "replace" : Replace the old data with the new data"""))
    newheadersattop = SelectField(_('Place New Headers At Top Of Message'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""To avoid breaking DKIM signatures,
                            you *must* set to yes"""))
    hostname = TextField(_('Hostname'),
                            default='the %org-name% ($HOSTNAME) Baruwa',
                            description=_("""Name of this host, or a name like
                            "the Scanner" if you want to hide the real hostname.
                            It is used in the Help Desk note contained in the
                            warnings sent to users."""))
    signalreadyscanned = SelectField(_('Sign Messages Already Processed'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If this is "no", then
                            (as far as possible) messages which have already
                            been processed by another Scanning server will
                            not have the clean signature added to the message.
                            This prevents messages getting many copies of the
                            signature as they flow through your site."""))
    allowmultsigs = SelectField(_('Allow Multiple HTML Signatures'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If this option is set to "no",
                            then messages are not signed multiple times"""))
    isareply = TextField(_('Dont Sign HTML If Headers Exist'),
                            description=_("""If any of these headers exist,
                            then the message is actually a reply and so we
                            may not want to sign it with an HTML signature."""))
    markinfectedmessages = SelectField(_('Mark Infected Messages'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Add the "Inline HTML Warning" or
                            "Inline Text Warning" to the top of messages that
                            have had attachments removed from them?"""))
    signunscannedmessages = SelectField(_('Mark Unscanned Messages'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Mark Unscanned Messages"""))
    unscannedheader = TextField(_('Unscanned Header Value'),
                            default='Not scanned: please contact your %org-long-name% for details',
                            description=_("""This is the text used by the
                            "Mark Unscanned Messages" option above."""))
    removeheaders = TextField(_('Remove These Headers'),
                            default='X-Mozilla-Status: X-Mozilla-Status2:',
                            description=_("""If any of these headers are
                            included in a a message, they will be deleted."""))
    delivercleanedmessages = SelectField(_('Deliver Cleaned Messages'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to deliver
                            messages once they have been cleaned of any
                            infections ?"""))
    scannedmodifysubject = SelectField(_('Scanned Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""When the message has been
                            scanned but no other subject line changes
                            #have happened, do you want modify the
                            subject line?
                            This can be 1 of 4 values:
                            * no => Do not modify the subject line, or
                            * start => Add text to the start of the subject line, or
                            * end => Add text to the end of the subject line, or
                            * yes => Add text to the end of the subject line."""))
    scannedsubjecttext = TextField(_('Scanned Subject Text'),
                            default='{Scanned}',
                            description=_("""This is the text to add
                            to the start/end of the subject line if the
                            "Scanned Modify Subject" option is set."""))
    virusmodifysubject = SelectField(_('Virus Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If the message contained a
                            virus, do you want to modify the subject line?"""))
    virussubjecttext = TextField(_('Virus Subject Text'),
                            default='{Virus?}',
                            description=_("""This is the text to add to
                            the start of the subject if the
                            "Virus Modify Subject" option is set."""))
    namemodifysubject = SelectField(_('Filename Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If an attachment triggered
                            a filename check, but there was nothing
                            else wrong with the message, do you want
                            to modify the subject line?"""))
    namesubjecttext = TextField(_('Filename Subject Text'),
                            default='{Filename?}',
                            description=_("""This is the text to add
                            to the start of the subject if the
                            "Filename Modify Subject" option is set."""))
    contentmodifysubject = SelectField(_('Content Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If an attachment triggered
                            a content check, but there was nothing
                            else wrong with the message, do you
                            want to modify the subject line?"""))
    contentsubjecttext = TextField(_('Content Subject Text'),
                            default='{Dangerous Content?}',
                            description=_("""This is the text to add
                            to the start of the subject if the
                            "Content Modify Subject" option is set."""))
    sizemodifysubject = SelectField(_('Size Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If an attachment or the
                            entire message triggered a size check, but
                            there was nothing else wrong with the message,
                            do you want to modify the subject line?"""))
    sizesubjecttext = TextField(_('Size Subject Text'),
                            default='{Allowed Message Size Exceeded}',
                            description=_("""This is the text to add to
                            the start of the subject if the
                            "Size Modify Subject" option is set."""))
    disarmmodifysubject = SelectField(_('Disarmed Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If HTML tags in the message
                            were "disarmed", do you want to modify the
                            subject line?"""))
    disarmsubjecttext = TextField(_('Disarmed Subject Text'),
                            default='{Message Disarmed}',
                            description=_("""This is the text to add to
                            the start of the subject if the
                            "Disarmed Modify Subject" option is set."""))
    tagphishingsubject = SelectField(_('Phishing Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If a potential phishing attack
                            is found in the message, do you want to
                            modify the subject line?"""))
    phishingsubjecttag = TextField(_('Phishing Subject Text'),
                            default='{Suspected Fraud?}',
                            description=_("""This is the text to add to the
                            start of the subject if the "Phishing
                            Modify Subject" option is set."""))
    spammodifysubject = SelectField(_('Spam Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""If the message is spam, do you
                            want to modify the subject line?"""))
    spamsubjecttext = TextField(_('Spam Subject Text'),
                            default='{Probable Spam?}',
                            description=_("""This is the text to add to the
                            start of the subject if the "Spam Modify Subject"
                            option is set."""))
    highspammodifysubject = SelectField(_('High Scoring Spam Modify Subject'),
                            choices=START_END,
                            default='no',
                            description=_("""This is just like the
                            "Spam Modify Subject" option above, except that
                            it applies when the message is higher than the
                            "Definate Spam Score" value."""))
    highspamsubjecttext = TextField(_('High Scoring Spam Subject Text'),
                            default='{Definete Spam?}',
                            description=_("""This is the text to add to the
                            start of the subject if the
                            "High Scoring Spam Modify Subject" option is set."""))
    warningisattachment = SelectField(_('Warning Is Attachment'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""When an infection or attachment is
                            replaced by a plain-text warning, should the
                            warning be in an attachment? If "no" then it
                            will be placed in-line."""))
    attachmentwarningfilename = TextField(_('Attachment Warning Filename'),
                            default='VirusWarning.txt',
                            description=_("""When an infection or attachment
                            is replaced by a plain-text warning, and that
                            warning is an attachment, this is the filename of
                            the new attachment."""))
    attachmentcharset = TextField(_('Attachment Encoding Charset'),
                            default='UTF-8',
                            description=_("""What character set do you want
                            to use for the attachment that replaces infections?
                            Do not change this unless you know what you are
                            doing."""))


class VirusSettings(Form):
    "Virus settings"
    virusscanners = SelectMultipleField(_('Virus Scanners'),
                            choices=list(VIRUS_SCANNERS),
                            default=['auto'],
                            description=_("""Which Secondary Virus Scanning
                            package to use? Set to none if you do not have a
                            second Anti-Virus Package ClamAV scanning takes
                            place at SMTP time by default."""))
    virusscannertimeout = IntegerField(_('Virus Scanner Timeout'),
                            default=300,
                            description=_("""The maximum length of time the
                            secondary virus scanner is allowed to run
                            for 1 batch of messages (in seconds)"""))
    deliverdisinfected = SelectField(_('Deliver Disinfected Files'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Should the Scanner attempt to
                            disinfect infected attachments and then deliver
                            the clean ones. "Disinfection" involves removing
                            viruses from files (such as removing macro viruses
                            from documents)."""))
    silentviruses = TextField(_('Silent Viruses'),
                            default='HTML-IFrame All-Viruses',
                            description=_("""Strings listed here will be
                            searched for in the output of the virus scanners.
                            It is used to list which viruses should be handled
                            differently from other viruses."""))
    deliversilent = SelectField(_('Still Deliver Silent Viruses'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Deliver (after cleaning) messages
                            that contained viruses listed in the above option
                            ("Silent Viruses") to the recipient?"""))
    noisyviruses = TextField(_('Non-Forging Viruses'),
                            description=_("""Strings listed here will be searched
                            for in the output of the virus scanners.
                            It works to achieve the opposite effect of the
                            "Silent Viruses" listed above."""))
    spamvirusheader = TextField(_('Spam-Virus Header'),
                            default='X-%org-name%-BaruwaFW-SpamVirus-Report:',
                            description=_("""Some virus scanners use their
                            signatures to detect spam as well as viruses.
                            These "viruses" are called "spam-viruses".
                            When they are found the following header will
                            be added to your message before it is passed to
                            SpamAssassin, listing all the "spam-viruses"
                            that were found as a comma-separated list."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    spaminfected = TextField(_('Virus Names Which Are Spam'),
                            default=SPAM_VIRII,
                            description=_("""This defines which virus reports
                            from your virus scanners are really the names of
                            "spam-viruses" as described in the "Spam-Virus Header"
                            option above. This is a space-separated list of
                            strings which can contain "*" wildcards to mean
                            "any string of characters", and which will match the
                            whole name of the virus reported by your virus scanner.
                            So for example "HTML/*" will match all virus names
                            which start with the string "HTML/". The supplied
                            example is suitable for F-Prot6 and the SaneSecurity
                            databases for ClamAV. The test is case-sensitive."""))
    blockencrypted = SelectField(_('Block Encrypted Messages'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Should encrypted messages be blocked?
                            This is useful if you are wary about your users sending
                            encrypted messages outside your organization."""))
    blockunencrypted = SelectField(_('Block Unencrypted Messages'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Should unencrypted messages be blocked?
                            This could be used to ensure all your users send messages
                            outside your company encrypted to avoid snooping."""))
    allowpasszips = SelectField(_('Allow Password-Protected Archives'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Should archives which contain any
                            password-protected files be allowed?"""))
    checkppafilenames = SelectField(
                            _('Check Filenames In Password-Protected Archives'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Normally, you can still get the
                            filenames out of a password-protected archive,
                            despite the encryption. So by default filename
                            checks are still done on these files. However,
                            some people want to suppress this checking as
                            they allow a few people to receive password-protected
                            archives that contain things such as .exe's as part of
                            their business needs. This option can be used to
                            suppress filename checks inside password-protected
                            archives."""))
    clamdusethreads = SelectField(_('Clamd Use Threads'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If MailScanner is running on a
                            system with more then 1 CPU core (or more than 1 CPU)
                            then you can set "Clamd Use Threads" to "yes" to
                            speed up the scanning, otherwise there is no advantage
                            and it should be set to "no"."""))
    clamavspam = SelectField(_('ClamAV Full Message Scan'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Setting this option to "yes", each
                            entire message is written out to the scanning area,
                            enabling spam signatures to work reliably."""))
    fprotd6port = IntegerField(_('Fpscand Port'),
                            default=10200,
                            description=_("""This is the port number used by the
                            local fpscand daemon. 10200 is the default value used
                            by the F-Prot 6 installation program, and so should
                            be correct."""))
    # sophosallowederrors = TextField(_('Allowed Sophos Error Messages'))


class ContentSettings(Form):
    "Content settings"
    allowpartial = SelectField(_('Allow Partial Messages'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to allow partial messages,
                            which only contain a fraction of the attachments, not
                            the whole thing? There is absolutely no way to scan these
                            "partial messages" properly for infections, as the Scanner
                            never sees all of the attachment at the same time. Enabling
                            this option can allow infections through."""))
    allowexternal = SelectField(_('Allow External Message Bodies'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to allow messages whose body
                            is stored somewhere else on the internet, which is downloaded
                            separately by the user's email package?
                            There is no way to guarantee that the file fetched by the
                            user's email package is free from infections, as the Scanner
                            never sees it."""))
    phishingnumbers = SelectField(_('Also Find Numeric Phishing'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""While detecting "Phishing" attacks, do you
                            also want to point out links to numeric IP addresses. Genuine
                            links to totally numeric IP addresses are very rare, so this
                            option is set to "yes" by default."""))
    strictphishing = SelectField(_('Use Stricter Phishing Net'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""If this is set to yes, then most of the URL
                            in a link must match the destination address it claims to
                            take you to. This is the default as it is a much stronger
                            test and is very hard to maliciously avoid."""))
    phishinghighlight = SelectField(_('Highlight Phishing Fraud'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""If a phishing fraud is detected, do you want
                            to highlight the tag with a message stating that the link may
                            be to a fraudulent web site."""))
    allowiframetags = SelectField(_('Allow IFrame Tags'),
                            choices=CONVERT,
                            default='disarm',
                            description=_("""Do you want to allow <IFrame> tags in email
                            messages? This is not a good idea as it allows various
                            Microsoft Outlook security vulnerabilities to remain unprotected,
                            but if you have a load of mailing lists sending them,
                            then you will want to allow them to keep your users happy.
                            * yes => Allow these tags to be in the message
                            * no  => Ban messages containing these tags
                            * convert  => Allow these tags, but stop these tags from
                            working"""))
    allowformtags = SelectField(_('Allow Form Tags'),
                            choices=CONVERT,
                            default='disarm',
                            description=_("""Do you want to allow <Form> tags in email
                            messages? This is a bad idea as these are used as scams to
                            pursuade people to part with credit card information and
                            other personal data.
                            * yes => Allow these tags to be in the message
                            * no  => Ban messages containing these tags
                            * convert  => Allow these tags, but stop these tags from
                            working"""))
    allowscripttags = SelectField(_('Allow Script Tags'),
                            choices=CONVERT,
                            default='disarm',
                            description=_("""Do you want to allow <Script> tags in
                            email messages? This is a bad idea as these are used to
                            exploit vulnerabilities in email applications and
                            web browsers.
                            * yes => Allow these tags to be in the message
                            * no  => Ban messages containing these tags
                            * convert  => Allow these tags, but stop these tags
                            from working"""))
    allowwebbugtags = SelectField(_('Allow WebBugs'),
                            choices=CONVERT,
                            default='disarm',
                            description=_("""Do you want to allow <Img> tags with
                            very small images in email messages? This is a bad
                            idea as these are used as 'web bugs' to find out if
                            a message has been read. It is not dangerous, it is
                            just used to make you give away information.
                            * yes => Allow these tags to be in the message
                            * no  => Ban messages containing these tags
                            * convert  => Allow these tags, but stop these tags
                            from working"""))
    webbugwhitelist = TextField(_('Ignored Web Bug Filenames'),
                            default='spacer pixel.gif pixel.png gap shim',
                            description=_("""This is a list of filenames
                            (or parts of filenames) that may appear in
                            the filename of a web bug URL. They are only
                            checked in the filename, not any directories or
                            hostnames in the URL of the possible web bug.
                            If it appears, then the web bug is assumed to
                            be a harmless "spacer" for page layout purposes
                            and not a real web bug at all. It should be a
                            space- and/or comma-separated list of filename
                            parts."""))
    webbugblacklist = TextField(_('Known Web Bug Servers'),
                            default='msgtag.com',
                            description=_("""This is a list of server names
                            (or parts of) which are known to host web bugs.
                            All images from these hosts will be replaced by
                            the "Web Bug Replacement" defined below."""))
    webbugurl = TextField(_('Web Bug Replacement'),
                            default='https://datafeeds.baruwa.com/1x1spacer.gif',
                            description=_("""When a web bug is found, what
                            image do you want to replace it with? By replacing
                            it with a real image, the page layout still works
                            properly, so the formatting and layout of the
                            message is correct. The default is a harmless
                            untracked 1x1 pixel transparent image."""))
    allowobjecttags = SelectField(_('Allow Object Codebase Tags'),
                            choices=CONVERT,
                            default='disarm',
                            description=_("""Do you want to allow
                            <Object Codebase=...> or <Object Data=...> tags
                            in email messages?
                            This is a bad idea as it leaves you unprotected
                            against various Microsoft-specific security
                            vulnerabilities. But if your users demand it,
                            you can do it.
                            * yes => Allow these tags to be in the message
                            * no  => Ban messages containing these tags
                            * convert  => Allow these tags, but stop these tags
                            from working"""))
    stripdangeroustags = SelectField(_('Convert Dangerous HTML To Text'),
                            choices=YES_NO,
                            default='no',
                            description=_("""When set to "yes", then the HTML
                            message will be converted to plain text."""))
    htmltotext = SelectField(_('Convert HTML To Text'),
                            choices=YES_NO,
                            default='no',
                            description=_("""When set to "yes", then the HTML
                            message will be converted to plain text."""))
    archivesare = TextField(_('Archives Are'),
                            default='zip rar ole',
                            description=_("""What sort of attachments are
                            considered to be archives?"""))
    # allowfilenames = TextField(_('Allow Filenames'),
    #                         description=_("""Allow any attachment filenames
    #                         matching any of the patterns listed here.
    #                         Example: \.txt$ \.pdf$"""))
    # denyfilenames = TextField(_('Deny Filenames'),
    #                         description=_("""Deny any attachment filenames
    #                         matching any of the patterns listed here.
    #                         Example: \.com$ \.exe$ \.cpl$ \.pif$"""))
    # allowfiletypes = TextField(_('Allow Filetypes'),
    #                         description=_("""Allow any attachment filetypes
    #                         matching any of the patterns listed here.
    #                         Example: script postscript"""))
    # allowfilemimetypes = TextField(_('Allow File MIME Types'),
    #                         description=_("""Allow any attachment MIME types
    #                         matching any of the patterns listed here.
    #                         Example: text/plain text/html"""))
    # denyfiletypes = TextField(_('Deny Filetypes'),
    #                         description=_("""Deny any attachment filetypes
    #                         matching any of the patterns listed here.
    #                         Example: executable MPEG"""))
    # denyfilemimetypes = TextField(_('Deny File MIME Types'),
    #                         description=_("""Deny any attachment MIME types
    #                         matching any of the patterns listed here.
    #                         Example: dosexec"""))
    # aallowfilenames = TextField(_('Archives: Allow Filenames'),
    #                         description=_("""Allow any archive content filenames
    #                         matching any of the patterns listed here.
    #                         Example: \.txt$ \.pdf$"""))
    # adenyfilenames = TextField(_('Archives: Deny Filenames'),
    #                         description=_("""Deny any archive content filenames
    #                         matching any of the patterns listed here.
    #                         Example: \.txt$ \.pdf$"""))
    # aallowfiletypes = TextField(_('Archives: Allow Filetypes'),
    #                         description=_("""Allow any attachment filetypes
    #                         found inside archives and matching any of the
    #                         patterns listed here.
    #                         Example: script postscript"""))
    # aallowfilemimetypes = TextField(_('Archives: Allow File MIME Types'),
    #                         description=_("""Allow any attachment MIME types
    #                         found inside archives and matching any of the
    #                         patterns listed here.
    #                         Example: executable MPEG"""))
    # adenyfiletypes = TextField(_('Archives: Deny Filetypes'),
    #                         description=_("""Deny any attachment filetypes
    #                         found inside archives and matching any of the
    #                         patterns listed here.
    #                         Example: script postscript"""))
    # adenyfilemimetypes = TextField(_('Archives: Deny File MIME Types'),
    #                         description=_("""Deny any attachment MIME types
    #                         found inside archives and matching any of the
    #                         patterns listed here.
    #                         Example: executable MPEG"""))


class ReportsSettings(Form):
    "Reports and responses settings"
    quarantineinfections = SelectField(_('Quarantine Infections'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to store copies of
                            the infected attachments and messages?"""))
    quarantinesilent = SelectField(_('Quarantine Silent Viruses'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to store copies of
                            "Silent Viruses" ?"""))
    quarantinemodifiedbody = SelectField(_('Quarantine Modified Body'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to store copies of
                            messages which have been disarmed by
                            having their HTML modified?"""))
    keepspamarchiveclean = SelectField(_('Keep Spam And MCP Archive Clean'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to stop any
                            virus-infected spam getting into the spam
                            quarantine ?"""))
    hideworkdir = SelectField(_('Hide Incoming Work Dir'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Hide the directory path from
                            all virus scanner reports sent to users."""))
    showscanner = SelectField(_('Include Scanner Name In Reports'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Include the name of the virus
                            scanner in each of the scanner reports."""))


class NoticeSettings(Form):
    "Notice settings"
    warnsenders = SelectField(_('Notify Senders'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to notify the people
                            who sent you messages containing infections or
                            badly-named filenames?"""))
    warnvirussenders = SelectField(_('Notify Senders Of Viruses'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If "Notify Senders" is set to yes,
                            do you want to notify people who sent you messages
                            containing infections?"""))
    warnnamesenders = SelectField(_('Notify Senders Of Blocked Filenames Or Filetypes'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If "Notify Senders" is set to yes,
                            do you want to notify people who sent you messages
                            containing attachments that are blocked due to
                            their filename or file contents?"""))
    warnsizesenders = SelectField(_('Notify Senders Of Blocked Size Attachments'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If "Notify Senders" is set to yes,
                            do you want to notify people who sent you messages
                            containing attachments that are blocked due to
                            being too small or too large?"""))
    warnothersenders = SelectField(_('Notify Senders Of Other Blocked Content'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If "Notify Senders" is set to yes,
                            do you want to notify people who sent you messages
                            containing other blocked content, such as partial
                            messages or messages with external bodies?"""))
    nosenderprecedence = TextField(_('Never Notify Senders Of Precedence'),
                            default='list bulk',
                            description=_("""If you supply a space-separated
                            list of message "precedence" settings, then senders
                            of those messages will not be warned about anything
                            you rejected. This is particularly suitable for
                            mailing lists."""))
    sendnotices = SelectField(_('Send Notices'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Notify the local system administrators
                            when any infections are found?"""))
    noticefullheaders = SelectField(_('Notices Include Full Headers'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Include the full headers of each message
                            in the notices sent to the local system administrators?"""))
    hideworkdirinnotice = SelectField(_('Hide Incoming Work Dir in Notices'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Hide the directory path from all the
                            system administrator notices."""))
    noticesignature = TextAreaField(_('Notice Signature'),
                            default='-- \n%org-name%\nEmail Security\n%website%',
                            description=_("""What signature to add to the bottom
                            of the notices."""))
    noticesfrom = TextField(_('Notices From'),
                            default='Baruwa',
                            description=_("""The visible part of the email address
                            used in the "From:" line of the notices. The <user@domain>
                            part of the email address is set to the "Local Postmaster"
                            setting."""))
    noticerecipient = TextField(_('Notices To'),
                            default='postmaster',
                            description=_("""Where to send the notices."""))
    localpostmaster = TextField(_('Local Postmaster'),
                            default='postmaster',
                            description=_("""Address of the local Postmaster,
                            which is used as the "From" address in infection
                            warnings sent to users."""))


class SpamSettings(Form):
    "Spam settings"
    maxspamassassinsize = TextField(_('Max SpamAssassin Size'),
                            default='800k',
                            description=_("""Truncate messages to this size to
                            improve SpamAssassin speed (in kilobytes)"""),
                            validators=[validators.Regexp(MAX_SPAMASSASSIN_RE,
                            message=_('Incorrect Format'))])
    spamassassinautowhitelist = SelectField(_('SpamAssassin Auto Whitelist'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Enable the automatic whitelisting
                            functions available within SpamAssassin."""))
    spamassassintimeout = IntegerField(_('SpamAssassin Timeout'),
                            default=75,
                            description=_("""If SpamAssassin takes longer than
                            this (in seconds), the checks is abandoned and the
                            timeout noted."""))
    maxspamassassintimeouts = IntegerField(_('Max SpamAssassin Timeouts'),
                            default=10,
                            description=_("""If SpamAssassin times out more
                            times in a row than this, then it will be marked
                            as "unavailable" until the Scanner next re-starts
                            itself."""))
    satimeoutlen = IntegerField(_('SpamAssassin Timeouts History'),
                            default=30,
                            description=_("""The total number of SpamAssassin
                            attempts during which "Max SpamAssassin Timeouts"
                            will cause SpamAssassin to stop doing all
                            network-based tests.
                            If double the timeout value is reached (i.e. it
                            continues to timeout at the same frequency as
                            before) then it is marked as "unavailable"."""))
    checksaifonspamlist = SelectField(_('Check SpamAssassin If On Spam List'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""If the message sender is on any
                            of the Spam Lists, do you still want to do the
                            SpamAssassin checks? Setting this to "no" will
                            reduce the load on your server, but will stop
                            the Definate Spam Actions from ever firing."""))
    sadecodebins = SelectField(_('Include Binary Attachments In SpamAssassin'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Normally, SpamAssassin skips over
                            all non-text attachments and does not scan them for
                            indications that the message is spam.
                            This setting over-rides that behaviour, telling
                            SpamAssassin to scan all attachments regardless
                            of type."""))
    spamstars = SelectField(_('Spam Score'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to include the
                            "Spam Score" header. This shows 1 character
                            (Spam Score Character) for every point of the
                            SpamAssassin score. This makes it very easy for
                            users to be able to filter their mail using
                            whatever SpamAssassin threshold they want."""))
    usesacache = SelectField(_('Cache SpamAssassin Results'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""For extra speed, cache the
                            SpamAssassin results for the messages"""))
    bayesrebuild = IntegerField(_('Rebuild Bayes Every'),
                            default=0,
                            description=_("""When using the Bayesian
                            statistics engine on a busy server,
                            you may well need to force a Bayesian
                            database rebuild and expiry at regular
                            intervals. This is measures in seconds.
                            1 day = 86400 seconds. To disable this
                            feature set this to 0."""))
    bayeswait = SelectField(_('Wait During Bayes Rebuild'),
                            choices=YES_NO,
                            default='no',
                            description=_("""During this time you can
                            either wait, or simply disable SpamAssassin
                            checks until it has completed."""))
    # spamchecks = SelectField(_('Spam Checks'),
                            # choices=YES_NO, default='yes')
    spamlist = SelectMultipleField(_('Spam List'),
                            choices=list(SPAM_LISTS),
                            description=_("""This is the list of spam
                            blacklists (RBLs) to enable."""))
    spamdomainlist = SelectMultipleField(_('Spam Domain List'),
                            choices=list(SPAM_DOMAIN_LISTS),
                            description=_("""This is the list of spam
                            domain blacklists to enable"""))
    normalrbls = IntegerField(_('Spam Lists To Be Spam'),
                            default=1,
                            description=_("""If a message appears in
                            at least this number of "Spam Lists"
                            (as defined above), then the message will
                            be treated as spam"""))
    highrbls = IntegerField(_('Spam Lists To Reach High Score'),
                            default=3,
                            description=_("""If a message appears in at
                            least this number of "Spam Lists" (as defined
                             above), then the message will be treated as
                            'Definate Spam'"""))
    spamlisttimeout = IntegerField(_('Spam List Timeout'),
                            default=10,
                            description=_("""If an individual "Spam List"
                            or "Spam Domain List" check takes longer
                            than this (in seconds), the check is abandoned
                            and the timeout noted."""))
    maxspamlisttimeouts = IntegerField(_('Max Spam List Timeouts'),
                            default=7,
                            description=_("""The maximum number of timeouts
                            caused by any individual "Spam List" or
                            "Spam Domain List" before it is marked as
                            "unavailable"."""))
    rbltimeoutlen = IntegerField(_('Spam List Timeouts History'),
                            default=10,
                            description=_("""The total number of Spam List
                            attempts during which "Max Spam List Timeouts"
                            #will cause the spam list fo be marked as
                            "unavailable"."""))
    blacklistedishigh = SelectField(_('Banned sender Is High Scoring'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Setting this to yes means that
                            spam found in the Banned sender list is treated
                            as Definate Spam"""))
    whitelistmaxrecips = IntegerField(_('Ignore Approved senders If Recipients Exceed'),
                            default=20,
                            description=_("""Ignore Approved senders If
                            Recipients Exceed this number"""))
    maxspamchecksize = IntegerField(_('Max Spam Check Size'),
                            default=150000,
                            description=_("""Dont run Spam checks on messages
                            bigger than this size (in bytes)"""))
    enablespambounce = SelectField(_('Enable Spam Bounce'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Enable Spam Bounce"""))
    bouncespamasattachment = SelectField(_('Bounce Spam As Attachment'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Send Bounces as Attachments?"""))
    spamdetail = SelectField(_('Detailed Spam Report'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want the full spam report,
                            or just a simple "spam / not spam" report?"""))
    listsascores = SelectField(_('Include Scores In SpamAssassin Report'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to include the
                            numerical scores in the detailed SpamAssassin
                            report, or just list the names of the scores?"""))
    includespamheader = SelectField(_('Always Include SpamAssassin Report'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to always include
                            the Spam Report in the SpamCheck header, even
                            if the message wasn't spam?"""))
    spamheader = TextField(_('Spam Header'),
                            default='X-%org-name%-BaruwaFW-SpamCheck:',
                            description=_("""Add this extra header to all
                            messages found to be spam."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    spamstarsheader = TextField(_('Spam Score Header'),
                            default='X-%org-name%-BaruwaFW-SpamScore:',
                            description=_("""Add this extra header if
                            "Spam Score" = yes. The header will contain
                            1 character for every point of the SpamAssassin
                            score."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])
    scoreformat = TextField(_('Spam Score Number Format'),
                            default='%d.1f',
                            description=_("""When putting the value of the
                            spam score of a message into the headers,
                            how do you want to format it.A few examples for you:
                            * %d     ==> 12
                            * %5.2f  ==> 12.34
                            * %05.1f ==> 012.3"""))
    spamstarscharacter = TextField(_('Spam Score Character'),
                            default='s',
                            description=_("""The character to use in the
                            "Spam Score Header".
                            Don't use: x as a score of 3 is "xxx" which
                            the users will think is porn,
                            * '#' as it will cause confusion with comments
                             in procmail as well the Scanner itself,
                            * '*' as it will cause confusion with pattern
                             matches in procmail,
                            * '.' as it will cause confusion with pattern
                             matches in procmail,
                            * '?' as it will cause the users to think
                             something went wrong.
                            * 's' is nice and safe and stands for "spam"."""))
    spamscorenotstars = SelectField(_('SpamScore Number Instead Of Stars'),
                            choices=YES_NO,
                            default='no',
                            description=_("""If this option is set to yes,
                            you will get a spam-score header saying just
                            the value of the spam score, instead of the
                            row of characters representing the score."""))
    minstars = IntegerField(_('Minimum Stars If On Spam List'),
                            default=0,
                            description=_("""This sets the minimum number
                            of "Spam Score Characters" which will appear
                            if a message triggered the "Spam List" setting
                            but received a very low SpamAssassin score."""))
    usewatermarking = SelectField(_('Use Watermarking'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to enable the
                            watermarking features?"""))
    addmshmac = SelectField(_('Add Watermark'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""Do you want to add a watermark
                            to each email message?"""))
    checkmshmac = SelectField(_('Check Watermarks With No Sender'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to check watermarks?"""))
    mshmacnull = SelectField(_('Treat Invalid Watermarks With No Sender as Spam'),
                            choices=WATERMARK_OPTIONS,
                            default='nothing',
                            description=_("""If the message has an invalid
                            watermark and no sender address, then it is a
                            delivery error (DSN) for a message which didn't
                            come from us.
                            Delivery errors have no sender address. So we
                            probably want to treat it as spam, or definate spam.
                            This option can take one of 5 values:
                            * "delete",
                            * "spam",
                            * "definate spam",
                            * "nothing"
                            If you set it to "nothing" then there probably isn't
                            much point in checking watermarks at all."""))
    checkmshmacskip = SelectField(_('Check Watermarks To Skip Spam Checks'),
                            choices=YES_NO,
                            default='yes',
                            description=_("""This feature skips Spam Checks
                            if the Watermark is trusted. The trust only works
                            between servers so will not apply to replies to
                            emails."""))
    mshmac = TextField(_('Watermark Secret'),
                            default='please change this to a secret pass phrase',
                            description=_("""This is the secret key used in the
                            watermark calculations to ensure that the watermark
                            can't be spoofed. It should be set to the same value
                            on all the Scanners in your organisation.

                            Note: YOU SHOULD CHANGE THIS TO SOMETHING
                            SECRET!"""))
    mshmacvalid = IntegerField(_('Watermark Lifetime'),
                            default=604800,
                            description=_(
                            """This sets the lifetime of a watermark.
                            Set it to the maximum length of time that you want
                            to allow for delivery errors to be delivered. Most
                            sites set their delivery timeouts to less than 7
                            days, so that is a reasonable value to use. This
                            time is measured in seconds. 7 days = 604800
                            seconds."""))
    mshmacheader = TextField(_('Watermark Header'),
                            default='X-%org-name%-BaruwaFW-Watermark:',
                            description=_("""This sets the name of the Watermark
                            header. Make sure this is customised for your site,
                            as you don't want to be reading other people's
                            watermarks."""),
                            validators=[validators.Regexp(MAIL_X_HEADER_RE,
                            message=_('Header provided is not valid'))])


class LoggingSettings(Form):
    "Logging settings"
    logfacility = SelectField(_('Syslog Facility'),
                            choices=SYSLOG_FACILITIES,
                            default='mail',
                            description=_("""This is the syslog "facility" name
                            that the Scanner uses. If you don't know what a
                            syslog facility name is, then don't change this
                            value"""))
    logspeed = SelectField(_('Log Speed'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want to log the processing
                            speed for each section of the code for a batch?
                            This can be very useful for diagnosing speed
                            problems, particularly in spam checking."""))
    logspam = SelectField(_('Log Spam'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Do you want all spam to be logged?
                            Useful if you want to gather spam statistics from
                            your logs, but can increase the system load quite a
                            bit if you get a lot of spam."""))
    lognonspam = SelectField(_('Log Non Spam'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Do you want all non-spam to be logged?
                            Useful if you want to see all the SpamAssassin
                            reports of mail that was marked as non-spam.
                            Note: It will generate a lot of log traffic."""))
    logdelivery = SelectField(_('Log Delivery And Non-Delivery'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Do you want to log all messages that
                            are delivered and not delivered to the original
                            recipients. Note that this log output will include
                            the Subject: of the original email, so is switched
                            off by default.
                            In some countries, particularly the EU, it may well
                            be illegal to log the Subject: of email messages.
                            """))
    logpermittedfilenames = SelectField(_('Log Permitted Filenames'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Log all the filenames that are allowed
                            by the Filetype Rules, or just the filetypes that
                            are denied?"""))
    logpermittedfiletypes = SelectField(_('Log Permitted Filetypes'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Log all the filenames that are allowed
                            by the Filetype Rules, or just the filetypes that
                            are denied?"""))
    logpermittedfilemimetypes = SelectField(_('Log Permitted File MIME Types'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Log all the filenames that are allowed
                            by the MIME types set in Filetype Rules, or just
                            the MIME Types yes that are denied?"""))
    logsilentviruses = SelectField(_('Log Silent Viruses'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Log all occurrences of 'Silent Viruses'"""))
    loghtmltags = SelectField(_('Log Dangerous HTML Tags'),
                            choices=YES_NO,
                            default='no',
                            description=_(
                            """Log all occurrences of HTML tags found
                            in messages, that can be blocked. This will help
                            you build up your whitelist of message sources
                            for which particular HTML tags should be allowed,
                            such as mail from newsletters and daily cartoon
                            strips."""))
    logsaactions = SelectField(_('Log SpamAssassin Rule Actions'),
                            choices=YES_NO,
                            default='no',
                            description=_("""Log all actions from the "SpamAssassin
                            Rule Actions" setting?"""))


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
    enabled = BooleanField(_('Enabled'), description=STATUS_DESC)


class PolicyForm(Form):
    """Policy Form"""
    name = TextField(_('Policy Name'), [validators.Required(message=REQ_MSG),
                        validators.Length(min=3, max=254),
                        validators.Regexp(r"^[a-zA-Z_\-]+$")],
                        description=_("""The Policy Name, a descriptive name
                                        to deferentiate the policy from
                                        others"""))
    enabled = BooleanField(_('Enabled'), description=STATUS_DESC)


class AddRuleForm(Form):
    """Rule addition form"""
    expression = TextField(_('Expression'),
                        [validators.Required(message=REQ_MSG),
                        validators.Length(min=3, max=254)],
                        description=_("""This is a regular expression used
                                    to match the required object"""))
    description = TextField(_('Description'),
                        [validators.Required(message=REQ_MSG)],
                        description=_("""This is a description of the rule"""))
    options = TextField(_('Options'),
                        description=_("""Rule options, this is
                        used to specify the email addresses or
                        rename to text"""))
    action = SelectField(_('Action'),
                        choices=RULE_ACTIONS,
                        default='deny',
                        description=_("""The action to be performed
                                        if rule is matched"""))
    enabled = BooleanField(_('Enabled'), description=STATUS_DESC)


class PolicySettingsForm(Form):
    """Policy Settings Form"""
    archive_filename = SelectField(_('Archive File Policy'),
                        description=_("""Select an Archive File Policy to be
                                    used"""))
    archive_filetype = SelectField(_('Archive MIME Policy'),
                        description=_("""Select an Archive Mime Policy to be
                                    used"""))
    filename = SelectField(_('File Policy'),
                        description=_("""Select a File Policy to be used"""))
    filetype = SelectField(_('Mime Policy'),
                        description=_("""Select a Mime policy to be used"""))


def check_address(form, field):
    """Check the address"""
    if str(form.address_type.data) not in ADDR_TYPES:
        raise validators.ValidationError(
            _(u'The address cannot be verified'))
    if str(form.address_type.data) in ['1', '3', '5', '6', '7', '9']:
        if not IPV4_RE.match(field.data):
            raise validators.ValidationError(
                _('Invalid IP address'))
    if str(form.address_type.data) in ['4', '8', '10']:
        if IPV4_RE.match(field.data) or not DOM_RE.match(field.data):
            raise validators.ValidationError(
                _('Invalid Domain name'))


class MTASettingsForm(Form):
    """MTA Settings Form"""
    address = TextField(_('Address'),
                        [validators.Required(message=REQ_MSG),
                        validators.Length(min=3, max=254), check_address],
                        description=_("""The address to match"""))
    enabled = BooleanField(_('Enabled'), description=STATUS_DESC)
    address_type = HiddenField(validators=[validators.AnyOf(ADDR_TYPES)])


class LocalScoreForm(Form):
    """Local Score form"""
    local_score = DecimalField(_('Local score'),
                                description=_("""The local score to overide
                                                the default score"""))

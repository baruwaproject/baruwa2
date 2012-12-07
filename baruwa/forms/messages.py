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
"Messages forms"

from wtforms import BooleanField, SelectField, validators
from wtforms import TextField, SelectMultipleField
from wtforms.widgets import CheckboxInput, ListWidget
from pylons.i18n.translation import lazy_ugettext as _

from baruwa.forms import Form
from baruwa.lib.regex import ADDRESS_RE

LEARN_OPTS = (
    ('spam', 'Spam'),
    ('ham', 'Clean'),
    ('forget', 'Forget')
)


class MultiCheckboxField(SelectMultipleField):
    "Multiple checkbox"
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class ReleaseMsgForm(Form):
    "Release messages form"
    def validate_all(self):
        errors = []
        if not self.release.data and not self.delete.data and not self.learn.data:
            errors.append(_('Select atleast one action to perform'))
        return errors

    def validate(self):
        if not super(ReleaseMsgForm, self).validate():
            return False

        errors = self.validate_all()
        if errors:
            self._errors = {'all': errors}
            return False
        return True

    def validate_altrecipients(self, field):
        if self.usealt.data and not field.data and self.release.data:
            raise validators.ValidationError(
            _('Provide atleast one alternative recipient'))

        if self.usealt.data and field.data and self.release.data:
            emails = field.data.split(',')
            for email in emails:
                if not ADDRESS_RE.match(email.strip()):
                    raise validators.ValidationError(
                    _('Invalid email address'))

    release = BooleanField(_('Release'), default=False)
    delete = BooleanField(_('Delete'), default=False)
    learn = BooleanField(_('Bayesian Learn'), default=False)
    usealt = BooleanField(_('Alt recipients'), default=False)
    learnas = SelectField('', choices=LEARN_OPTS)
    altrecipients = TextField('')


class BulkReleaseForm(ReleaseMsgForm):
    "Bulk release form"
    message_id = MultiCheckboxField('')

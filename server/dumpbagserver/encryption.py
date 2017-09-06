# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
import subprocess

from subprocess import PIPE

from .exception import DumpEncryptionError

import logging

_logger = logging.getLogger(__name__)


class EncryptionOptions():
    """ Base options for commanders """
    _commander = None


class EncryptionCommander():
    """ Base commander for encryption

    :meth:`new_commander` is a factory method that returns an instance
    of the commander determined by the type of the options.

    """

    def __init__(self, options):
        self.options = options

    @classmethod
    def new_commander(cls, options):
        klass = options._commander
        if not klass:
            raise TypeError('No commander class set for these options')
        return klass(options)

    def public_keys(self):
        return ''

    def encrypt(self, tmpdir, filename):
        raise NotImplementedError

    def download_commands(self, dbname, filename):
        return [], {}


class NoOpEncryptionCommander(EncryptionCommander):
    """ Commander for no-op (no encryption) """

    def encrypt(self, tmpdir, filename):
        return filename


class NoOpEncryptionOptions():
    """ Options for no-op (no encryption) """
    _commander = NoOpEncryptionCommander


class GPGKeysCommander(EncryptionCommander):
    """ Commander for encryption with GPG Public/Private Keys """

    def public_keys(self):
        keys = []
        for recipient in self.options.recipients:
            command = [
                'gpg', '--export', '-a', recipient
            ]
            proc = subprocess.Popen(
                command, stdin=PIPE, stdout=PIPE, stderr=PIPE
            )
            stdout, stderr = proc.communicate()
            keys.append(stdout.decode('utf8'))
        return '\n'.join(keys)

    def encrypt(self, tmpdir, filename):
        target = os.path.join(tmpdir, filename)
        command = [
            'gpg', '--encrypt', '--always-trust',
        ]
        for recipient in self.options.recipients:
            command += [
                '--recipient', recipient,
            ]
        command.append(target)
        proc = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode:
            _logger.error(
                'error when encrypting %s:\n%s', target, stderr.decode('utf8')
            )
            raise DumpEncryptionError(stderr.decode('utf8'))
        return "%s.gpg" % (filename,)

    def download_commands(self, dbname, filename):
        lines = [
            "# decrypt with gpg, "
            "you need to have the private key (on lastpass)",
            "$$ gpg $filename",
        ]
        return lines, {}


class GPGKeysOptions():
    """ Options for GPG Public/Private Keys encryption """
    _commander = GPGKeysCommander

    def __init__(self, recipients):
        self.recipients = recipients

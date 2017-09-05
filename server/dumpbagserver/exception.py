# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


class DumpBagError(Exception):
    """ Base Exception for the application """


class DumpConfigurationError(DumpBagError):
    """ Configuration Error """


class DumpingError(DumpBagError):
    """ Exception during creation of dump """


class DumpNotExistError(DumpBagError):
    """ Dump does not exist """


class DumpEncryptionError(DumpBagError):
    """ Error with the encryption """


class DumpStorageError(DumpBagError):
    """ Error with the storage """

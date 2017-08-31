# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


class DumpBagError(Exception):
    """ Base Exception for the application """


class DumpingError(DumpBagError):
    """ Exception during creation of dump """

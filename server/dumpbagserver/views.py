# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from dumpbagserver import app, app_config
from flask import Flask, render_template, redirect, url_for, request, flash

from .bagger import Bagger


@app.route('/')
def databases():
    databases = Bagger(app_config).list_databases()
    return render_template('databases.html', databases=databases)


@app.route('/dumps')
def dumps():
    dumps = Bagger(app_config).list_dumps()
    return render_template('dumps.html', dumps=dumps)


@app.route('/dump/<string:dbname>')
def new_dump(dbname):
    filename = Bagger(app_config).bag_one_database(dbname)
    flash('dump {} has been pushed with filename {}'.format(dbname, filename))
    return redirect(url_for('dumps'))

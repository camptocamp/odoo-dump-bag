# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import re
from datetime import datetime

from dumpbagserver import app, app_config
from flask import render_template, redirect, url_for, flash, jsonify

from .bagger import Bagger

RE_DUMP_DATE = re.compile('.*(\d{8}-\d{6}).*')

@app.route('/databases')
def databases():
    databases = Bagger(app_config).list_databases()
    return render_template('databases.html', databases=databases)


@app.route('/')
def dumps():
    bagger = Bagger(app_config)
    dumps = bagger.list_dumps()
    return render_template('dumps.html', dumps=dumps,
                           download_commands=bagger.download_commands)


@app.route('/dump/<string:dbname>')
def new_dump(dbname):
    filename = Bagger(app_config).bag_one_database(dbname)
    flash('dump {} has been pushed with filename {}'.format(dbname, filename))
    return redirect(url_for('dumps', _anchor=dbname))


@app.route('/has_dump_for_today/<string:dbname>')
def has_dump_for_today(dbname):
    return jsonify(Bagger(app_config).has_dump_for_today(dbname))


@app.route('/download/<string:db>/<string:filename>')
def download_dump(db, filename):
    dump = Bagger(app_config).read_dump(db, filename)
    r = app.response_class(dump, mimetype='application/octet-stream')
    r.headers.set('Content-Disposition', 'attachment', filename=filename)
    return r


@app.template_filter('date_from_dumpname')
def date_from_dumpname(s):
    # extract 20170904-143345 from 'prod_template-20170904-143345.pg'
    s_date = RE_DUMP_DATE.match(s).groups()[0]
    converted = datetime.strptime(s_date, '%Y%m%d-%H%M%S')
    return converted.strftime('%Y-%m-%d %H:%M:%S')

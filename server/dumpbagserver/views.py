# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import re
from datetime import datetime

from dumpbagserver import app, app_config
from flask import render_template, redirect, url_for, flash, jsonify
from werkzeug.routing import UnicodeConverter, ValidationError

from .bagger import Bagger


class DBNameConverter(UnicodeConverter):

    def to_python(self, value):
        if not re.match("^[A-Za-z0-9_-]+$", value):
            raise ValidationError()
        return value


app.url_map.converters['dbname'] = DBNameConverter


RE_DUMP_DATE = re.compile(r'.*(\d{8}-\d{6}).*')


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


@app.route('/dump/<dbname:dbname>')
def new_dump(dbname):
    filename = Bagger(app_config).bag_one_database(dbname)
    flash('dump {} has been pushed with filename {}'.format(dbname, filename))
    return redirect(url_for('dumps', _anchor=dbname))


@app.route('/dumpall')
def dumpall():
    # route used from curl / scheduler / cron
    Bagger(app_config).bag_all_databases()
    return ''


@app.route('/has_dump_for_today/<dbname:dbname>')
def has_dump_for_today(dbname):
    """ Indicate if we already have a dump for today

    Called with an ajax request from the 'databases' view
    """
    return jsonify(Bagger(app_config).has_dump_for_today(dbname))


@app.route('/download/<dbname:db>/<string:filename>')
def download_dump(db, filename):
    dump = Bagger(app_config).read_dump(db, filename)
    r = app.response_class(dump, mimetype='application/octet-stream')
    r.headers.set('Content-Disposition', 'attachment', filename=filename)
    return r


@app.route('/api/nightly')
def get_nightlies():
    """ Return a JSON object with the list of S3 URIs
        for each dump of the current day
    """
    today = datetime.today().strftime('%Y%m%d')
    storage = Bagger(app_config).storage
    db_list = storage.list_by_db()
    return jsonify([
        storage.download_commands(k, v[-1])[1]['s3_url']
        for k, v in db_list.items()
        if today in v[-1]
    ])


@app.route('/api/dumps/<dbname:db>')
def dumps_for(db):
    bagger = Bagger(app_config)
    dumps = bagger.list_dumps(dbname=db).get(db, [])
    return jsonify([
        "%s/%s" % (db, dump) for dump in dumps
    ])


@app.route('/help')
def help():
    has_gpg = app_config.encryption_kind == 'gpg'
    gpg_recipients = (
        app_config.encryption_options().recipients
        if has_gpg else ''
    )
    has_s3 = app_config.storage_kind == 's3'
    return render_template(
        'help.html',
        has_s3=has_s3,
        has_gpg=has_gpg,
        gpg_recipients=gpg_recipients,
    )


@app.route('/keys')
def public_keys():
    return '\n'.join(Bagger(app_config).public_keys())


@app.route('/recipients')
def recipients():
    return ','.join(Bagger(app_config).recipients())


@app.template_filter('date_from_dumpname')
def date_from_dumpname(s):
    # extract 20170904-143345 from 'prod_template-20170904-143345.pg'
    match = RE_DUMP_DATE.match(s)
    if match is None:
        return ''
    converted = datetime.strptime(match.groups()[0], '%Y%m%d-%H%M%S')
    return converted.strftime('%Y-%m-%d %H:%M:%S')

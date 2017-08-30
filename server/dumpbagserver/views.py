# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from dumpbagserver import app
from flask import Flask, render_template, redirect, url_for, request, flash


@app.route('/')
def databases():
    return render_template('databases.html')


@app.route('/dumps')
def dumps():
    return render_template('dumps.html')

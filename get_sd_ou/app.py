#!/usr/bin/env python3
from flask import (Flask, request, render_template, session, flash,
    redirect, url_for, jsonify)

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

from celery import Celery
import time

from get_sd_ou import get_sd_ou

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top top secret!'

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['CELERY_IGNORE_RESULT'] = False

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])

celery.conf.update(app.config)


class StartForm(FlaskForm):
    start_year = StringField('years', validators=[DataRequired()])
    term = StringField('Search term')
    pub_title = StringField('in jornal or book title ')
    authors = StringField('authors')
    affiliation = StringField('affiliation')
    volume = IntegerField('volume')
    issue = IntegerField('issue')
    page = IntegerField('page')
    keywords = StringField('Title, abstract or author-specified keywords')
    title = StringField('title')
    refrence = StringField('refrences')
    issn = StringField('ISSN or ISBN')
    submit = SubmitField('Start')
    
@celery.task(bind=True)
def search_task(self, **search_kwargs):
    #TODO this celery decorated function should be inside get_sd_ou and import it here to be called when start clicked on web page
    #
    #
    #    IMPORTANT IMPLIMENTATION IN GET_SD_OU.get_sd_ou for celey self.update
    #  
    #
    #
    for i in range(100):
        message = f'{i}'
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': 100,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

@app.route('/longtask', methods=['POST'])
def longtask():

    form = StartForm()
    kwargs = {
        'start_year':form.start_year.data, 
        'qs':form.term.data,
        'pub':form.pub_title.data,
        'authors':form.authors.data,
        'affiliations':form.affiliation.data,
        'volume':form.volume.data,
        'issue':form.issue.data,
        'page':form.page.data,
        'tak':form.keywords.data,
        'title':form.title.data,
        'refrences':form.refrence.data,
        'docId':form.issn.data
    }
    task = get_sd_ou.start_search.apply_async(kwargs=kwargs)
    print(kwargs)
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}

@app.route('/', methods=['GET', 'POST'])
def index():
    form = StartForm()
    return render_template('index.html', form=form)
    
@app.route('/taskstatus/<task_id>')
def taskstatus(task_id):
    task = search_task.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }


    return jsonify(response)
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
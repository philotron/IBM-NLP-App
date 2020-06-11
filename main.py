"""
    StaffingAdvisor
    ~~~~~
    A web application based on the developed matching engine. Main purpose of
    the app is representing an adequate use case for the matching engine.
    
    Version 1.0 - 01.05.2019
"""

# import used modules
from flask import Flask, redirect, render_template, request, url_for, jsonify, session
from flask_sessionstore import Session
from flask_bootstrap import Bootstrap
import engine
import conn_eightbase
from webforms import InputForm, SkillForm, RequirementForm, FeedbackForm
import pandas as pd

# initialize application and connect to 8base
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'super secret key'
Session(app)
Bootstrap(app)
eb_connection = conn_eightbase.EightbaseConnection()

# each page is connected with a function that gets executed
@app.route("/")
def index():
    session.clear()
    return render_template('index.html')

# page for title and description user input
@app.route("/input", methods=['GET', 'POST'])
def input():
    form = InputForm()
    taxon = pd.read_json(r'taxon.json', orient='split')
    title_list=[(row['name'], row['name']) for i, row in taxon.iterrows()]
    title_list = [('-', '-')] + title_list
    form.title_select.choices = title_list
    if form.validate_on_submit() and request.method == 'POST':
        session['title'] = form.title.data
        session['title_select'] = form.title_select.data
        session['description'] = form.description.data
        if form.title.data == '':
            session['title'] = form.title_select.data
                   
        return redirect(url_for('output'))

    return render_template('input.html', form=form)    

'''
    page for calculating and displaying matching results
    de-comment lines 62, 65 and comment out line 64 to query and preprocess taxnonmy directly from
    8base (not reading in the already preprocessed json taxonomy)
'''

@app.route("/output", methods=['GET', 'POST'])
def output():
    if session.get('title') or session.get('description'):
        title = session.get('title')
        description = session.get('description')
#        json = eb_connection.getAllOccupations()
        taxon = pd.read_json(r'taxon.json', orient='split')
        match = engine.OccMatcher(title, description, taxon=taxon)
#        match.read_taxonomy(json)
        match.preprocess_input()
        # set thresholds according to what works best
        match.evaluate_match(th_fuzz=0.75, th_coss=0.15, th_fuzz_2=15, th_coss_2=0.2)
        opr = match.output_results()
        session['skill_list'] = opr.skill_list
        session['skill_rank'] = opr.skill_rank
        session['title_list'] = opr.title_list
        session['requirement_list'] = opr.requirement_list
        return render_template('output.html', opr=opr)
    
    return render_template('output.html')

# page for selecting skills based on matching results
@app.route("/skills", methods=['GET', 'POST'])
def skills():
    form = SkillForm()
    if form.validate_on_submit() and request.method == 'POST':
        session['sow_skills'] = (form.autotag.data).split(',')
        return redirect(url_for('requirements'))
    
    return render_template('skills.html', form=form)
    

# function for autocompletion with Bloodhound
@app.route('/bloohdhoundRemote', methods=['GET', 'POST'])
def bloohdhoundRemote():
	print("bloohdhoundRemote() called") 
	if request.method == 'POST':
		print("POST request") 
	else:
		print("GET request")

	if session.get('skill_list'):
		options = session.get('skill_list')
	else:
		options = ['no data']

	return jsonify(options=options)


# page for selecting requirements based on matching results
@app.route("/requirements", methods=['GET', 'POST'])
def requirements():
    form = RequirementForm()
    if session.get('sow_skills') and session.get('requirement_list'):
        requirement_list= engine.OccMatcher.string_similarity(' '.join(session.get('sow_skills')), session.get('requirement_list'))
        requirement_list=[(item[0], item[0]) for item in requirement_list]
        form.multiple.choices = requirement_list
    
    if  request.method == 'POST' and form.validate_on_submit():
        session['sow_requirements'] = form.multiple.data
        session['req_text'] = form.req_text.data
        session['sow_requirements'].append(session['req_text'])
        
        
        return redirect(url_for('feedback'))
    
    return render_template('requirements.html', form=form)
       
        
# page for user feedback input
@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    if  request.method == 'POST' and form.validate_on_submit and session.get('title') and session.get('sow_skills') and session.get('sow_requirements'):
        session['feedback'] = form.feedback.data
        session['rating'] = form.rating.data
        file1 = open("SOW_1.txt","w")
        file1.write("================================================Statement of Work================================================")
        file1.writelines(["\nTitle: ", session['title']])
        file1.writelines(["\nDescription: ", session['description']])
        file1.write("\n")
        file1.write("\nSkills:")
        for i in session.get('sow_skills'):
            file1.write("\n"+i)
        file1.write("\n")
        file1.write("\nRequirements:")
        for i in session.get('sow_requirements'):
            file1.write("\n"+i)
        file1.write("\n")
        file1.writelines(["\nFeedback: ", session['feedback']])
        file1.write("\n")
        file1.writelines(["\nRating: ", session['rating']])    
        
        result = eb_connection.uploadSOW(session['title'], session['description'], str(session.get('sow_skills')),
                                        str(session['sow_requirements']), session['feedback'], session['rating'])
        
        return render_template('feedback.html', form=form)
    
    return render_template('feedback.html', form=form)


# start web application
if __name__ == "__main__":
    app.run(debug=True)
    



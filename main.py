from flask import render_template, redirect, url_for, request, flash, redirect, session, make_response, Flask
from wtforms import Form, BooleanField, StringField, validators, TextAreaField
from bson.objectid import ObjectId

import smtplib
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv('MONGO'))
db = client.thingsTD
Notes = db.Notes
Usuarios = db.Usuarios

app = Flask(__name__)

app.secret_key = 'some super secure string'

@app.route('/', defaults={'lg' : 'en'})
@app.route('/<lg>')
def home(lg):
	if lg == "es":
		return render_template('ES/home.html')
	return render_template('EN/home.html')

@app.route('/throw/', defaults={'lg' : 'en'})
@app.route('/throw/<lg>', methods=['POST', 'GET'])
def throw(lg):
	if request.method == 'POST':
		if len(request.form['note']) >= 340:
			flash('El mensaje que quieres enviar es demasiado largo')
			return render_template('throw.html')

		info = {'title':request.form['title'],
				'note':request.form['note'],
				'date':str(datetime.datetime.now().date()),
				'save':0,
				'throw_again':0}
		Notes.insert_one(info)
		flash('Has lansado una botella')
		return render_template('throw.html', info=info)

	if lg == "es":
		return render_template('ES/throw.html')
	return render_template('EN/throw.html')

@app.route('/catch/', defaults={'lg' : 'en'})
@app.route('/catch/<lg>')
def catch(lg):
	random_note = Notes.aggregate([{ "$sample": { "size": 1 } }])
	note = []
	for inf in random_note:
		note.append(inf)
	if len(note) == 0:
		note.append({'title':'None',
					'note':'No existe ninguna nota hasta el momento, ¿por que no envias la primera?',
					'date':'0-0-0',
					'save':0,
					'throw_again':0
					})
	if lg == "es":
		return render_template('ES/catch.html', note=note)
	return render_template('EN/catch.html', note=note)

def send_email(email_data):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(os.getenv("mail"), os.getenv("passw"))
    text = f"Hello, I'm {email_data['name']}\n This is my email: {email_data['email']}\n Message: {email_data['message']}"
    subject = f"New user: {email_data['name']}"
    message = 'Subject: {}\n\n{}'.format(subject, text)
    server.sendmail(os.getenv("mail"), os.getenv("mail"), message)
    server.quit()

class ContactForm(Form):
    username = StringField('Nombre', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])
    message = TextAreaField('Mensaje', [validators.Length(min=6, max=300)])

@app.route('/contact/', defaults={'lg' : 'es'}, methods=['GET', 'POST'])
@app.route('/contact/<lg>', methods=['GET', 'POST'])
def contact(lg):
    form = ContactForm(request.form)
    if request.method == 'POST' and form.validate():
        email_data = {"name":form.username.data,
                      "email":form.email.data,
                      "message":form.message.data
                        }

        Usuarios.insert_one({'name':email_data['name'], 'email':email_data['email'], 'message':email_data['message']})
        flash('Gracias por contactar con nosotros, responderemos tu mensaje lo antes posible')
        send_email(email_data)

    if lg == "es":
    	return render_template('ES/contact.html', form=form)
    return render_template('EN/contact.html', form=form)


@app.route('/status', methods=['POST'])
def status():
	try:
		inf_form = list(request.form)
		note_id = ObjectId(inf_form[0])

		cursor_note = Notes.find_one({'_id':note_id})
		save_count = int(cursor_note['save'])
		ta_count = int(cursor_note['throw_again'])


		if inf_form[1] == "salvar":
			Notes.update_one({'_id':note_id},{'$set':{'save':save_count+1}}, upsert=False)
		elif inf_form[1] == "regresar":
			Notes.update_one({'_id':note_id},{'$set':{'throw_again':ta_count+1}}, upsert=False)

		return redirect('/catch')
	except:
		return redirect('/')

@app.route('/info/', defaults={'lg' : 'en'})
@app.route('/info/<lg>')
def info(lg):
	if lg == "es":
		return render_template('ES/info.html')
	return render_template('EN/info.html')

if __name__ == "__main__":
	app.run(host='0.0.0.0')

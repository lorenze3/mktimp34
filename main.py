import sys,os
sys.path.insert(0, "D:/home/site/wwwroot/env/Lib/site-packages")
sys.path.append(os.path.join(os.getcwd(), "site-packages"))
from flask import Flask, render_template, request, json, redirect, session, url_for
from werkzeug import generate_password_hash, check_password_hash
import mysql.connector
import uuid
import time
import Mailer
import MKTransforms
import numpy
import pandas as pd
import plotly2json
import multiprocessing
import modeldrone

modelJobs=[]
#create mailer object and go ahead and put in passwords for now . . .

m=Mailer.Mailer()
m.subject='How to use the No Touch Marketing Measurement WebApp'
m.send_from='notouchmarketingmeasurementapp@gmail.com'
m.attachments =["static/downloads/Example.csv"]
m.gmail_password='%like%me'
with open('templates/Email text.txt', 'r') as myfile:
  msg1 = myfile.read()
m.message=msg1
#end mailer setup.  

#define flask server
app = Flask(__name__)
app.secret_key = 'I am the very model of a modern major general'
app.config['UPLOAD_FOLDER'] = 'static/Uploads' 

@app.route("/")
def main():
    #return "Yes This App Is Working"
	 return render_template('index.html')

@app.route('/showSignup')
def showSignup():
    return render_template('signup.html')

@app.route('/signUp',methods=['POST','GET'])
def signUp():
    if request.method == 'POST':
        try:
            _name = request.form['inputName']
            _email = request.form['inputEmail']
            _password = request.form['inputPassword']
            # validate the received values
            if _name and _email and _password:
                # All Good, let's call MySQL
                conn = mysql.connector.connect(user='azure', password='6#vWHD_$',
                                  host='127.0.0.1',port=55302,
                                  database='BucketList',autocommit=True)
                cursor = conn.cursor()
                _hashed_password = generate_password_hash(_password)
                #check for records with that username
                qstr='select * from tbl_user where user_username="'+str(_email)+'";'
                cursor.execute(qstr)
                userrecord=cursor.fetchall()
                cursor.close()
                del cursor
                #return json.dumps({'output':userrecord})
                if len(userrecord) == 0:
                    userrecord=[]
                    #add user to database and send email 
                    cursor2=conn.cursor()
                    cursor2.callproc('sp_createUser',(_name,_email,_hashed_password))    
                    cursor2.close()
                    #conn.close()
                    m.recipients=[_email]
                    m.send_email()
                    mt=""
                    messagetxt="Your account has been created!"
                    message2txt="An input template and instructions have been emailed to you."
                    message3txt="Please sign in to continue."
                    return render_template('signin.html', message=str(messagetxt),message2=str(message2txt),message3=str(message3txt))
                else:
                    mt= "This email address already has an account"
                    message2txt=str(userrecord)+"Please sign in to continue."
                    message3txt=" "
                    return render_template('signin.html', message=str(mt),message2=str(message2txt),message3=str(message3txt))
            else:
                return json.dumps({'html':'<span>Enter the required fields</span>'})
        except Exception as e:
            return json.dumps({'error':str(e)})
        finally:
            #cursor.close() 
            conn.close()
        
@app.route('/showSignin')
def showSignin():
    return render_template('signin.html')

@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']
        conn = mysql.connector.connect(user='azure', password='6#vWHD_$',
                              host='127.0.0.1',port=55302,
                                  database='BucketList')
        cursor = conn.cursor()
        cursor.callproc('sp_validateLogin',(_username,))
        for reg in cursor.stored_results():
            data=reg.fetchall()
        if len(data) > 0:
            if check_password_hash(str(data[0][2]),_password):
                session['user'] = data[0][0]
                session['username']= data[0][1]
                #querystring2="update tbl_user set user_lastlogin = NOW() where user_id="+str(data[0][0])+";"
                #cursor.execute(querystring2)
                return redirect('/userHome')
            else:
                return render_template('error.html',error='Wrong Email address or Password.')
        else:
            return render_template('error.html',error = 'Email address not found.')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close
        conn.close

@app.route('/userHome', methods=['GET', 'POST'])
def userHome():
    if request.method == 'GET':
        if session.get('user'):
            try:
                conn = mysql.connector.connect(user='azure', password='6#vWHD_$',
                              host='127.0.0.1',port=55302,
                                      database='BucketList')
                cursor = conn.cursor()
                querystring="Select data_filename from tbl_datafiles where user_id="+str(session.get('user'))+"&& data_resultsname IS NOT NULL;"
                cursor.execute(querystring)
                results=cursor.fetchall()
                #results is list of tuples;
                #trim off part before _ and extension
                resNames=[]
                resFiles=[]
                for r in results:
                    startchar=int(r[0].find('_')+1)
                    endchar=int(r[0].find('.'))
                    resNames.append(r[0][startchar:endchar])
                    resFiles.append(r[0][0:len(r[0])-4]+'results.json')
                    #resFiles.append(r[1])
                betterResults=zip(resFiles,resNames)
                return render_template('userHome.html', results=betterResults)
            except Exception as e:
                return json.dumps({'error':str(e)})
        else:
            return render_template('error.html',error ='Please Sign In')
        
    if request.method == 'POST':
        struid=session.get('user')
        file = request.files['file']
        f_name = str(struid)+"_"+file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
        try:
            conn = mysql.connector.connect(user='azure', password='6#vWHD_$',
                              host='127.0.0.1',port=55302,
                                  database='BucketList',autocommit=True)
            cursor = conn.cursor()
            cursor.callproc('sp_addinputD',(f_name,struid))
            for rr in cursor.stored_results():
                data=rr.fetchall()
            if not('data' in locals()) or data[0][0]!="Existing Filename; Please rename.":
                #success!
                #add process to processing queue to run models
               # try:
                    #usethisfile=os.path.join(app.config['UPLOAD_FOLDER'], f_name)
                    #p = multiprocessing.Process(
                    #                target=modeldrone.modeldrone,args=(usethisfile,)
                    #                )
                    #modelJobs.append(p)
                    #p.start()
                    
                #except Exception as e:
                    #return json.dumps({'error in multiprocessing':str(e)})
                status, rawdf = MKTransforms.readChkDF(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
                if len(status)>0:
                    return render_template('error.html',error=status)
                        #create model data with user provied transforms
                depMeans,depV,IDnames, groups, transforms, knownSigns, origDep,datadf=MKTransforms.MKTransforms(rawdf)
                #intcoef, X1, Y1 =MKTransforms.runModels(depV,IDnames,groups, knownSigns, origDep,datadf)
                optmsg, intcoef, X1, Y1=MKTransforms.runConstrainedModels(depV,IDnames,groups,knownSigns,origDep,datadf)
                origSpaceDecomp,modSpaceDecomp, =MKTransforms.decomp0(X1,Y1,origDep,intcoef,depV,depMeans,transforms,rawdf,IDnames)
                groupedDecomp=MKTransforms.makeGroupedDecomp(origSpaceDecomp,groups,depV)
                elasts=MKTransforms.calcElast(intcoef,X1,IDnames,groups, transforms)
                figAll=MKTransforms.createDash(groupedDecomp,IDnames,rawdf,groups,elasts,f_name)
                f_nameNoExt=os.path.splitext(f_name)[0]
                jsonname=os.path.join(app.config['UPLOAD_FOLDER'], f_nameNoExt+'results.json')
                plotly2json.plotlyfig2json(figAll, jsonname)
                #tag it in database
                cursor.callproc('sp_addresults',(jsonname,struid,f_name))
                #need to learn how to get upload message on page while using the redirect to trigger the results
                #return render_template('userHome.html',message= 'File Uploaded . . .Ingesting Data. . .')
                return redirect(url_for('userHome',message='File Ingested Sucessfully '+optmsg))
            else:
                return render_template('userHome.html',message = 'Username already has a file of that name.')
        except Exception as e:
            return json.dumps({'error':str(e)})
        finally:
            #close mysql connectino
            cursor.close() 
            conn.close()                

@app.route('/logout')
def logout():
        struid=session.get('user')
        try:
            conn = mysql.connector.connect(user='azure', password='6#vWHD_$',
                                              host='127.0.0.1',port=55302,
                                              database='BucketList',autocommit=True)
            cursor = conn.cursor()
            querystring2='update tbl_user set user_lastlogin = NOW() where user_id='+str(struid)+';'
            cursor.execute(querystring2)
            cursor.close()
            conn.close()
            session.pop('user',None)
            return redirect('/')
        except Exception as e:
            return json.dumps({'error':str(e)})
            
#hahaha
@app.route('/makeDash/<resultsfile>', methods=['GET','POST'])
def makeDash(resultsfile):
    try:
        thisJson=os.path.join(app.config['UPLOAD_FOLDER'], resultsfile)
        #raise ValueError('before html')
        premade=plotly2json.plotlyfromjson(thisJson)
        return render_template('dashboard.html',premade='/'+premade)
    except Exception as e:
        return json.dumps({'error':str(e)})


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        #extension = os.path.splitext(file.filename)[1]
        f_name = file.filename#str(uuid.uuid4()) + extension
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
        return render_template('error.html',error='it worked')#json.dumps({'filename':f_name})

if __name__ == "__main__":
    app.run()
    
    
    
    
    
    
    
    
    
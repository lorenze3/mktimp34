# -*- coding: utf-8 -*-
"""
Created on Sun Jun 10 10:35:00 2018

@author: TeamLorenzen
"""

def modeldrone(ff):    
    import MKTransforms
    import mysql.connector
    import numpy as np
    import pandas as pd
    import ntpath as ntpath
    import os
    import plotly2json
    import plotly
    from flask import Flask, render_template
    
    status, rawdf = MKTransforms.readChkDF(ff)
    if len(status)>0:
        return render_template('error.html',error=status)
    #f_name=ntpath.basename(ff)
    pathtosave,f_name=ntpath.split(ff)
    depMeans,depV,IDnames, groups, transforms, knownSigns, origDep,datadf=MKTransforms.MKTransforms(rawdf)
    intcoef, X1, Y1 =MKTransforms.runModels(depV,IDnames,groups, knownSigns, origDep,datadf)
    origSpaceDecomp,modSpaceDecomp, =MKTransforms.decomp0(X1,Y1,origDep,intcoef,depV,depMeans,transforms,rawdf,IDnames)
    groupedDecomp=MKTransforms.makeGroupedDecomp(origSpaceDecomp,groups,depV)
    elasts=MKTransforms.calcElast(intcoef,X1,IDnames,groups, transforms)
    figAll=MKTransforms.createDash(groupedDecomp,IDnames,rawdf,groups,elasts,f_name)
    f_nameNoExt=os.path.splitext(f_name)[0]
    jsonname=ntpath.join(pathtosave, f_nameNoExt+'results.json')
    return render_template('error.html',error=f_nameNoExt+'results.json')
    plotly2json.plotlyfig2json(figAll, jsonname)
    #tag it in database
    cursor.callproc('sp_addresults',(jsonname,struid))
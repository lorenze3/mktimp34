
def MKTransforms(rawdf):
    import pandas as pd
    #import numpy
    from numpy import arange, r_,reshape
    import math
    """
    #pass in dataframe with control rows on top following expected format
    #output is the
    #names of id columns, groups for decomps, transforms, knownsigns for models, original dep variable
    #and dataframe with only data that is transformed for modeling 
    """
    #control information referenced above
    groups=rawdf.iloc[0,:]
    transforms=rawdf.iloc[1,:]
    knownSigns=rawdf.iloc[2,:]
    
    #some useful lists for dataframes below
    needForAdstockVs=[i for i, word in enumerate(transforms) if word.startswith('adstock')]
    needForAdstockIDs=[i for i,word in enumerate(groups) if word.endswith('id')]
    needForAdstock=needForAdstockIDs + needForAdstockVs
    needForLogVs = [i for i, word in enumerate(transforms) if word.startswith('log')]
    needForMCVs=[i for i, word in enumerate(transforms) if word.endswith('mc')]
    
    #get the data
    
    
    #pd.set_option('display.multi_sparse', False)
    #get the data
    #rawdf=pd.read_csv("C:/Users/TeamLorenzen/Documents/App0/static/downloads/ex.csv")
    #make 4 dataframes (or series, I guess)
    #1) series of groups for decomps from row 2
    #2) series of transforms from row 3
    #3) series of sign constraints from row 4
    
    #Most Df operations want column names -- so they are made in these lists
    IDnames=rawdf.columns.values[needForAdstockIDs].tolist()
    AdstockVs=rawdf.columns.values[needForAdstockVs].tolist()
    LogVs=rawdf.columns.values[needForLogVs].tolist()
    MCVs=rawdf.columns.values[needForMCVs].tolist()
    #if time isn't the last id column then this sort will lead to bad adstock
    rawdf.sort_values(by=IDnames)
    
    #get the data only frame, convert to floats when possible
    datadf=rawdf.iloc[3:rawdf.shape[0],:]
    #get original dependent in a dataframe to be returned for use in decomps
    idxdep=[i for i,word in enumerate(groups) if word==('dependent')]
    depV=rawdf.columns.values[idxdep].tolist()
    origDep=datadf[depV]
    #Adstock transform -- everyone gets a .5 for now!
    retention=0.5
    #forAdstock=rawdf.iloc[3:rawdf.shape[0],needForAdstock]
    #forAdstock=datadf
    #make new vars as name+'_stock'
    #for adstvar in AdstockVs:
    #    forAdstock[adstvar+'_stock']=0
    
    #make dict of sub-DFs by all ID names except the last one, which better be time ID
    #dictAdstockDFs=dict(tuple(forAdstock.groupby(IDnames[0:len(IDnames)-1])))
    dictAdstockDFs=dict(tuple(datadf.groupby(IDnames[0:len(IDnames)-1])))
    
    #apply adstocking to each sub-DF for each variable to be adstocked
    for k in dictAdstockDFs.keys():
        idxmin=dictAdstockDFs[k].index.values.min()
        for adstvar in AdstockVs:
            for i,row in dictAdstockDFs[k][adstvar].iteritems():
                if i==idxmin: #first row is first wweek, needs special care
                    #dictAdstockDFs[k].at[i,adstvar]=value
                    oldvalue=0.0
                    #print(k,i,oldvalue)
                else:
                    #print("start",i,dictAdstockDFs[k].loc[i,adstvar])
                    dictAdstockDFs[k].at[i,adstvar]=pd.to_numeric(dictAdstockDFs[k].loc[i,adstvar])+retention*oldvalue
                    oldvalue=dictAdstockDFs[k].loc[i,adstvar]
                    #print("end",i,dictAdstockDFs[k].loc[i,adstvar])
    #need to recombine them
    datadf=pd.concat(dictAdstockDFs[k] for k in dictAdstockDFs.keys())
    
    try:
        for v in (LogVs):
            datadf[v] = pd.to_numeric(datadf[v])#.apply(lambda x: value(x))
            datadf[v] = datadf[v].apply(lambda x: math.log(x))
    except Exception as e:
        print(e)
    #remember depMeans is after log transform, if any.  depMeans is in the modeled space
    depMeans=datadf.groupby(IDnames[0:len(IDnames)-1])[depV[0]].mean()
    #tackling mean center now;  first break into sub dfs again to mean cneter by id vars
    #have to rebuild the dict as the original df has changed
    dictAdstockDFs=dict(tuple(datadf.groupby(IDnames[0:len(IDnames)-1])))
    for k in dictAdstockDFs.keys():
        for vv in MCVs:
            #in case not logged first, need to get to float
            dictAdstockDFs[k][vv] = pd.to_numeric(dictAdstockDFs[k][vv])
            dictAdstockDFs[k][vv]=dictAdstockDFs[k][vv]-dictAdstockDFs[k][vv].mean()

    #need to recombine them
    datadf=pd.concat(dictAdstockDFs[k] for k in dictAdstockDFs.keys())
    
    #make dummies for all IDs other than time
    datadf=pd.get_dummies(datadf,columns=IDnames[0:len(IDnames)-1])#,drop_first=True)
    #need to put dummies in first columns and not last where they are put by the get_dummies() so duetos ordering is easy
                 
    return depMeans,depV,IDnames, groups, transforms,knownSigns, origDep,datadf

def runModels(depV,IDnames,groups, knownSigns, origDep,datadf):
    from sklearn import linear_model
    import pandas as pd
    from numpy import arange, r_, reshape as np
    #get dependent
    #idxdep=[i for i,word in enumerate(groups) if word==('dependent')]
    #depV=rawdf.columns.values[idxdep].tolist()

    notDepV=[w for w in datadf.columns.values.tolist() if (w not in depV and w not in IDnames )]#if  word not in notIndList]
    mod1=linear_model.LinearRegression(normalize=False,fit_intercept=False)
    
    Y1=datadf[depV]
    X1=datadf[notDepV]
    #print(X1.columns.values)
    #order isn't preserved here
    cols=[]
    cols.append([C for C in X1.columns.values if C.startswith(tuple(IDnames[0:len(IDnames)-1]))])
    cols.append([C for C in X1.columns.values if not(C.startswith(tuple(IDnames[0:len(IDnames)-1])))])
    cols = [item for sublist in cols for item in sublist]
    newcolorder=[]
    for word in cols:
        if word not in newcolorder:
             newcolorder.append(word)
    
    #print(newcolorder)   
   
    X1= X1.reindex(columns=newcolorder)
    

    mod1.fit(X1,Y1)

    #print(mod1.score(X1,Y1),"\n",mod1.coef_,"\n", mod1.intercept_)
    #combine intercept and coef
    #make int a 1D array of length 1:
    int=[mod1.intercept_]
    #make coef a 1D array of whatever length it was before:
    coef=reshape(mod1.coef_,-1,1)
    #join them
    intcoef=r_[int,coef]
    return intcoef, X1, Y1

def decomp0(X1,Y1,origDep,intcoef,depV,depMeans,transforms,rawdf,IDnames):
    import math
    import pandas as pd
    from numpy import arange, r_, reshape
    #append columns of 1s to data
    X1.insert(0,'intOnes',1.)
    X2=pd.DataFrame(0,index=X1.index.values,columns=X1.columns.values,dtype='float64')
    for C in X1:
        X2[C]=pd.to_numeric(X1[C],errors='coerce')
    
    X1=X2.sort_index()
    
    #score to get transformed space decomps
    modSpaceDecomp= intcoef*X1
    #insert modeled target
    modSpaceDecomp.insert(0,depV[0],value=Y1[depV].values)
    #print(modSpaceDecomp.head())
    #compute residual
    modSpaceDecomp['total']=modSpaceDecomp.iloc[:,1:modSpaceDecomp.shape[1]].sum(axis=1)
    modSpaceDecomp['residual']=modSpaceDecomp[depV[0]]-modSpaceDecomp['total']
    modSpaceDecomp.drop('total',axis=1,inplace=True)
    
    #bring it to original space
    #if transform was none or blank (na) then do nothing
    #if trasnform was log, then exponentiate
    #if transform was logmc, then add back the mean in depMeans and then exponentiate
    
    #first make an index for dataframe for orig space decomps
    plainidx=arange(start=modSpaceDecomp.index.values.min(),stop=modSpaceDecomp.index.values.max()+1,dtype='int')
    
    #get a dict of transforms
    transformsDict=transforms.to_dict()
    if transformsDict[depV[0]]=='none':
        origSpaceDecomp=modSpaceDecomp
    elif transformsDict[depV[0]]=='log':
        origSpaceDecomp=pd.DataFrame(0,index=plainidx,columns=modSpaceDecomp.columns.values)
        for C in modSpaceDecomp:
            origSpaceDecomp[C]=modSpaceDecomp[C].apply(lambda x:math.exp(x))
    elif transformsDict[depV[0]]=='logmc':
        origSpaceDecomp=pd.DataFrame(0,index=plainidx,columns=modSpaceDecomp.columns.values)
        origSpaceDecomp=modSpaceDecomp #starting point is modspace, now add in mean values for depV
        #make depMeans a DF
        depMeans=pd.DataFrame(depMeans)
        #reset index on decomp data frame for differencing
        #first insert the columns back from rawdf
        idCols=rawdf.loc[3:rawdf.shape[0],IDnames[0:len(IDnames)-1]]
        origSpaceDecomp=origSpaceDecomp.join(idCols,how='outer')
        origSpaceDecomp.set_index(keys=IDnames[0:len(IDnames)-1],inplace=True)
        #make a dataframe with onecolumn
        intOnesPlus=pd.DataFrame(origSpaceDecomp['intOnes']+depMeans[depV[0]],columns=['intOnes']).set_index(plainidx)
        #drop the old column, insert the new column
        origSpaceDecomp.drop('intOnes',axis=1,inplace=True)
        origSpaceDecomp.insert(loc=0,column='intOnes',value=intOnesPlus.values)
        origSpaceDecomp.set_index(keys=plainidx,inplace=True)
        #that's a lot of fucking work to add in a column, finally apply the exp
        #first drop depV[0] column, no one knows what it is at this point
        origSpaceDecomp.drop(depV[0],axis=1,inplace=True)

        for C in origSpaceDecomp:
            origSpaceDecomp[C]=origSpaceDecomp[C].apply(lambda x:math.exp(x))
       
    #ok, we are done if additive model
    if transformsDict[depV[0]].startswith('log'):
        #if not additive, need to do column[2]*column[1]-column[1]=colum2decomp
        #just go in order for now
        origSpaceDecomp2=pd.DataFrame(0,index=plainidx,columns=origSpaceDecomp.columns.values)
        #will refigure residual
        origSpaceDecomp.drop('residual',axis=1,inplace=True)
        #print(origSpaceDecomp.columns.values)
        for idx,C in enumerate(origSpaceDecomp):        
            #print(idx,C)
            if idx==0:
                origSpaceDecomp2[C]=origSpaceDecomp[C]
            else:
                BigProd=origSpaceDecomp.iloc[:,0:idx+1].product(axis=1)
                LessBigProd=origSpaceDecomp.iloc[:,0:idx].product(axis=1)
                #print(origSpaceDecomp.iloc[:,0:idx+1].columns.values,"\n",origSpaceDecomp.iloc[:,0:idx].columns.values)
                Diff=BigProd-LessBigProd
                origSpaceDecomp2[C]=Diff
        origSpaceDecomp=origSpaceDecomp2
        
        #origSpaceDecomp['total']=modSpaceDecomp.iloc[:,1:modSpaceDecomp.shape[1]].sum(axis=1)
        
        
        #need to append original depV series . .. or reversed transformed dep series from above?
        #reverse transform Y1
        if transformsDict[depV[0]]=='log':
            origY1=Y1
            origY1.apply(lambda x:math.exp(x))
        elif transformsDict[depV[0]]=='logmc':
            origY1minus=Y1.join(idCols,how='outer')
            origY1minus.set_index(keys=IDnames[0:len(IDnames)-1],inplace=True)
            #make a dataframe with onecolumn
            origY1=pd.DataFrame(origY1minus[depV[0]]+depMeans[depV[0]],columns=[depV[0]]).set_index(plainidx)
            origY1[depV[0]]=origY1[depV[0]].apply(lambda x:math.exp(pd.to_numeric(x)))
        #now append the origY1[depV[0]]
        origSpaceDecomp.insert(loc=0,column=depV[0],value=origY1[depV[0]].values)
        origSpaceDecomp['total']=origSpaceDecomp.iloc[:,1:origSpaceDecomp.shape[1]].sum(axis=1)
        origSpaceDecomp['residual']=origSpaceDecomp[depV[0]]-origSpaceDecomp['total']
        origSpaceDecomp.drop('total',axis=1,inplace=True)
    return origSpaceDecomp,modSpaceDecomp

def makeGroupedDecomp(origSpaceDecomp,groups,depV):
    import pandas as pd
    from numpy import arange, r_, reshape
    #now need to sum up the columns to their groups . . .
    groupsDict=groups.to_dict()
    #get columns for decomps, includes dependent
    decompCols=["Base"]
    for g in groups:
        if not(g.endswith("id") ):
            decompCols.append(g)
    decompCols=list(set(decompCols))
    #make a new dataframe with those columns
    plainidx=arange(start=origSpaceDecomp.index.values.min(),stop=origSpaceDecomp.index.values.max(),dtype='int')
    groupedDecomp=pd.DataFrame(0,index=plainidx,columns=decompCols)
    #sum up to the groups
    for C in origSpaceDecomp:
            try: 
                if C!=depV:
                    groupedDecomp[groupsDict[C]]= groupedDecomp[groupsDict[C]]+pd.to_numeric(origSpaceDecomp[C])
            except:
                if C!=depV:
                    groupedDecomp['Base']= groupedDecomp['Base']+pd.to_numeric(origSpaceDecomp[C])

    #groupedDecomp.drop("dependent",axis=1,inplace=True)
    #output will still have totals, useful for period vs period change analysis
    return groupedDecomp

def calcElast(intcoef,X1,IDnames,groups, transforms):
    import pandas as pd
    from numpy import arange, r_, reshape
    #get intcoef name it from X1, remove dummies and base, and then compute elastiticies based on 
    #transforms
    #perhaps label them based on groups
    coefs=pd.Series(intcoef, index=X1.columns.values,name='Coef')
    transforms.name='Transforms'
    groups.name='Groups'
    indxs=[indx for indx in coefs.index.values if (not(indx.startswith(tuple(IDnames[0:len(IDnames)-1]))) and indx!="intOnes")]
    coefs2=coefs[indxs]
    transforms2=transforms[indxs]
    groups2=groups[indxs]
    #will need average of relevant X1 columns
    avg=[]
    for C in X1[indxs]:
        avg.append(pd.to_numeric(X1[indxs][C]).mean())
    es=[]
    for i,val in enumerate(coefs2):
        
        if transforms2[i].startswith('log'):
            es.append(val)
        else:
            es.append(val*.1*avg[i])
    elasticities=pd.Series(es,index=indxs,name='Elasticities') 
    return elasticities

def createDash(groupedDecomp,IDnames,rawdf,groups,elasts,fname):
    import plotly.plotly as py
    from plotly.offline import init_notebook_mode, iplot, plot
    import plotly.graph_objs as go
    import math
    import os
    #for decomps over time id, remove dependent from df
    subGroupedDecomp=groupedDecomp.drop('dependent',axis=1)
    #now use group by to get summed over all ids except time
    #first put id columns back in . . .
    idCols=rawdf.loc[3:rawdf.shape[0],IDnames[0:len(IDnames)]]
    for C in idCols:
        idCols[C]=pd.to_numeric(idCols[C],errors='ignore')
    subGroupedDecomp=subGroupedDecomp.join(idCols,how='outer')
    #subGroupedDecomp.set_index(keys=IDnames,inplace=True)
    tididx=[i for i,word in enumerate(groups) if word==('tid')]
    tidName=groups.index.values[tididx][0]
    aggGroupedDecomp=subGroupedDecomp.groupby(tidName).sum().sort_index()

    #split data in half for 'year over year' view to prevent user configuration of view:
    #even or odd number of tid values?
    numberInHalf=math.floor(len(aggGroupedDecomp.index.values)/2)
    if numberInHalf!=len(aggGroupedDecomp.index.values)/2:
        start=1
    else:
        start=0
    #print(numberInHalf)
    #this only works because already agged to one obs per time id
    YoYDecomp=aggGroupedDecomp.iloc[start:aggGroupedDecomp.shape[0],:]
    listPeriods=[]
    for i in arange(0,len(aggGroupedDecomp.index.values)-start):
        if i+1<=numberInHalf:
            listPeriods.append('Past')
        else:
            listPeriods.append('Current')

    YoYDecomp.insert(loc=0,column='Period',value=listPeriods)
    YoY=YoYDecomp.groupby('Period').sum().T
    YoY['Change']=(YoY['Current']-YoY['Past'])
    YoY=YoY.sort_values(by=['Change'])
    YoYTot=pd.DataFrame(YoY.sum()).T
    YoY=YoY.append(YoYTot)
    indexYoY = YoY.index
    indexYoY =  YoY.index.tolist()[0:len(YoY.index.tolist())-1]+['Total']
    indexYoY=pd.Index(indexYoY)
    YoY=YoY.set_index(indexYoY)
    YoY['PctChange']=YoY['Change']/YoY.loc['Total','Past']*100
    #plotly stuff
    traces=[]
    xforplot=[x for x in subGroupedDecomp[tidName]]
    for varnum in range(1,aggGroupedDecomp.shape[1]+1):
        traces.append(go.Bar(x=xforplot,y=aggGroupedDecomp.iloc[:,varnum-1].values,name=aggGroupedDecomp.columns.values[varnum-1]))

    layout = go.Layout(
        barmode='relative'
    )

    figTidDecomp = go.Figure(data=traces, layout=layout)
    #plot(go.Figure(data=traces, layout=layout))
    cneg='rgba(50, 171, 96, 0.7)'
    cpos='rgba(50, 171, 96, 0.7)'
    clist=[]
    for i,xx in enumerate(YoY["PctChange"]):
        if i==YoY["PctChange"].shape[0]-1:
            #total -- make orange and blue
            if xx<=0:
                clist.append('orange')
            else:
                clist.append('blue')
        else:
            if xx<=0:
                clist.append('red')
            else:
                clist.append('green')
    horztraces=[go.Bar(x=YoY["PctChange"],y=YoY.index.values,orientation='h',name='Current vs Past', 
                       marker=dict(color=clist),showlegend=False
                                  )]
    layout2=go.Layout(barmode='relative')
    figYoY=go.Figure(data=horztraces,layout=layout2)
    #plot(figYoY)

    etraces=[go.Bar(x=elasts.index.values,y=elasts,name='Elasticities',marker=dict(color='blue'),showlegend=False)]
    layout3=go.Layout(barmode='relative')
    figE=go.Figure(data=etraces,layout=layout3)

    from plotly import tools
    figAll=tools.make_subplots(rows=2, cols=2, specs=[[{'colspan':2},None], [{},{}]], subplot_titles=('Target Variable Decomposition','Drivers of Change (%)', 'Elasticities'))

    for i,tr in enumerate(figTidDecomp['data']):
        figAll.append_trace(figTidDecomp['data'][i],1,1)
    #figAll.append_trace(figTidDecomp['data'][0],1,1)
    figAll.append_trace(figYoY['data'][0],2,1)
    figAll.append_trace(figE['data'][0],2,2)
    #make title based on fname
    titleFileName, file_extension = os.path.splitext(fname)
    titleFileName=titleFileName[titleFileName.find('_')+1:]
    figAll['layout'].update(showlegend=True, title=titleFileName+' Model Results',barmode='relative')
    #plot(figAll)
    return figAll
    
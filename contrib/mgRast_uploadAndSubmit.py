# -*- coding: utf-8 -*-
"""
Created on Wed Apr 11 16:41:35 2018
This class is used to upload and submit data in mg-rast
Processing steps include:
1. Identify files in the mg-rast inbox that were previously submitted, and 
     move these to a user-specified directory for submitted files 
2. Find metadata file in user-specified directory, and use to identify which
     files in the directory need to be uploaded/submitted
3. Upload files that are not already in the mgRast inbox
4. Submit files that have not been previously submitted
5. Move submitted files to new directory

To run via: 
    Navigate to dirctory where script resides
    In command line/terminal: python mgrast_uploadAndSubmit.py auth_key [arguments]
         For help, use python mgrast_uploadAndSubmit.py -h
@author: nrobinson
"""

import json
import logging
import os
import subprocess
import pandas as pd
import datetime
import sys
import argparse
import time
import copy

class mgRastLoadSubmit:
    #Available arguments
    base_url = "http://api.mg-rast.org"
    api_version = "1" 
    url = base_url + '/' + api_version
    auth_key = None
    dir_path = os.getcwd()    
    search_dir = dir_path + "/data"
    submitted_dir = dir_path + "/submitted"
    log_file = dir_path + '/mgrast_uploadAndSubmit.log'
    
    # Submission details. These will automatically set to defaults if not changed below
    project_id = None  #Not needed if project_name provided
    project_name = None  #Default to info in metadata file
    priority = "3months"  #Change to None for default of 'never'
    assembled = None #Default is 0 for False 
    filter_ln = None #Default is 1 for True
    filter_ambig = None #Default is 1 for True
    dynamic_trim =None #Default is 1 for True
    dereplicate = 0 #Change to None for default of 1 for True
    bowtie = None #Default is 1 for True
    filter_ln_mult = None # Default is 2
    max_ambig = None # Default is 5 
    max_lqb = None # Default is 5 
    min_qual = None # Default is 15

    # Constructor.
    def __init__ (self):
        # Basic logger configuration. Log levels are DEBUG, INFO, WARN, ERROR, CRITICAL
        self.logger = logging.getLogger (__name__)
        self.logger.setLevel (logging.DEBUG)
        # Log file handler
        logger_fh = logging.FileHandler ('mgrast_uploadAndSubmit.log')
        logger_fh.setLevel (logging.DEBUG)
        # Log console handler
        logger_ch = logging.StreamHandler()
        logger_ch.setLevel (logging.INFO)
        # Register handlers with logger
        self.logger.addHandler (logger_fh)
        self.logger.addHandler (logger_ch)
        self.logger.info ('\nMG Rast Load&Submit started: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
		
    def print_config (self):
        '''
        Print configuration info for diagnostics
        '''
        self.logger.info ("base_url: " + self.base_url)
        self.logger.info ("api_version: " + self.api_version)
        self.logger.info ("search_dir: " + self.search_dir)
        self.logger.info ("submitted_dir: " + self.submitted_dir)
        self.logger.info ("log_file: " + self.log_file)
        
    def get_filesForUpload(self,fileInfoDF):
        '''
        "Package" files for upload to mgRast:
            1) Search data directory for valid metadata files
            2) Report expected sequencing files missing from data directory
            3) Create and output dictionary with metadata and associated seq files - excluding
                files previously uploaded to mgRast            
        '''
        self.logger.info ('\nMG Rast file verification started: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        #Make sure directory provided is a valid directory
        if os.path.isdir(self.search_dir) == False:
            self.logger.info (self.search_dir + ' is not a directory')
            sys.exit(0)
        else:
            #Initiate dictionary   
            filesToUpload={}   
            #For each csv in directory, get metadata and sequencing file names if csv is metadata file
            csvs = [self.search_dir+'/'+f for f in os.listdir(self.search_dir) if f.endswith('.csv')]
            for csv in csvs:
                metaFiles=[]; seqFiles=[]   #Lists of files
                #Import csv w/out header, test for header, add header or re-read with header
                dat = pd.read_csv(csv, header=None)
        		#Reject non-metadata files
                if len(dat.columns) != 2:
                    self.logger.info ('\n' + csv + ' is not a valid input file')
                else:
        			#If headers are correct, import file as-is
                    if dat[0][0] == 'metadata_file' and dat[1][0] == 'sample_file':
                        dat = pd.read_csv(csv)
                    else: 
        				#Add correct headers
                        dat.columns = ['metadata_file', 'sample_file']              
                        self.logger.info ("\nInvalid header. Using headers: 'metadata_file','sample_file' for file: " + csv)                    
                    #Add files to dictionary: metadata filename and all associated sequencing filenames
                    for meta in dat.metadata_file.unique():
                        metaFiles.append(meta)
                        sFiles=[row['sample_file'] for index, row in dat.iterrows() if row['metadata_file'] == meta]
                        sFiles=list(set(sFiles))
                        seqFiles.append(sFiles)                 
                    # Verify seq files exist in directory, remove from dictionary and report if absent   
                    allFiles = metaFiles + [item for sublist in seqFiles for item in sublist]
                    extensions = ['.fasta','.fastq','.xlsx','.zip','.tar','.tar.gz','.tar.bz2']
                    skipFiles=[]
                    self.logger.info ("\nSearching files for valid extension: " + " ".join([str(x) for x in extensions]))
                    for f in allFiles:
                        #Skip valid files
                        if f in os.listdir(self.search_dir):
                            pass
                        #If filename is in directory, check for good extension and report invalid files
                        elif f in [os.path.splitext(os.path.basename(filename))[0] for filename in os.listdir(self.search_dir)]:
                            #make sure extension is good
                            ind = [os.path.splitext(os.path.basename(filename))[0] for filename in os.listdir(self.search_dir)].index(f)
                            ext = os.path.splitext(os.path.basename(os.listdir(self.search_dir)[ind]))[1]
                            if ext in extensions:
                                pass
                            else:
                                self.logger.warning ("Sequence file referenced in metadata file not in data directory: " + f)
                                skipFiles.append(f)
                        #If file not in directory, throw error
                        else:
                            self.logger.warning ("Sequence file referenced in metadata file not in data directory: " + f)
                            skipFiles.append(f)
                    #Remove bad files from dictionary
                    for i in skipFiles:
                        if i in metaFiles:
                            #Remove the metadata file AND associated sequencing file(s)
                            mInd = metaFiles.index(i)
                            metaFiles.pop(mInd)
                            seqFiles.pop(mInd)
                        for j in seqFiles:
        					#Remove sequencing file individually
                            if i in j:
                                j.remove(i)
                                #If seqFiles list is empty, remove remove corresponding metadata file
                                if len(j) == 0:
                                    sInd = seqFiles.index(j)
                                    metaFiles.pop(sInd)
                                    seqFiles.pop(sInd)
                    allFiles = dict(list(zip(metaFiles, seqFiles)))                    
                    filesToUpload.update(allFiles)            
            #Check dictionary against mg-rast inbox; remove file(s) from dictionary if already in inbox
            if len(filesToUpload) > 0:
                allFilesInDir = copy.deepcopy(filesToUpload)
                #Ping SHOCK server to continue
                ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
                shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
                if shockStat == 1:
                    #Get contents of mgRast inbox, ignoring mgRast-created json files
                    inboxCurl=['curl', '-X', 'GET', '-H', 'Authorization: mgrast ' + self.auth_key, self.url + '/inbox']
                    try:
                        inboxJson=json.loads(subprocess.check_output(inboxCurl).decode('utf-8'))
                        if not 'ERROR' in inboxJson.keys():
                            inboxDict = {'fileName':[inboxJson['files'][i]['filename'] for i in range(0,len(inboxJson['files']))],
                             'fileID':[inboxJson['files'][i]['id'] for i in range(0,len(inboxJson['files']))],
                             'uploadTime':[inboxJson['files'][i]['timestamp'] for i in range(0,len(inboxJson['files']))],
                             'submissionID':[inboxJson['files'][i]['submission'] if 'submission' in inboxJson['files'][i].keys() else None for i in range(0,len(inboxJson['files']))]}
                            inboxDF=pd.DataFrame.from_dict(inboxDict)
                            #Add files already uploaded to fileInfoDF
                            checkBox=list(filesToUpload.keys()) + [j for i in list(filesToUpload.values()) for j in i]
                            for fToCheck in checkBox:
                                # Add to outputDF if already loaded and not already in fileInfoDF
                                inboxRow=[i for i, s in enumerate(inboxDF['fileName']) if fToCheck in s]
                                outDFRow=[i for i, s in enumerate(fileInfoDF['fileName']) if fToCheck in s]
                                if len(inboxRow) > 0 and len(outDFRow)==0:
                                    df = pd.DataFrame.from_dict({'fileName':[inboxDF['fileName'][inboxRow[0]]],'mgRastID':[inboxDF['fileID'][inboxRow[0]]],'study':None,'uploadedDate':'N/A','submitDate':None,'submitSuccessDate':None,'submissionID':None,'noExt':None})
                                    fileInfoDF=fileInfoDF.append(df)
                            #Remove uploaded files from list to upload
                            inInbox = [inboxDF['fileName'][i] for i in range(0,len(inboxDF)) if not inboxDF['fileName'][i].endswith('json')]
                            if len(inInbox) > 0:
                                #Get filenames without extensions                    
                                inInboxNoExt =copy.deepcopy(inInbox) #Make a copy to not change original
                                for f in range(0,len(inInboxNoExt)):
                                    if '.fast' in inInboxNoExt[f]:
                                        inInboxNoExt[f] = os.path.splitext(inInboxNoExt[f])[0]                                    
                                #Remove already existing files from dictionary 
                                remIndex=[]; remSeqName=[]
                                for i in range(0,len(filesToUpload)):
                                    #Get indices of previously uploaded metadata files
                                    if list(filesToUpload.keys())[i] in inInbox: 
                                        remIndex.append(i)
                                        break
                                    else:
                                        #If metadata file wasn't previously uploaded, check each seq file
                                        for j in range(0,len(list(filesToUpload.values())[i])):
                                            fName=list(filesToUpload.values())[i][j]
                                            if fName in inInboxNoExt:
                                                remSeqName.append(list(filesToUpload.values())[i][j])                
                                #Remove whole elements if metadata file was already in inbox
                                for p in remIndex:
                                    filesToUpload.pop(list(filesToUpload.keys())[p],0)                
                                #Remove sequencing files and whole elements if no seq files remain
                                if len(filesToUpload) > 0: 
                                    for sFile in remSeqName:
                                        for a in filesToUpload.values():
                                            try:
                                                a.remove(sFile)
                                            except ValueError:
                                                pass
                                    filesToUpload=dict((k, v) for k, v in filesToUpload.items() if v) 
                            self.logger.info ('\nMG Rast file verification completed: '+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                        else:
                            self.logger.error ("\nError while getting files for upload: " + inFiles['ERROR'])             
                    except subprocess.CalledProcessError as e:
                        self.logger.error ('\nCould not fetch inbox, error: ')
                        self.logger.error (e)
                        sys.exit()
                else:
                    self.logger.error ("\nServer is not responding, please try again later")
                    sys.exit()
                #Return dictionaries and fileInfoDF 
                if len(allFilesInDir) > 0:
                    if len(filesToUpload) > 0:
                        return allFilesInDir, filesToUpload, fileInfoDF
                    else:
                        self.logger.warning ("\nAfter file verification, no files were available for upload to mg-rast")     
                        return allFilesInDir,None,fileInfoDF
            else:
                self.logger.warning ("\nAfter file verification, no files were available for upload to mg-rast - may be no valid metadata file in directory")     
                sys.exit()
            
    
    def upload_files (self,fNames,fileInfoDF):  
        ''' 
        Upload files to mgrast, with 3 attempts made to upload each file. 
        Requires input fNames dictionary with metadata file + associated sequencing files
        Adds info about files uploaded to mgRast to fileInfoDF dataframe
        '''
        # Add info to log file
        self.logger.info ('\nMG Rast file upload started: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        if type(fNames) is dict and fNames !={}:
            #Unpack dictionary 
            allFiles = list(fNames.keys()) + sorted({x for v in fNames.values() for x in v})
        elif type(fNames) is list and fNames !=[]:
            allFiles=fNames
        if len(allFiles) > 0: 
            #Add filepath to filename
            allFiles= [self.search_dir+ '/' + i for i in os.listdir(self.search_dir) for f in allFiles if f in i] 
            #Ping SHOCK server to continue
            ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
            shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
            if shockStat == 1:
                #Upload files, trying 3 total times. If any files fails to upload in 3 attempts, abort the script
                for f in allFiles:
                    uploadCurl = ['curl','-X','POST','-H','Authorization: mgrast '+ self.auth_key,'-F','upload=@'+f,self.url+"/inbox"]
                    # Try to upload the file 3 times
                    tries = 0
                    while tries <= 2:
                        self.logger.info('\nUpload attempt ' + str(tries+1)+' for file: '+f)
                        uploadRes=subprocess.check_output (uploadCurl)
                        #try:
                        if '408 Request Timeout' not in uploadRes.decode("utf-8"):                             
                            # If uploadRes contains 'Request Timeout' then the script fails - returns byte-like data
                            uploadDict = json.loads(uploadRes.decode("utf-8"))
                            #Proceed if no error
                            if not 'ERROR' in uploadDict.keys():
                                df = pd.DataFrame.from_dict({'fileName':[uploadDict['status'].split(' (')[0]],'mgRastID':[uploadDict['status'].split(' (')[1].split(')')[0]],'study':[None],'uploadedDate':[uploadDict['timestamp']],'submitDate':[None],'submitSuccessDate':[None],'submissionID':[None],'noExt':[None]})
                                if df.shape[0] > 0:
                                    fileInfoDF=fileInfoDF.append(df)
                                break
                        #except subprocess.CalledProcessError as e:
                        else:
                            if tries == 2:
                                self.logger.error ('\nMG Rast file upload file upload aborted - File: ' + f +' did not uploaded in three attempts due to server timeouts')  #with error: ')
                                #self.logger.error (e)
                                sys.exit()
                            else:
                                time.sleep(2) #Pause 2 seconds and try again
                                tries += 1
                                continue
            else:
                self.logger.error ("\nServer is not responding, please try again later")
                sys.exit()        
            self.logger.info ('\nMG Rast file upload complete: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + '\n')
        else:
            self.logger.info ('\nFile upload failed, no files to upload: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))            
        return fileInfoDF
        
    def unpackZipped(self):
        '''
        Unpack zipped files in mgrast inbox
        '''    
        # Add info to log file
        self.logger.info ('\nChecking MG Rast inbox for zipped files to unpack: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        #Check for zipped file extensions
        extensions = ['.zip','.tar','.tar.gz','.tar.bz2']
        ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
        shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
        #Ping SHOCK server to continue
        if shockStat == 1:  
            inboxCurl = ['curl','-X','GET','-H','Authorization: mgrast '+self.auth_key,self.url+'/inbox']
            try:
                inRes = subprocess.check_output (inboxCurl)
                inFiles = json.loads(inRes.decode("utf-8"))
                #For each file in inbox, if file is zipped, unpack it
                for f in inFiles['files']:
                    if any(ext in f['filename'] for ext in extensions):            
                        fFormat = [extensions[i] for i in range(0,len(extensions)) if extensions[i] in f['filename']][0].split('.')[1]
                        self.logger.info ('unpacking: ' + f['filename'])                
                        #Unpack - removing zipped file
                        unpackCurl = ['curl','-X','POST','-H','Authorization: mgrast '+self.auth_key,'-F',"format="+fFormat,self.url+"/unpack/"+f['id']]
                        try:
                            unpackRes = subprocess.check_output (unpackCurl)
                        except subprocess.CalledProcessError as e:
                            self.logger.error ("Could not unpack: " + f['filename'] +".  Return code = " + e.returncode + ". Return output = " + e.output)
            except subprocess.CalledProcessError as e:
                self.logger.error ('\nCould not fetch inbox, error: ')
                self.logger.error (e)
                sys.exit()                                
        else:
            self.logger.error ("\nServer is not responding, please try again later")
            sys.exit() 
        self.logger.info ('\nMG Rast file unpacking complete: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    def submit_files(self,filesToSubmit,fileInfoDF):
        '''
        Submit files to mgrast
        Requires dictionary of files to submit, with metadata file and associated seq files. 
        Each 'package' is checked in mgRast to make sure it hasn't already been submitted, and metadata files are validated
        Returns fileInfoDF dataframe so uploaded files can be checked for submission
        '''  
        # Add info to log file
        self.logger.info ('\nMG Rast file submission started: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        #Ping SHOCK server to continue
        ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
        shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
        if shockStat == 1:            
            inboxCurl = ['curl','-X','GET','-H','Authorization: mgrast '+self.auth_key,self.url+'/inbox']
            try:
                #Get files in inbox, with mgRast ID and filename
                inboxRes = subprocess.check_output (inboxCurl)
                inFiles = json.loads(inboxRes.decode("utf-8"))
                inDict = {'fileName':[inFiles['files'][i]['filename'] for i in range(0,len(inFiles['files']))],'fileID':[inFiles['files'][i]['id'] for i in range(0,len(inFiles['files']))],'uploadTime':[inFiles['files'][i]['timestamp'] for i in range(0,len(inFiles['files']))],'submissionID':[inFiles['files'][i]['submission'] if 'submission' in inFiles['files'][i].keys() else None for i in range(0,len(inFiles['files']))]}
                inboxDF=pd.DataFrame.from_dict(inDict)
                #Remove previously submitted files from filesToSubmit dictionary
                submitted = [inboxDF['fileName'][i].split('.fast')[0] for i in range(0,len(inboxDF['fileName'])) if inboxDF['submissionID'][i] is not None and '.json' not in inboxDF['fileName'][i]]
                if submitted is not None and len(submitted) > 0:
                    #Update filesToUpload dictionary by removing those already submitted
                    for f in submitted:
                        if f in [elem for lst in filesToSubmit.values() for elem in lst]:
                            [seqList.remove(f) for seqList in filesToSubmit.values() if f in seqList]
                    #Remove metadata:seq pairs where seq list is empty
                    filesToSubmit={k:v for k,v in filesToSubmit.items() if len(v) > 0}
                if len(filesToSubmit) > 0:
                    #Create options dictionary for submission
                    opts={"project_id":self.project_id,"project_name":self.project_name,"priority":self.priority,"assembled":self.assembled,"filter_ln":self.filter_ln,"filter_ambig":self.filter_ambig,"dynamic_trim":self.dynamic_trim,"dereplicate":self.dereplicate,"bowtie":self.bowtie,"filter_ln_mult":self.filter_ln_mult,"max_ambig":self.max_ambig,"max_lqb":self.max_lqb,"min_qual":self.min_qual}        
                    #Fill data dictionary with default settings if user doesn't provide
                    data = {}
                    data['priority'] = opts['priority'] if opts['priority'] else 'never'
                    data['project_name'] = opts['project_name'] if opts['project_name'] else None
                    data['assembled'] = opts['assembled'] if opts['assembled'] else 0
                    data['filter_ln'] = opts['filter_ln'] if opts['filter_ln'] else 1
                    data['filter_ambig'] = opts['filter_ambig'] if opts['filter_ambig'] else 1
                    data['dynamic_trim'] = opts['dynamic_trim'] if opts['dynamic_trim'] else 1
                    data['dereplicate'] = opts['dereplicate'] if opts['dereplicate'] else 0
                    data['bowtie'] = opts['bowtie'] if opts['bowtie'] else 1
                    data['filter_ln_mult'] = opts['filter_ln_mult'] if opts['filter_ln_mult'] else 2
                    data['max_ambig'] = opts['max_ambig'] if opts['max_ambig'] else 5
                    data['max_lqb'] = opts['max_lqb'] if opts['max_lqb'] else 5
                    data['min_qual'] = opts['min_qual'] if opts['min_qual'] else 15
                    #For each set of metadata and seq files, complete data dictionary and submit package
                    for obj in range(0,len(filesToSubmit)): 
                        metaFile = list(filesToSubmit.keys())[obj]
                        #Validate metadata file and submit or exit
                        validateMetaCurl=['curl','-X','POST','-H','Authorization: mgrast '+self.auth_key,'-F','upload=@'+self.search_dir+'/'+metaFile,self.url+'/metadata/validate']
                        try:
                            validateMetaRes=subprocess.check_output(validateMetaCurl)
                            validateMetaJson=json.loads(validateMetaRes.decode("utf-8"))
                            if validateMetaJson['is_valid']==1:
                                self.logger.info ("MG Rast validation passed for metadata file: " + metaFile)
                                #Add study from metadata file, and initial submission attempt date
                                seqFiles = list(filesToSubmit.values())[obj]
                                metaDF = pd.read_excel(self.search_dir+'/'+metaFile,sheet_name='project')
                                study=metaDF['project_name'][1].replace(' ','')
                                fileInfoDF['noExt']=fileInfoDF['fileName'].str.split('.fast',expand=True)[0]
                                fileInfoDF.loc[fileInfoDF['noExt'].isin([metaFile]+seqFiles), 'study'] = study                
                                fileInfoDF.loc[fileInfoDF['noExt'].isin([metaFile]+seqFiles), 'submitDate'] = str(datetime.datetime.now()).replace(' ','T').split('.')[0]
                                #Map filenames to mgRast IDs
                                metaFile=list(fileInfoDF['mgRastID'][fileInfoDF['fileName']==metaFile])
                                seqFiles=list(fileInfoDF['mgRastID'][fileInfoDF['noExt'].isin(seqFiles)])
                                data['metadata_file']=metaFile[0]
                                data['seq_files'] = seqFiles
                                #Submit package of files
                                submitCurl = ['curl','-X','POST','-H','Authorization: mgrast '+self.auth_key,'-d',json.dumps(data),self.url+"/submission/submit"]  #Note - fake address does not throw error
                                try:
                                    subRes = subprocess.check_output (submitCurl)
                                    subResDict = json.loads(subRes.decode("utf-8"))
                                    self.logger.info ("Submitting to MG-RAST with the following parameters:")
                                    self.logger.info (json.dumps(data, sort_keys=True, indent=4))
                                    #Check submission dictionary for success
                                    if 'id' in subResDict.keys():
                                        subFiles=subResDict['info']['files']
                                        subMeta=subResDict['info']['metadata']
                                        #Update output dataframe
                                        fileInfoDF.loc[fileInfoDF['fileName'].isin(subFiles), 'submitSuccessDate'] = str(datetime.datetime.now()).replace(' ','T').split('.')[0]
                                        fileInfoDF.loc[fileInfoDF['fileName'].isin(subFiles), 'submissionID'] = subResDict['id']
                                        fileInfoDF.loc[fileInfoDF['mgRastID']==subMeta, 'submitSuccessDate'] = str(datetime.datetime.now()).replace(' ','T').split('.')[0]
                                        fileInfoDF.loc[fileInfoDF['mgRastID']==subMeta, 'submissionID'] = subResDict['id']            
                                except subprocess.CalledProcessError as e:
                                    self.logger.error ('\nSubmission failed, error: ')
                                    self.logger.error (e)                            
                            else:
                                self.logger.info ('\nMG Rast validation failed for metadata file: ' + metaFile+'. This file and associated sequencing files were NOT submiited')
                        except subprocess.CalledProcessError as e:
                            self.logger.error ('\nCould not perform metadata file validation, error: ')
                            self.logger.error (e)
                    self.logger.info ('\nSubmission attempt complete: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                else:
                    self.logger.info ('\nSubmission failed, NO files to submit: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))                
            except subprocess.CalledProcessError as e:
                self.logger.error ('\nCould not fetch inbox, error: ')
                self.logger.error (e)
                sys.exit()
        else:
            self.logger.error ("\nServer is not responding, please try again later")
            sys.exit()
        return fileInfoDF
        
    def cleanDirectory(self):
        '''
        Move files that have already been submitted to 'submitted' directory
        '''
        self.logger.info ('\nDirectory clean started: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        #Look for submitted files in inbox and get zip extensions
        extensions = ['.zip','.tar','.tar.gz','.tar.bz2']
        #Ping SHOCK server to continue
        ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
        shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
        if shockStat == 1: 
            inboxCurl = ['curl','-X','GET','-H','Authorization: mgrast '+self.auth_key,self.url+'/inbox']
            try:
                inboxRes = subprocess.check_output (inboxCurl)
                if 'webkey expired' in inboxRes.decode("ascii",errors="ignore"):
                    self.logger.info ('\nYour authorization key is expired - please try again. ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                    sys.exit()
                else:
                    inFiles = json.loads(inboxRes.decode("utf-8"))
                    submitted = [inFiles['files'][i]['filename'] for i in range(0,len(inFiles['files'])) if 
                         'submission' in inFiles['files'][i] and not inFiles['files'][i]['filename'].endswith('json')]
                    #Identify zip files in search_dir
                    zips = [os.path.splitext(f)[0] for f in os.listdir(self.search_dir) if any(ext in f for ext in extensions)]
                    #If more than xlsx in submitted list, move pertinent files to 'submitted' folder
                    if sum((itm.count("xlsx") for itm in submitted)) != len(submitted):
                        for f in submitted:
                            if f.endswith('xlsx'):
                                submitted.append(os.path.splitext(f)[0] + '.csv') 
                            if os.path.splitext(f)[0] in zips: #Add possible zip paths to move zip folders
                                add = [os.path.splitext(f)[0] + '.zip', os.path.splitext(f)[0] + '.tar', os.path.splitext(f)[0] + '.tar.gz', os.path.splitext(f)[0] + '.tar.bz2']  
                                submitted = submitted + add
                        for f in submitted:
                            if f in os.listdir(self.search_dir):
                                os.rename(self.search_dir + '/' + f, self.submitted_dir + '/' + f)
                    self.logger.info ('Directory clean complete: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            except subprocess.CalledProcessError as e:
                self.logger.error ('\nCould not fetch inbox, error: ')
                self.logger.error (e)
        else:
            self.logger.error ("\nServer is not responding, please try again later")
            sys.exit() 
            
    def checkSubmission(self,filesToCheck,fileInfoDF):
        ''' Check list of file names to see if they've gotten a submissionID '''         
        #Ping SHOCK server to continue
        ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
        shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
        if shockStat == 1:
            #Get inbox
            inboxCurl = ['curl','-X','GET','-H','Authorization: mgrast '+self.auth_key,self.url+'/inbox']
            try:
                inboxRes = subprocess.check_output (inboxCurl)
                inFiles = json.loads(inboxRes.decode("utf-8"))
                inDict = {'fileName':[inFiles['files'][i]['filename'] for i in range(0,len(inFiles['files']))],'fileID':[inFiles['files'][i]['id'] for i in range(0,len(inFiles['files']))],'uploadTime':[inFiles['files'][i]['timestamp'] for i in range(0,len(inFiles['files']))],'submissionID':[inFiles['files'][i]['submission'] if 'submission' in inFiles['files'][i].keys() else None for i in range(0,len(inFiles['files']))]}
                inboxDF=pd.DataFrame.from_dict(inDict)
                #Check for submissionIDs for files in filesToCheck                
                filesToCheck=list(fileInfoDF['fileName'][fileInfoDF['noExt'].isin(filesToCheck)]) #Get full filename
                #If filename is in inbox, add submissionID and date to file info dataframe if submissionID is available
                for fn in filesToCheck:
                    if fn in list(inboxDF['fileName']) and list(inboxDF['submissionID'][inboxDF['fileName']== fn])[0] is not None:
                        fileInfoDF['submissionID'][fileInfoDF['fileName']==fn]=list(inboxDF['submissionID'][inboxDF['fileName']== fn])[0]
                        fileInfoDF['submitSuccessDate'][fileInfoDF['fileName']==fn]=str(datetime.datetime.now()).replace(' ','T').split('.')[0]
                print ('\Submission check complete: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            except subprocess.CalledProcessError as e:
                self.logger.error ('\nCould not fetch inbox, error: ')
                self.logger.error (e)   
        else:
            print ("\nServer is not responding, please try again later")
            sys.exit()        
        return fileInfoDF
        

def main():
    procFiles = mgRastLoadSubmit()
    #Get user-input arguments
    parser = argparse.ArgumentParser (description="Upload and submit files - MG RAST. For API setting options go to api.mg-rast.org/api.html")
    parser.add_argument ("auth_key", 
                 help="authorization key (auth_key) [Required]")
    parser.add_argument ("-url", "--base_url", dest="base_url", 
                 help="base MG RAST URL [default: " + procFiles.base_url + "/1]")
    parser.add_argument ("-v", "--api_version", dest="api_version", 
                 help="API version [default: 1]")
    parser.add_argument ("-search_dir", "--search_dir", dest="search_dir", 
                 help="directory to search for data [default: " + procFiles.search_dir + "]")
    parser.add_argument ("-submitted_dir", "--submitted_dir", dest="submitted_dir", 
                 help="directory to which to move submitted data [default: " + procFiles.submitted_dir + "]")
    parser.add_argument ("-log_file", "--log_file", dest="log_file", 
                 help="output file for log info [default: " + procFiles.log_file + "]") 
    parser.add_argument ("-proj_id", "--project_id", dest="project_id", 
                 help="project ID for data submission [Not Required if metadata files contains project name, default: NONE]")
    parser.add_argument ("-proj_name", "--project_name", dest="project_name", 
                 help="project Name for data submission [Not Required if metadata files contains project name, default: NONE]")
    parser.add_argument ("-p", "--priority", dest="priority", 
                 help="priority setting for data submission [default: 3months]")
    parser.add_argument ("-a", "--assembled", dest="assembled", 
                 help="assembled setting for data submission [default: 0]")
    parser.add_argument ("-f_ln", "--filter_ln", dest="filter_ln", 
                 help="filter ln setting for data submission [default: 1]")
    parser.add_argument ("-f_ambig", "--filter_ambig", dest="filter_ambig", 
                 help="filter ambig setting for data submission [default: 1]")
    parser.add_argument ("-dyn_trim", "--dynamic_trim", dest="dynamic_trim", 
                 help="dynamic trim setting for data submission [default: 1]")
    parser.add_argument ("-derep", "--dereplicate", dest="dereplicate", 
                 help="dereplicate setting for data submission [default: 0]")
    parser.add_argument ("-bowtie", "--bowtie", dest="bowtie", 
                 help="bowtie setting for data submission [default: 1]")
    parser.add_argument ("-f_ln_mult", "--filter_ln_mult", dest="filter_ln_mult", 
                 help="filter ln mult setting for data submission [default: 2]")
    parser.add_argument ("-max_ambig", "--max_ambig", dest="max_ambig", 
                 help="max ambig setting for data submission [default: 5]")
    parser.add_argument ("-max_lqb", "--max_lqb", dest="max_lqb", 
                 help="max lqb setting for data submission [default: 5]")
    parser.add_argument ("-min_qual", "--min_qual", dest="min_qual", 
                 help="min qual setting for data submission [default: 15]")
    args = parser.parse_args()
    #Set defaults
    if args.auth_key is not None:
        procFiles.auth_key = args.auth_key
    if args.base_url is not None:
        procFiles.base_url = args.base_url    
    if args.api_version is not None:
        procFiles.api_version = args.api_version
    if args.search_dir is not None:
        procFiles.search_dir = args.search_dir
    if args.submitted_dir is not None:
        procFiles.submitted_dir = args.submitted_dir
    if args.log_file is not None:
        procFiles.log_file = args.log_file
    if args.project_id is not None:
        procFiles.project_id = args.project_id
    if args.project_name is not None:
        procFiles.project_name = args.project_name
    if args.priority is not None:
        procFiles.priority = args.priority
    if args.assembled is not None:
        procFiles.assembled = args.assembled
    if args.filter_ln is not None:
        procFiles.filter_ln = args.filter_ln
    if args.filter_ambig is not None:
        procFiles.filter_ambig = args.filter_ambig
    if args.dynamic_trim is not None:
        procFiles.dynamic_trim = args.dynamic_trim
    if args.dereplicate is not None:
        procFiles.dereplicate = args.dereplicate
    if args.bowtie is not None:
        procFiles.bowtie = args.bowtie
    if args.filter_ln_mult is not None:
        procFiles.filter_ln_mult = args.filter_ln_mult
    if args.max_ambig is not None:
        procFiles.max_ambig = args.max_ambig
    if args.max_lqb is not None:
        procFiles.max_lqb = args.max_lqb
    if args.min_qual is not None:
        procFiles.min_qual = args.min_qual
    #Throw warning if required auth_key not provided
    procFiles.print_config()
    if procFiles.auth_key is None:
        procFiles.logger.error ("auth_key must be supplied")
    #Ping SHOCK server to continue
    ping= ['curl', 'https://api.mg-rast.org/heartbeat/SHOCK']
    shockStat = json.loads(subprocess.check_output (ping).decode("utf-8"))['status']
    if shockStat == 1:
        #Run processing steps ##################################################
        #Open or create fileStats csv
        if os.path.isfile(procFiles.dir_path+'/fileStats.csv'):
            fileInfoDF = pd.read_csv(procFiles.dir_path+'/fileStats.csv')
        else:
            fileInfoDF=pd.DataFrame(columns=['fileName','mgRastID','study','uploadedDate','submitDate','submitSuccessDate','submissionID','noExt'])
        #Clean up directory
        procFiles.cleanDirectory()
        if len(os.listdir(procFiles.search_dir))>0:
            #Identify: files in directory of correct format and in a metadata file (allFilesInDir)
            #          all valid files needing to be uploaded (filesToUpload)
            allFilesInDir,filesToUpload,fileInfoDF=procFiles.get_filesForUpload(fileInfoDF)                 
            if filesToUpload is not None:
                #Upload, with 3 total attempts made to upload all files, update fileInfoDF if applicable
                fileInfoDF=procFiles.upload_files(fNames=filesToUpload,fileInfoDF=fileInfoDF)
            #Submit any files that weren't previously submitted, with retries for up to 3 hours              
            #unpack zipped files in mgrast inbox     
            procFiles.unpackZipped() 
            #Submit, with verification that each file of interst hasn't been previously submitted
            fileInfoDF=procFiles.submit_files(filesToSubmit=allFilesInDir,fileInfoDF=fileInfoDF)
            #If any files of interest arent' submitted, keep checking every 30 min for up to 3 hours 
            filesToCheck=list(allFilesInDir.keys()) + sorted({x for v in allFilesInDir.values() for x in v}) #Unpack
            reCheck=0        
            while reCheck < 7:                
                #Filter to files of interest and without submissionIDs in fileInfo dataframe        
                needsSubID=list(set(filesToCheck).intersection(list(fileInfoDF['noExt'][fileInfoDF['submissionID'].isnull()])))
                if len(needsSubID)==0:
                    procFiles.logger.info('\nAll files from initial upload have successfully submitted: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                    break                
                else:
                    procFiles.logger.info('\nRechecking for file submissions: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                    time.sleep(1800)  #sleep is 30 mins
                    #Try to add submission info for each file
                    fileInfoDF=procFiles.checkSubmission(filesToCheck=needsSubID,fileInfoDF=fileInfoDF)
                    #Refresh list of files without submissionIDs
                    new_needsSubID = list(set(filesToCheck).intersection(list(fileInfoDF['noExt'][fileInfoDF['submissionID'].isnull()])))
                    if len(new_needsSubID) == 0:
                        procFiles.logger.info('\nAll files from initial upload have successfully submitted: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                        break
                    else:
                        if reCheck < 5:
                            reCheck = reCheck+1
                            continue
                        else:
                            procFiles.logger.error ("\nSubmission was unsuccessful after 3 hours. Files not submitted: " + "; ".join([str(x) for x in new_needsSubID]))
                            if fileInfoDF.shape[0] > 0:
                                fileInfoDF.to_csv(procFiles.dir_path+'/fileStats.csv',index=False)
                            sys.exit()       
            #Clean up directory
            procFiles.cleanDirectory()     
        else:               
            procFiles.logger.info ('\nFile upload and submit failed, there are no unsubmitted files in the data directory: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            sys.exit()
        #Write csv, whether updated or not
        if fileInfoDF.shape[0] > 0:
            fileInfoDF.to_csv(procFiles.dir_path+'/fileStats.csv',index=False)
    else:
        procFiles.logger.error ("\nServer is not responding, please try again later")
        sys.exit()

if __name__=="__main__":
    main()
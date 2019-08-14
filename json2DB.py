import json
import sys
#filer = "clinical.project-TCGA-HNSC.2017-12-14T12_15_13.069787.json"
#cType = "HNSC"
#filer = "clinical.project-TCGA-OV.2018-01-30T06_26_17.307051.json"
#cType = "OV"
#filer = "clinical.project-TCGA-LUSC.2018-01-11T18_45_17.986081.json"
#cType = "LUSC"
#filer = "clinical.project-TCGA-STAD.2018-01-25T12_54_07.644114.json"
#cType = "STAD"
#filer = "clinical.project-TCGA-LUAD.2018-02-27.json"
#cType = "LUAD"
#filer = "clinical.project-TCGA-LIHC.2018-02-07T10_39_45.741561.json"
#cType = "LIHC"
#filer = "clinical.project-TCGA-COAD.2018-02-27.json"
#cType = "COAD"
#filer = "clinical.project-TCGA-READ.2018-02-27.json"
#cType = "READ"
#filer = "clinical.project-TCGA-BRCA.2018-05-11.json"
#cType = "BRCA"
#filer = "clinical.project-TCGA-BLCA.2018-05-11.json"
#cType = "BLCA"
#filer = 'clinical.project-TCGA-UCEC.2018-05-22.json'
#cType = 'UCEC'
#filer = 'clinical.project-TCGA-KIRC.2018-06-17.json'
#cType = 'KIRC'
#filer = 'clinical.project-TCGA-KIRP.2018-06-17.json'
#cType = 'KIRP'
#filer = 'clinical.project-TCGA-KICH.2018-06-19.json'
#cType = 'KICH'
#filer = 'clinical.cases_selection.2018-10-18.json'
#cType = 'GBM'
#filer = 'clinical.project-TCGA-PAAD.2018-10-18.json'
#cType = 'PAAD'
#filer = 'clinical.project-TCGA-THCA.2018-11-14.json'
#cType = 'THCA'
# filer = 'clinical.project-TCGA-CHOL.2019-07-29.json'
# cType = 'CHOL'
# filer = 'clinical.project-TCGA-UCS.2019-07-31.json'
# cType = 'UCS'
# filer = 'clinical.project-TCGA-DLBC.2019-08-02.json'
# cType = 'DLBC'
# filer = 'clinical.project-TCGA-UVM.2019-08-06.json'
# cType = 'UVM'
# filer = 'clinical.project-TCGA-ACC.2019-08-08.json'
# cType = 'ACC'
# filer = 'clinical.project-TCGA-THYM.2019-08-12.json'
# cType = 'THYM'
filer = 'clinical.project-TCGA-PCPG.2019-08-14.json'
cType = 'PCPG'
# filer = 'clinical.project-TCGA-SKCM.2019-08-12.json'
# cType = 'SKCM'


sql = "clinical_data.sql"
print "Reading {} data".format(filer)
with open(filer, 'r') as f :
  j = json.load(f)

print "Finished reading. Got {0} cases. Extracting and converting data to SQL".format(len(j))

for l in j :
    # print "case_id------------", l['case_id'] # Alternative to Primary key
    # print "submitter_id-------", l['demographic']['submitter_id'].split('_')[0] #PRIMARY KEY
    # print "age_at_diagnosis---", l['diagnoses'][0]['age_at_diagnosis'] #Float. Days after birth -> transform to years
    # try:
    #     days_to_death = l['demographic']['days_to_death']
    # except KeyError:
    #     days_to_death = None
    # print "days_to_death------", type(days_to_death) #Float. Days to death. None if still alive?
    # print "gender-------------", l['demographic']['gender'] #Either 'female' or 'male'
    # print "race---------------", l['demographic']['race'] #String with the race. Longest is 32 characters
    # print "ethnicity----------", l['demographic']['ethnicity'] #String. Longest is 22 characters
    # print "year_of_birth------", l['demographic']['year_of_birth'] #Integer or None
    # print "year of death------", l['demographic']['year_of_death'] #Integer or None
    # print "weight-------------", l['exposures'][0]['weight'] #Integer ?
    # print "height-------------", l['exposures'][0]['height'] #Integer ?
    # print "bmi----------------", l['exposures'][0]['bmi'] #Float / Integer ?
    # print "years smoked-------", l['exposures'][0]['years_smoked'] # Float, maybe it is possible to convert it to int
    # print "cigarretes per day-", l['exposures'][0]['cigarettes_per_day'] # Float or None
    # print "alcohol history----", l['exposures'][0]['alcohol_history'] # String: 'yes' or 'no'
    # print "alcohol intensity-",  l['exposures'][0]['alcohol_intensity'] #Integer ??

    try :
        store = True
        if len(l['exposures']) > 1 :
            print "WARNING: case {0} has more than one exposure".format(l)
            store = False

        if len(l['diagnoses']) > 1 :
            print "WARNING: case {0} has more than one diagnose".format(l['case_id'])
            store = False
    except KeyError, e :
        print "Key [{}] not found in entry {}.".format(e, str(l))
        store = False
        next

    if store :
        with open(sql, 'a') as f :
            f.write('INSERT INTO patient VALUES(')
            f.write("'{1}', '{0}', ".format(l['case_id'], l['demographic']['submitter_id'].split('_')[0]))
            #Float. Days after birth -> transform to years
            if l['diagnoses'][0]['age_at_diagnosis'] == None :
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['diagnoses'][0]['age_at_diagnosis']/365)))

            #Float. Days to death. None if still alive?	   	
	    # JEC: seems that this field has been changed to be under  demographic key
            # if l['diagnoses'][0]['days_to_death'] == None :
	    try:
	    	days_to_death = l['demographic']['days_to_death'] 
	    except KeyError:
	    	days_to_death = None
	    	print "days_to_death not found in entry {}, set to null.".format(l['case_id'])
	    # if l['demographic']['days_to_death'] == None :
        #         f.write("NULL, ")
        # else :
	    # 	f.write("{}, ".format(str(int(l['diagnoses'][0]['days_to_death']))))
	    # 	f.write("{}, ".format(str(int(l['demographic']['days_to_death']))))
	    if days_to_death == None :
                f.write("NULL, ")
            else :
                # f.write("{}, ".format(str(int(l['diagnoses'][0]['days_to_death']))))
                f.write("{}, ".format(str(int(l['demographic']['days_to_death']))))

            if l['demographic']['gender'] == None : #Either 'female' or 'male'
                f.write("NULL, ")
            else :
                f.write("'{}', ".format(l['demographic']['gender']))

            if l['demographic']['race'] == None : #String with the race. Longest is 32 characters
                f.write("NULL, ")
            else :
                f.write("'{}', ".format(l['demographic']['race']))

            if l['demographic']['ethnicity'] == None : #String. Longest is 22 characters
                f.write("NULL, ")
            else :
                f.write("'{}', ".format(l['demographic']['ethnicity']))

            if l['demographic']['year_of_birth'] == None: #Integer or None
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['demographic']['year_of_birth'])))

            if l['demographic']['year_of_death'] == None : #Integer or None
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['demographic']['year_of_death'])))

            if l['exposures'][0]['weight'] == None : #Integer ?
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['exposures'][0]['weight'])))

            if l['exposures'][0]['height'] == None : #Integer ?
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['exposures'][0]['height'])))

            if l['exposures'][0]['bmi'] == None : #Float / Integer ?
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['exposures'][0]['bmi'])))

            if l['exposures'][0]['years_smoked'] == None : # Float, maybe it is possible to convert it to int
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(int(l['exposures'][0]['years_smoked']))))

            if l['exposures'][0]['cigarettes_per_day'] == None : # Float or None
                f.write("NULL, ")
            else :
                f.write("{}, ".format(str(l['exposures'][0]['cigarettes_per_day'])))

            if l['exposures'][0]['alcohol_history'] == None : # String: 'yes' or 'no'
                f.write("NULL, ")
            else :
                f.write("'{}', ".format(l['exposures'][0]['alcohol_history']))

            if l['exposures'][0]['alcohol_intensity'] == None : #Integer ??
                f.write("NULL,")
            else :
                f.write("'{}',".format(l['exposures'][0]['alcohol_intensity']))
            f.write("'{}');\n".format(cType))

print "Finished the conversion. Records stored in {}".format(sql)

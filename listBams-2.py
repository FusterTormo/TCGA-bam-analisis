import os
import glob
import requests
import json
import urllib
import re

# Get the repository to get the cancer samples
print "Where to go?\n===================\n\t[1] /g/strcombio/fsupek_cancer1/TCGA_bam/\n\t[2] /g/strcombio/fsupek_cancer2/TCGA_bam/\n\t[3] /g/strcombio/fsupek_cancer3/TCGA_bam/"
aux = int(raw_input("Your choice: "))
if aux == 1 :
    root = '/g/strcombio/fsupek_cancer1/TCGA_bam/'
elif aux == 2 :
    root = '/g/strcombio/fsupek_cancer2/TCGA_bam/'
elif aux == 3 :
    root = '/g/strcombio/fsupek_cancer3/TCGA_bam/'
else :
    raise ValueError("Invalid option")

cancer = []
print "Getting cancer names"
#Go to directory where all the bams are to get the different cancers stored
for dirname, dirnames, filenames in os.walk(root):
    # Get the cancers.
    for subdirname in dirnames:
        cancer.append(subdirname)
    break

print "\nCancers found: \n==================="
it = 0
for c in cancer :
    print "\t[{}] - {}".format(it,c)
    it += 1
print "\t[{}] - all".format(it)
ind = int(raw_input("===================\nFrom which cancer create the data? "))
print "Getting info for {} cancer".format(cancer[ind])
try :
    cancer = [ x for x in cancer if cancer.index(x) == ind]
except IndexError :
    pass

#Get submitter_ids from the selected subcancer
for c in cancer :
    path = "{}{}".format(root, c) #Path to the subcancer directory

    for dirname, dirnames, filenames in os.walk(path) :
        for submitter in dirnames : #For each submitter_id directory
            newPath = "{}/{}".format(path,submitter)
            for rut, dirs, files in os.walk(newPath) :
                for uuid in dirs : #For each bam folder in the submitter_id directory
                    os.chdir("{}/{}".format(newPath,uuid))
                    bam = glob.glob('*.bam')

                    #At this step we have the needed information: UUID, submitter_id, and name of the bam
                    try :
                        #Find platform, experimental_strategy, sequencing center, analyte (DNA, RNA), and sample type (Blood control, tumor solid ...) using TCGA API
                        url = 'https://api.gdc.cancer.gov/files/'
                        fields = '?fields=experimental_strategy,platform,cases.samples.portions.analytes.aliquots.center.short_name,cases.samples.sample_type,cases.samples.portions.analytes.analyte_type'

                        query = url + uuid + fields
                        response = requests.get(query)
                        res = response.json()
                        if 'platform' in res['data'] :
                            platform = res['data']['platform']
                        else :
                            platform = "NULL"

                        if 'experimental_strategy' in res['data'] :
                            exp = "'" + res['data']['experimental_strategy'] + "'"
                        else :
                            exp = "NULL"

                        #Gather analyte type (DNA, WGA)
                        molecule = "'" + res['data']['cases'][0]['samples'][0]['portions'][0]['analytes'][0]['analyte_type'] + "'"
                        #Gather information if bam is tumor tissue, normal tissue, normal blood...
                        tumor = "'" + res['data']['cases'][0]['samples'][0]['sample_type'] + "'"
                        #Gather information from sequencing center
                        seqCenter = "'" + res['data']['cases'][0]['samples'][0]['portions'][0]['analytes'][0]['aliquots'][0]['center']['short_name'] + "'"

                        if exp != "\'WXS\'" and exp != "\'WGS\'" :
                            print "WARNING: Downloaded {} from {}. UUID: {}".format(exp, submitter, uuid)
                            exp = "NULL"

                        # Warn in case more information than expected found in each classification
                        if len(res['data']['cases']) > 1 :
                            print "WARNING: More than 1 case found. Submitter: {}. UUID: {}".format(submitter, uuid)
                            print "\t{}".format(res['data']['cases'])

                        if len(res['data']['cases'][0]['samples']) > 1 :
                            print "WARNING: More than 1 sample found. Submitter: {}. UUID: {}".format(submitter, uuid)
                            print "\t{}".format(res['data']['cases'][0]['samples'])

                        if len(res['data']['cases'][0]['samples'][0]['portions']) > 1 :
                            print "WARNING: More than 1 portion found. Submitter: {}. UUID: {}".format(submitter, uuid)
                            print "\t{}".format(res['data']['cases'][0]['samples'][0]['portions'])

                        if len(res['data']['cases'][0]['samples'][0]['portions'][0]['analytes']) > 1 :
                            print "WARNING: More than 1 analyte found. Submitter: {}. UUID: {}".format(submitter, uuid)
                            print "\t{}".format(res['data']['cases'][0]['samples'][0]['portions'][0]['analytes'])

                        if len(res['data']['cases'][0]['samples'][0]['portions'][0]['analytes'][0]['aliquots']) > 1 :
                            print "WARNING: More than 1 aliquot found. Submitter: {}. UUID: {}".format(submitter, uuid)
                            print "\t{}".format(res['data']['cases'][0]['samples'][0]['portions'][0]['analytes'][0]['aliquots'])


                        #Write the extracted information in the SQL file
                        sql = root + c + '/sample_data.sql'
                        with open(sql, "a") as f :
                            order = "INSERT INTO sample(uuid,bamName,wxs,tumor,platform,analyte,seqCenter,submitter,refGene,deleted) VALUES(\'{}\',\'{}\',{},{},\'{}\',{},{},\'{}\','hg38','No');\n".format(uuid,bam[0],exp,tumor,platform,molecule,seqCenter,submitter)
                            f.write(order)

                    except ValueError, er :
                        print "ERROR!! found error when searching {} in submitter {}. UUID {}".format(query,submitter,uuid)
                        print er
                        next
                    except KeyError, e :
                        print "Not found key {} in query {}".format(e, query)
                        print "Returned object {}\n".format(res)

                break
        break

print "Program finished successfully. SQL data stored at {}".format(sql)

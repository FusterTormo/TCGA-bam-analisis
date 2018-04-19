import requests
import json
import urllib
import os

endp='https://api.gdc.cancer.gov/cases/'
fields = 'fields=submitter_id'
'''
To download new cancer type, change the value of this variable, and
CREATE A DIRECTORY IN /mnt/data/TCGA_bam with the name of the variable you wrote !!!
'''
#subtype = "TCGA-HNSC"
#subtype = 'TCGA-OV'
#subtype = 'TCGA-LUSC'
#subtype = 'TCGA-STAD'
#subtype = 'TCGA-LUAD'
#subtype = 'TCGA-LIHC'
#subtype = 'TCGA-COAD'
#subtype = 'TCGA-READ'
#subtype = 'TCGA-BRCA'
subtype = 'TCGA-BLCA'
#Get the number of samples in a specific cancer subtype
filters = '{"op":"=","content":{"field": "project.project_id", "value":["' + subtype +'"]}}'
size = 1
query = endp + "?" + fields + "&filters=" + urllib.quote_plus(filters) + "&size=" + str(size)
response = requests.get(query)

#Get the number of elements in order to get all the data once (no pagination)
res = response.json()
size = res["data"]["pagination"]["total"]
print "Size received: " + str(size) + " samples comprise all the data. Wait..."

#Repeat the query to get all the submitter ids without pagination
query = endp + "?" + fields + "&filters=" + urllib.quote_plus(filters) + "&size=" + str(size)
response = requests.get(query)
res = response.json()
hits = res["data"]["hits"] #Each hit has a pair 'submitter_id : value'
print "Found " + str(len(hits)) + " submitter ids. Getting manifest for bams for each submitter id..."
success = 0
fail = 0
for h in hits :
    s_id = h["submitter_id"]
    endp = 'https://api.gdc.cancer.gov/files/'

    filters = '{"op": "and","content": [{"op": "=",	"content": {"field": "cases.submitter_id", "value": ["' + s_id + '"]}},{"op" : "=", "content" : {"field" : "data_format","value" : ["BAM"]}}, {"op" : "=", "content" : {"field" : "experimental_strategy", "value" : ["WXS"]} }, {"op":"=","content" :{"field" : "cases.project.project_id" ,"value" : ["' + subtype + '"]}}]}'
    #Get only sample_ids for the bams
    fields = 'fields=file_id'
    query = endp + "?" + fields + "&filters=" + urllib.quote_plus(filters) + "&return_type=manifest"
    response = requests.get(query)
    if response.status_code == 200 :
        #The output of the request is the manifest in text format. Store it in a file with the name of the submitter id
        mani = response.text
        #Create the folder where the manifest will be stored.
        folder = "/mnt/data/TCGA_bam/" + subtype + "/" + s_id
        arx = folder + "/" + s_id + ".txt"
        print "Writing manifest " + arx + " in " + folder
        os.system("mkdir " + folder)
        fi = open(arx, "w")
        fi.write(mani)
        fi.close()
        success +=1
    else :
        print "Error found in " + s_id
        print response.text
        fail += 1

print "END successfully. " + str(success) + " manifests downloaded. " + str(fail) + " errors"

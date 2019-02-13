import requests
import json
import re
import urllib
import os
import masterScriptConstants as mc
import subprocess

def availableCancers() :
    downloaded = mc.cancerPath.keys()
    cancers = []
    endp = "https://api.gdc.cancer.gov/projects/"
    fields = "fields=project_id"
    size = '100'
    query = "{}?{}&size={}".format(endp,fields,size)
    print "INFO: Get TCGA information through API"
    response = requests.get(query)
    if response.status_code == 200 :
        res = response.json()
        for i in res['data']['hits'] :
            if i['project_id'].startswith("TCGA-") :
                aux = i['project_id'].split("-")[1]
                if aux not in downloaded :
                    cancers.append(i['project_id'])
        cancers.sort()
    else :
        print "ERROR: Error found. Description"
        print response.text

    return cancers

def downloadSample(case) :
    print "INFO: Downloading {}".format(case)
    if os.path.isfile("{}.txt".format(case)) :
        os.system("rm */logs/*parcel")
        os.system("/mnt/data/gdc-client download -t {} -m {}.txt -d . -n 40".format(mc.pathToken, case))
        os.system("sqlite3 {} \"UPDATE sample SET deleted='No' WHERE submitter='{}';\"".format(mc.pathDb, case))
    else :
        print "ERROR: Manifest not found"

def downloadSample_old(ids) :
    '''Gets a list of bam UUIDS and downloads them without using the API. Uses the token stored in /mnt/data. To change this value, go to masterScriptConstants.py'''
    processes = []
    for i in ids :
        print "INFO: Downloading {}".format(i)

        endp = "https://api.gdc.cancer.gov/data/{}".format(i)
        with open(mc.pathToken,"r") as token:
            token_string = str(token.read().strip())

        response = requests.get(endp, headers = { "Content-Type": "application/json", "X-Auth-Token": token_string })
        print response.status_code
        try :
            response_head_cd = response.headers["Content-Disposition"]
        except :
            print "CAGADA"
        filename = re.findall("filename=(.+)", response_head_cd)[0]

        with open(filename, "wb") as output_file:
            output_file.write(response.content)

        #Run samtools index. Bam index is not downloaded
        filename = "C500.TCGA-DK-A1AA-10A-01D-A13W-08.3_gdc_realn.bam"
        print "INFO: Creating bam index to {}".format(filename)
        if (os.path.isdir(i)) :
            os.rename(filename, "{}/{}".format(i, filename)) # Move the bam to corresponding folder
            filename = i + "/" + filename

        p = subprocess.Popen("samtools index -@ 8 {}".format(filename), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(p)

    for p in processes :
        print p.returncode;
        p.wait()

def getManifests(subtype) :
    endp='https://api.gdc.cancer.gov/cases/'
    fields = 'fields=submitter_id'

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

if __name__ == "__main__" :
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
    #subtype = 'TCGA-BLCA'
    #subtype = 'TCGA-UCEC'
    #subtype = 'TCGA-KIRC'
    #subtype = 'TCGA-KIRP'
    #subtype = 'TCGA-KICH'
    #subtype = 'TCGA-GBM'
    #subtype = 'TCGA-PRAD'
    #subtype = 'TCGA-PAAD'
    subtype = 'TCGA-THCA'
    getManifests(subtype)

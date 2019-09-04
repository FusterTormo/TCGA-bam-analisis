from os.path import expanduser
home = expanduser("~")

home_jespinosa = '/home/jespinosa'
home_ffuster = '/home/ffuster'

if home == home_jespinosa:
    pathScripts = home_jespinosa + "/git/bam-anal-isis/bash_scripts_conda"
    pathMasterScript = home_jespinosa + "/git/bam-anal-isis/masterScriptLib.py"
elif home == home_ffuster:
    pathScripts = home_ffuster + "/Scripts"
    pathMasterScript = home_ffuster + "/Scripts/masterScriptLib.py"
else:
    pathScripts = home_ffuster + "/Scripts"
    pathMasterScript = home_ffuster + "/Scripts/masterScriptLib.py"

pathToken = "/mnt/data/token.txt"
pathDb = "/g/strcombio/fsupek_cancer2/TCGA_bam/info/info.db" #Absolute path where DB is stored

cancerPath = { "HNSC" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "LIHC" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "LUAD" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
               "LUSC" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
               "OV" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
               "STAD" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
               "BLCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "BRCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "COAD" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "GBM" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               # "KICH" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "KIRC" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               # "KIRP" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "KIRP" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "KICH" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "PAAD" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               # "READ" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "READ" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               # "THCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "THCA" : "/g/strcombio/fsupek_cancer2/TCGA_bam",
               "UCEC" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "CHOL" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "UCS"  : "/g/strcombio/fsupek_cancer3/TCGA_bam",
               "DLBC" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "UVM"  : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "ACC"  : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "THYM" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "PCPG" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
               "SKCM" : "/g/strcombio/fsupek_cancer3/TCGA_bam" }


#"PRAD" : "/g/strcombio/fsupek_cancer3/TCGA_bam",

pathSql = "local_analyses.sql"
finish_file = ".finished"

analyses = { "all" : "All analyses",
             "vcall" : "Only variant calling (Strelka2 germinal, Platypus, Strelka2 somatic)",
             "cnv" : "Only copy number (CNVkit, EXCAVATOR2, Manta germinal, Manta somatic)",
             "msi" : "Only msi (MSIsensor)",
             "loh" : "Only LOH (FACETS, AscatNGS)",
             "cov" : "Only coverage (bedtools genomeCov)",
             "strelka" : "Only run Strelka2 germline",
             "strelkaS" : "Only run Strelka2 somatic",
             "platypus" : "Only run Platypus",
             "cnvkit" : "Only run CNVkit",
             "excavator" : "Only run EXCAVATOR2",
             "manta" : "Only run Manta germline",
             "mantaS" : "Only run Manta somatic",
             "facets" : "Only run FACETS",
             "ascat" : "Only run AscatNGS"}

## Jobs specification for slurm batches
## Germline analyses resources
strelka_germline_r = ["8", "2G", "strelka2G_", "03:00:00"]
platypus_r = ["1", "1G", "platypus_", "50:00"]
bedtools_cov_r =  ["1", "10G", "bedtoolsCov_", "02:30:00"]
# cnvkit_r = ["8", "10G", "cnvkit_" , "30:00"]
cnvkit_r = ["8", "10G", "cnvkit_" , "01:30:00"]
excavator_r = ["20", "1G", "excavator2_", "01:30:00"]
manta_germline_r = ["6", "2G", "mantaG_", "01:30:00"]

## Somatic analyses resources
strelka_somatic_r = ["8", "2G", "strelka2S_", "03:00:00"]
manta_somatic_r = ["6", "2G", "mantaS_", "03:00:00"]
facets_r = ["1", "1G", "facets_", "05:00:00"]
ascat_r = ["2", "22G", "ascat_", "14:00:00"]
msi_r = ["10", "1G", "msisensor_", "01:00:00"]

job_specs = {'all' :  {  "strelka" : strelka_germline_r,
                        "strelkaS" : strelka_somatic_r,
                        "platypus" : platypus_r,
                        "cnvkit" : cnvkit_r,
                        "excavator" : excavator_r,
                        "manta" : manta_germline_r,
                        "mantaS" : manta_somatic_r,
                        "facets" : facets_r,
                        "ascat" : ascat_r,
                        "msi" : msi_r,
                        "cov" : bedtools_cov_r },
            ## dropped from the tools to run 2019/02/01
            'dropped' :{"strelka" : strelka_germline_r,
                        "strelkaS" : strelka_somatic_r,
                        "platypus" : platypus_r,
                        "mantaS" : manta_somatic_r,
                        "facets" : facets_r,
                        "msi" : msi_r,
                        "cov" : bedtools_cov_r },
            ## only strelka run 2019/02/26
            'strelka' :{"strelka" : strelka_germline_r,
                        "strelkaS" : strelka_somatic_r },
             ## complentary strelka run 2019/02/26
            'not_strelka' :{"platypus" : platypus_r,
                        "mantaS" : manta_somatic_r,
                        "facets" : facets_r,
                        "msi" : msi_r,
                        "cov" : bedtools_cov_r },
            ## only cnvkit run 2019/03/06
            'cnvkit': {"cnvkit": cnvkit_r }
            }

germlinePrograms = ["Strelka2 germline", "Platypus germline", "EXCAVATOR2", "CNVkit", "Manta germline", "Bedtools genomeCov"]
somaticPrograms = ["Strelka2 somatic", "AscatNGS", "FACETS", "Manta somatic", "MSIsensor"]

### List of tools updated until dropping the ones that are not use anymore (2019/02/01)
## CNVkit, excavator, ascat, manta germline
germlineProgramsDroppedTools = ["Strelka2 germline", "Platypus germline", "Bedtools genomeCov"]
somaticProgramsDroppedTools = ["Strelka2 somatic", "FACETS", "Manta somatic", "MSIsensor"]

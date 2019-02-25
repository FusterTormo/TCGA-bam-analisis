from os.path import expanduser
home = expanduser("~")

home_jespinosa = '/home/jespinosa'
home_ffuster = '/home/ffuster'

if home == home_jespinosa:
    pathScripts = home_jespinosa + "/git/bam-anal-isis/bash_scripts_conda"
    pathMasterScript = home_jespinosa + "/Scripts/masterScriptLib.py"
elif home == home_ffuster:
    pathScripts = home_ffuster + "/Scripts"
    pathMasterScript = home_ffuster + "/Scripts/masterScriptLib.py"
else:
    pathScripts = home_ffuster + "/Scripts"
    pathMasterScript = home_ffuster + "/Scripts/masterScriptLib.py"

pathToken = "/mnt/data/token.txt"
pathDb = "/g/strcombio/fsupek_cancer2/TCGA_bam/info/info.db" #Absolute path where DB is stored

cancerPath = {"HNSC" : "/g/strcombio/fsupek_cancer1/TCGA_bam",
        "LIHC" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
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
        "THCA" : "/g/strcombio/fsupek_cancer3/TCGA_bam",
        "UCEC" : "/g/strcombio/fsupek_cancer3/TCGA_bam"}

#
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

germlinePrograms = ["Strelka2 germline", "Platypus germline", "EXCAVATOR2", "CNVkit", "Manta germline", "Bedtools genomeCov"]
somaticPrograms = ["Strelka2 somatic", "AscatNGS", "FACETS", "Manta somatic", "MSIsensor"]

### List of tools updated until dropping the ones that are not use anymore (2019/02/01)
## CNVkit, excavator, ascat, manta germline
germlineProgramsDroppedTools = ["Strelka2 germline", "Platypus germline", "Bedtools genomeCov"]
somaticProgramsDroppedTools = ["Strelka2 somatic", "FACETS", "Manta somatic", "MSIsensor"]

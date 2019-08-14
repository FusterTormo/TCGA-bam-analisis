#!/bin/bash

#To download new cancers, change this line to where the manifests are, and that's all
# cd /g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-THCA/
# dir_samples="/g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-SKCM"
# dir_samples="/g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-CHOL"
# dir_samples="/g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-UCS"
# dir_samples="/g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-DLBC"
# dir_samples="/g/strcombio/fsupek_cancer1/TCGA_bam/TCGA-UVM"
# dir_samples="/g/strcombio/fsupek_cancer1/TCGA_bam/TCGA-ACC"
# dir_samples="/g/strcombio/fsupek_cancer1/TCGA_bam/TCGA-THYM"
# dir_samples="/g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-LGG"
dir_samples="/g/strcombio/fsupek_cancer1/TCGA_bam/TCGA-PCPG"

cd $dir_samples
sta=`date`
token="/mnt/data/token.txt"
gdc="/mnt/data/gdc-client download"
minspace=41943040	
for f in *; do
	echo "Getting $f. Started at `date`"
	cd "$dir_samples/$f"
	#Manifest has the same name as the folder, plus ".txt" extension. -n parameter should be between 30-40 to get the maximum download speed
	$gdc -t $token -m $f.txt -d . -n 40
	echo -e "Finished at `date`\n"
	cd $dir_samples
	#Check if the disk is near full
	#space=`df -k /dev/md126 | grep /dev | awk '{print $4}'`
	#if [ $space -le $minspace ]; then 
#		echo -e "Disk capacity reached. Exiting\n"
#		echo -e "Last sample downloaded: $f\n"
#		break	
#	fi
done
echo -e "getBams.sh started on $sta\n\ngetBams.sh ended on `date`"


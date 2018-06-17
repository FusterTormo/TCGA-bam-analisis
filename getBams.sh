#!/bin/bash

#To download new cancers, change this line to where the manifests are, and that's all
cd /g/strcombio/fsupek_cancer3/TCGA_bam/TCGA-KICH/
sta=`date`
token="/mnt/data/token.txt"
gdc="/mnt/data/gdc-client download"
minspace=41943040	
for f in *; do
	echo "Getting $f. Started at `date`"
	cd $f
	#Manifest has the same name as the folder, plus ".txt" extension. -n parameter should be between 30-40 to get the maximum download speed
	$gdc -t $token -m $f.txt -d . -n 40
	echo -e "Finished at `date`\n"
	cd ..
	#Check if the disk is near full
	#space=`df -k /dev/md126 | grep /dev | awk '{print $4}'`
	#if [ $space -le $minspace ]; then 
#		echo -e "Disk capacity reached. Exiting\n"
#		echo -e "Last sample downloaded: $f\n"
#		break	
#	fi
done
echo -e "getBams.sh started on $sta\n\ngetBams.sh ended on `date`"


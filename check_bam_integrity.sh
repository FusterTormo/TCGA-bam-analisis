#############################################################################
### Jose Espinosa-Carrasco AGENDAS-IRB Group. Sep 2019                    ###
#############################################################################
### Do to a problem in Sinology cancer 3 disk we have to check the        ###
### integrity of files on the disk. Since SKCM bam files where downloaded ###
### just before the crash, we will use this files to check the integrity  ###
### of data in the disk.                                                  ###
#############################################################################

#!/usr/bin/env bash

dir_samples="/g/strcombio/fsupek_cancer3/TCGA_bam/SKCM"

cd $dir_samples
sta=`date`
minspace=41943040

for f in *; do
	echo "md5sum checking on $f. Started at `date`"
	cd "$dir_samples/$f"
    touch $dir_samples/md5_result.txt
	# Manifest has the same name as the folder, plus ".txt" extension. -n parameter should be between 30-40 to get the maximum download speed
	# The manifest contains the md5sum hash key
	{
    read
    while IFS=$'\t' read -r -a bam_info_ary; do
        cd "${bam_info_ary[0]}"
        echo "md5sum checking on file ${bam_info_ary[1]}"
        echo -e "${bam_info_ary[2]}""\t""${bam_info_ary[1]}" > "${bam_info_ary[1]}".md5
        md5sum --check "${bam_info_ary[1]}".md5 >> $dir_samples/md5_result.txt

        cd "$dir_samples/$f"
     done
     } < ${f}.txt

	echo -e "Finished at `date`\n"
	cd $dir_samples

done
echo -e "check_bam_integrity.sh started on $sta\n\ncheck_bam_integrity.sh ended on `date`"

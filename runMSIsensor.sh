#!/bin/bash

#Constants
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

MSIref=~/genome_references/msisensor.list
MSISENSOR=~/soft/msisensor/msisensor
ALIAS=MSIsensor

if (( $# == 3 ))
then
	tumor=$(basename $1)
	dirTumor=$(dirname $1)
	tumorIndex=${tumor%.*}.bai
	normal=$(basename $2)
	dirNormal=$(dirname $2)
	normalIndex=${normal%.*}.bai
	outputFolder=$3

	sta=`date`
	SECONDS=0
	
	if [ ! -f $MSIref ]
	then
		echo -e "\n${RED}Reference file not found.${NC} Creating MSIsensor homopolymer and microsatellites list.\n"
		$MSISENSOR scan -d ~/genome_references/customRef38.fa -o $MSIref
	fi
	echo "Redoing the tumor and normal BAM indexes"
	#Change the name of the old files, not necessary to make it, and if the program runs in parallel, there can be some conflicts
	#mv $dirTumor/$tumorIndex $dirTumor/${tumorIndex}_old
	#mv $dirNormal/$normalIndex $dirNormal/${normalIndex}_old
	#Run both samtools index in parallel and wait until they have finished
	~/soft/samtools-1.6/samtools index $dirTumor/$tumor &
	~/soft/samtools-1.6/samtools index $dirNormal/$normal &
	wait
	
	mkdir $outputFolder
	cd $outputFolder
	$MSISENSOR msi -d $MSIref -n $dirNormal/$normal -t $dirTumor/$tumor -o $ALIAS -l 1 -q 1 -b 4
	if (( $? == 0))
	then
		echo -e "${GREEN}MSIsensor analysis ran successfully.${NC}\n"
		rm $dirTumor/${tumor}.bai
		rm $dirNormal/${normal}.bai
		#Adding a header to the MSIsensor output files _germline and _somatic
		echo -e "Chr\tLocation\tLeft_flank\tRepeat_times\tRepeated_bases\tRight_flank\tGenotype\n$(cat MSIsensor_germline)" > MSIsensor_germline
		echo -e "Chr\tLocation\tLeft_flank\tRepeat_times\tRepeated_bases\tRight_flank\tDifference\tpvalue\tFDR\tRank\n$(cat MSIsensor_somatic)" > MSIsensor_somatic
		#Return the name of the old bai files
		#mv $dirNormal/${normalIndex}_old $dirNormal/$normalIndex
		#mv $dirTumor/${tumorIndex}_old $dirTumor/$tumorIndex
	else
		echo >&2 -e "${RED} Error found while running MSIsensor. Check output${NC}\n"
		exit 1
	fi
	
	end=`date`
	echo -e "MSIsensor started at $sta\nEnded at $end"
	printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
else
	echo >&2 -e "\n\nUSAGE: runMSIsensor.sh tumor.bam normal.bam output_folder\n"
	exit 1
fi

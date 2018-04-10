#!/bin/bash

#Get the absolute path of the bam files
function createSourceTarget() {
	controlRef="/g/strcombio/fsupek_cancer2/sc_repo/poolDataAnalysis.txt"
	abPath=`realpath $1`
	dir=`dirname $abPath`
	#filename=`basename $abPath`
	filename=$2
	outputDir=$dir/EXCAVATOR2
	#Create subfolderStructure
	mkdir $outputDir
	echo "$abPath $outputDir $filename" > $dir/dataPrepare.txt
	echo "T1 $outputDir $filename" > $dir/dataAnalyse.txt
	cat $controlRef >> $dir/dataAnalyse.txt
	echo -e "${GREEN}Configuration files created successfully in $abPath${NC}"
}




GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if (( $# == 2 ))
then
	if [ ! -f $1 ]
	then
		echo "${RED}Bam file not found${NC}\n"
	else
		sta=`date`
		SECONDS=0
		pathEX=~/soft/EXCAVATOR2_Package_v1.1.2
		
		#Create needed configuration files
		dir=`realpath $1`
		current_dir=`dirname $dir`
		createSourceTarget $1 $2
		cd $pathEX

		#Run dataPrepare script
		perl EXCAVATORDataPrepare.pl $current_dir/dataPrepare.txt --processors 20 --target targets50K --assembly hg38
		if (( $? == 0 )); then
			#Run dataAnalysis
			perl EXCAVATORDataAnalysis.pl $current_dir/dataAnalyse.txt --processors 20 --target targets50K --assembly hg38 --output ./EXCAVATOR2 --mode pooling
			mv $current_dir/dataAnalyse.txt $current_dir/EXCAVATOR2
			mv $current_dir/dataPrepare.txt $current_dir/EXCAVATOR2
			if (( $? == 0))
			then
				echo -e "${GREEN}EXCAVATOR2 analysis ran successfully.${NC}\n"
			else
				echo -e "${RED} Error found. Check output${NC}\n"
			fi
			
		else
			echo -e >&2 "${RED} Error found. Check output${NC}\n"
			exit 1
		fi
		
		end=`date`
		echo -e "EXCAVATOR2 started at $sta\nEnded at $end"
		printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
	fi
else
	echo >&2 -e "\n\nUSAGE: runEXCAVATOR2.sh input_bam alias_for_input_bam\n"
	exit 1
fi

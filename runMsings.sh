#!/bin/bash

#Constants
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VARSCAN=~/soft/msings/msings-env/bin/VarScan.v2.3.7.jar
INTERVALS_FILE=~/genome_references/customRefSeqExons.msi_intervals
INTERVALS_FILE2=~/genome_references/customMSINGS.msi_intervals
BEDFILE=~/genome_references/customMSINGS.sorted.bed
REF_GENOME=~/genome_references/customRef38.fa
MSI_BASELINE=~/soft/msings/doc/mSINGS_TCGA.baseline

BAM=$1

#"multiplier" is the number of standard deviations from the baseline that is required to call instability
multiplier=2.0 
#"msi_min_threshold" is the maximum fraction of unstable sites allowed to call a specimen MSI negative     
msi_min_threshold=0.2
#"msi_max_threshold" is the minimum fraction of unstable sites allowed to call a specimen MSI positive
msi_max_threshold=0.2

sta=`date`
SECONDS=0

#TODO uncomment to test whether bam is sorted
#echo "Testing if bam file is sorted"
#Get if bam is sorted previously
#isSorted=`samtools stats $BAM | grep 'is sorted' | cut -f 3`

#if [ $isSorted != 1 ]
#then
#	echo -e >&2 "${RED}ERROR: BAM is not sorted. Exiting${NC}\n"
#	exit 1
#fi

SAVEPATH=$(dirname $BAM)
BAMNAME=$(basename $BAM)
PFX=${BAMNAME%.*}

echo "Creating output dir"
mkdir -p $SAVEPATH/mSINGS
echo "Dir $SAVEPATH/mSINGS created"

printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
echo `date`
source ~/soft/msings/msings-env/bin/activate
echo "Running pileup"
samtools mpileup -f $REF_GENOME -d 100000 -A -E $BAM -l $INTERVALS_FILE | awk '{if($4 >= 6) print $0}' > $SAVEPATH/mSINGS/$PFX.mpileup
if (( $? != 0)); then
	echo "\n${RED}Errors found during samtools analysis. Check output"
	exit 1
fi
echo "Pileup stored in $SAVEPATH/mSINGS/$PFX.mpileup"
printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
echo `date`

echo "Removing chr prefix from the files"
sed 's/chr//g' $SAVEPATH/mSINGS/$PFX.mpileup > $SAVEPATH/mSINGS/pileupNoChr.mpileup
printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
echo `date`

echo "Running VarScan Readcounts"
ssh agendas java -Xmx128g -jar $VARSCAN readcounts $SAVEPATH/mSINGS/pileupNoChr.mpileup --variants-file $INTERVALS_FILE2 --min-base-qual 10 --output-file $SAVEPATH/mSINGS/$PFX.msi_output

if (( $? != 0)); then
	echo "\n${RED}Errors found during VarScan analysis. Check output"
	exit 1
fi

echo "VarScan output stored in $SAVEPATH/mSINGS/$PFX.msi_output"
printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
echo `date`

echo "MSI Analysis"
msi analyzer $SAVEPATH/mSINGS/$PFX.msi_output $BEDFILE -o $SAVEPATH/mSINGS/$PFX.msi.txt
#echo "Ended analyzer"
#Not working nowadays (14-02-18) due to baseline file has to be reprogrammed
#msi count_msi_samples $MSI_BASELINE $SAVEPATH/mSINGS -m $multiplier -t $msi_min_threshold $msi_max_threshold -o $SAVEPATH/mSINGS/$PFX.MSI_Analysis.txt
#echo "Ended count_msi_samples"

if (( $? == 0 )); then
	echo -e "${GREEN}mSINGS ran successfully.${NC}"
	end=`date`
	echo -e "mSINGS started at $sta\nEnded at $end"
	printf 'Elapsed time -> %dh:%dm:%ds\n' $(($SECONDS/3600)) $(($SECONDS%3600/60)) $(($SECONDS%60))
else
	echo -e >&2 "\n${RED}Execution aborted. Check below possible errors${NC}\n"
	exit 1
fi

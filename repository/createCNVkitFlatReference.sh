#!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m'

#Path for files needed to create the flat reference
refSeq=~/genome_references/customRef38.fa
targetBed=~/genome_references/customRefSeqExons.bed
annotation=~/genome_references/refFlat.txt

#Check if the folder that contains the references exists
cd ~/genome_references
if [ ! -d cnvkit ]
then
	mkdir cnvkit
fi

#Create the flat reference. It will be store as 
echo -e "\nCompiling access regions\n==================================\n\n"
cnvkit.py access $refSeq -o ~/genome_references/cnvkit/sequenced.bed
echo -e "\nCompiling target regions\n==================================\n\n"
cnvkit.py target $targetBed --annotate $annotation --split -o ~/genome_references/cnvkit/target.bed
echo -e "\nCompiling anti-target regions\n==================================\n\n"
cnvkit.py antitarget ~/genome_references/cnvkit/target.bed -g ~/genome_references/cnvkit/sequenced.bed -o ~/genome_references/cnvkit/antitarget.bed
echo -e "\nCreating flat reference\n==================================\n\n"
cnvkit.py reference -o ~/genome_references/cnvkit/germlineFlat.reference.cnn -f $refSeq -t ~/genome_references/cnvkit/target.bed -a ~/genome_references/cnvkit/antitarget.bed

if (( $? == 0 )); then
	echo -e "${GREEN}CNVkit references compiled successfully.${NC}"
fi

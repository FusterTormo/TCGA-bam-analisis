#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

cd /g/strcombio/fsupek_cancer3/TCGA_bam/BRCA
rsync -aP 04e6b781-48c0-473d-83e2-b3770e52bd38/TCGA-B6-A0RE-10A-01W-A071-09_HOLD_QC_PENDING_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 07a41712-a48a-4d45-ae2a-0ad492e6784f/TCGA-E2-A15O-10A-01D-A110-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 1571b866-6da0-48a3-875c-21cbaef4e7cb/TCGA-A2-A0SV-10A-01W-A097-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 219a2da4-a916-49ae-a412-9c1ea84703d4/TCGA-AR-A0U2-10A-01D-A10G-09_IlluminaGA-DNASeq_exome_HOLD_QC_PENDING_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 2257901b-fc4f-4a52-bcbe-c756e74be153/TCGA-A1-A0SH-10A-03D-A099-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 39761577-e317-482b-b20b-2ea6947f43fe/TCGA-A8-A07P-10A-01W-A021-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP b62da5ff-09aa-4333-aee9-f779ed7944df/TCGA-A8-A09D-10A-01W-A021-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP bbaa4a13-b892-4b42-8689-1faccda0fc65/TCGA-AR-A0TY-10A-01D-A110-09_IlluminaGA-DNASeq_exome_1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP c1ad5a00-3d81-4b22-8fe6-c6b1964bed24/TCGA-A8-A091-10A-01W-A021-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP fba14cd3-613d-47d7-8ffd-2f17ae043b88/TCGA-AN-A0AS-10A-01W-A021-09_IlluminaGA-DNASeq_exome_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
cd ../COAD
rsync -aP 10ebf44f-3f93-420d-909c-8ffffedca021/TCGA-D5-6533-10A-01D-1719-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 2810d595-ec40-478e-b3ed-c948f2d878d4/TCGA-D5-6898-10A-01D-1924-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 3f2f400f-598d-426b-a133-9d61b178c6d7/TCGA-AZ-4308-10A-01D-2188-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 42eeb75b-0bbc-4b9a-8093-f6d0ff19665a/TCGA-G4-6321-10A-01D-1720-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 47aba8b6-122f-4e61-82b9-5c27ad89be49/TCGA-AZ-4684-10A-01D-2188-10_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 592244d8-ab93-4df0-ad95-bc04332371b9/TCGA-D5-6922-10A-01D-1924-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 9aa3287c-4109-43f9-85a1-13905a0a219b/TCGA-D5-6929-10A-01D-1924-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP 9ca38767-1a54-485d-9d93-01a3e712a670/TCGA-CK-5912-10A-01D-1650-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP c8573454-ebd2-48f1-9ba8-f0b575664d3d/TCGA-DM-A285-10A-01D-A16V-10_hg19_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP c892c83c-adfa-44c3-a0db-570379ca1be7/TCGA-CM-6167-10A-01D-1650-10_Illumina_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
cd ../../../fsupek_cancer2/TCGA_bam/STAD
rsync -aP TCGA-BR-7722/f1a932d7-301d-4553-b0e9-b489c884bd42/C440.TCGA-BR-7722-10A-01D-2201-08.6_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-CD-8524/8f932982-28bc-408a-b8e3-966566bacb78/C440.TCGA-CD-8524-10A-01D-2341-08.8_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-D7-A4YV/a88df0df-1859-4ff9-8b6d-f8495e25d5b5/C440.TCGA-D7-A4YV-10A-01D-A25E-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-HU-A4GN/41189538-01dc-4473-b06b-2734825624ab/C440.TCGA-HU-A4GN-10A-01D-A25E-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-VQ-A91Z/fe8c8d00-619e-493a-9ed2-8054d01cbf92/C440.TCGA-VQ-A91Z-10A-01D-A413-08.2_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
cd ../LUAD/
rsync -aP TCGA-05-5429/817cb132-2618-46d4-862b-7e008c5e0465/C509.TCGA-05-5429-10A-01D-1625-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-35-4123/d15c6630-f884-431d-8d20-20bd48443cdc/C347.TCGA-35-4123-10A-01D-1105-08.5_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-44-2661/aae69031-a9a1-46b1-9259-d89a7b36d046/C347.TCGA-44-2661-10A-01D-1105-08.5_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-55-6970/91e70307-0191-4504-8598-58c3ee59df55/C509.TCGA-55-6970-11A-01D-1945-08.3_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-4B-A93V/dece21d1-4769-4282-bec7-9cf0d1f56632/C509.TCGA-4B-A93V-10A-01D-A39A-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
cd ../LUSC/
rsync -aP TCGA-21-5786/c5884ae2-a06f-42c6-95f2-c6260da48431/C508.TCGA-21-5786-10A-01D-1632-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-33-4533/f6ff6a59-b982-4b45-adbd-6b531f2d687d/C347.TCGA-33-4533-11A-01D-1267-08.4_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-37-3783/379dcf39-6834-47e8-a584-d0af8eb834d5/C347.TCGA-37-3783-10A-01D-1267-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-43-3394/9769ac68-caa9-44ca-9b6e-73615cac009c/C508.TCGA-43-3394-11A-01D-1553-08.7_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-56-8309/c80d38ea-9647-485e-aa8f-52821c1a292c/C508.TCGA-56-8309-10A-01D-2293-08.2_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
cd ../../../fsupek_cancer1/TCGA_bam/HNSC/
rsync -aP TCGA-CN-4723/5ff82123-d3e3-45ec-92d1-adb182f87093/C495.TCGA-CN-4723-10A-01D-1434-08.3_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-BA-4074/9d6ea1fa-8aec-4ed1-88ac-901b10853262/C495.TCGA-BA-4074-10A-01D-1434-08.3_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-CQ-5329/209b61ea-97cf-472a-bc4d-acf07f5c1859/C495.TCGA-CQ-5329-10A-01D-1683-08.2_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-CR-6467/e99f9c5c-6987-4119-9c8b-745404048429/C495.TCGA-CR-6467-10A-01D-1870-08.4_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/
rsync -aP TCGA-CV-7407/20ce907e-3368-44dc-b66c-3930e3a26d0d/C495.TCGA-CV-7407-10A-01D-2078-08.1_gdc_realn.ba* /mnt/data/cnvkit_pool_reference/

echo -e "\n${GREEN}Bams copied successfully${NC}\n"
sta=`date`
cd /mnt/data/cnvkit_pool_reference/
mkdir reference
cnvkit.py batch	/g/strcombio/fsupek_cancer2/TCGA_bam/OV/TCGA-04-1343/65188600-0933-4b7b-9cdd-eac182199770/C239.TCGA-04-1343-10A-01W.2_gdc_realn.bam --normal *.bam --targets ~/genome_references/customRefSeqExons.bed --fasta ~/genome_references/customRef38.fa --output-reference germline.reference.cnn --output-dir ./reference
if (( $? == 0 )); then
	echo -e "${GREEN}CNVkit reference compiled successfully.\n"
else 
	echo -e "\n${RED}Execution aborted. Check below possible errors${NC}\n"
fi
end=`date`
echo -e "CNVkit started at $sta\nEnded at $end"

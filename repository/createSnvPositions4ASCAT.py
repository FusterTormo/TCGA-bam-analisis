import gzip
import sys

vcf = "/home/ffuster/genome_references/1000GENOMES-phase_3.vcf.gz"
maf = 0.01
gap = 100
chroms = ["1", "2", "3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y"]
lastChrom = ""
lastPos = -100

with gzip.open(vcf, "r") as fi :
  for lin in fi :
      cols = lin.split("\t")
      if len(cols) > 1 and cols[0] in chroms :
          #Get MAF
          info = cols[7].split(";")
          for i in info :
              aux = i.split("=")
              if aux[0] == "MAF" :
                  rs = cols[2]
                  chr = cols[0]
                  pos = int(cols[1])
                  if lastChrom != chr :
                      lastPos = -100

                  if float(aux[1]) >= maf and pos-gap > lastPos :
                      print "{}\t{}\t{}".format(rs, chr, pos)
                      lastPos = pos
                      lastChrom = chr

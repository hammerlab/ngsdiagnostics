from nose.tools import *
from scripts import gatk_log_parser

def test_line_parsing():
  sample_log_line = """\
INFO  14:34:51,180 FunctionEdge - Starting:  'bash'  '-c'  "  'set'  '-o' 'pipefail'  &&  'bwa'  'mem'  '-M'  '-R' '@RG\tID:D1375ACXX.1.GGCTAC\tSM:NA12878\tLB:L01WE\tPL:illumina\tPU:amee'  '-v' '1'  '-t' '16'  '/projects/ngs/resources/gatk/2.3/ucsc.hg19.female.fasta'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R1_001.D1375ACXX.fastq.gz'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R2_001.D1375ACXX.fastq.gz'  |  'java'  '-Xmx10240m'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'net.sf.picard.sam.SortSam'  'INPUT=/dev/stdin'  'TMP_DIR=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  'OUTPUT=./NA12878_GGCTAC_L001_R1_001.D1375ACXX.bam'  'VALIDATION_STRINGENCY=SILENT'  'SO=coordinate'  'MAX_RECORDS_IN_RAM=4000000'  'CREATE_INDEX=true'  "  \
"""
  hours = 14
  mins = 34
  secs = 51
  msecs = 180
  edgeType = 'Starting'
  body = """\
'bash'  '-c'  "  'set'  '-o' 'pipefail'  &&  'bwa'  'mem'  '-M'  '-R' '@RGID:D1375ACXX.1.GGCTACSM:NA12878LB:L01WEPL:illuminaPU:amee'  '-v' '1'  '-t' '16'  '/projects/ngs/resources/gatk/2.3/ucsc.hg19.female.fasta'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R1_001.D1375ACXX.fastq.gz'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R2_001.D1375ACXX.fastq.gz'  |  'java'  '-Xmx10240m'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'net.sf.picard.sam.SortSam'  'INPUT=/dev/stdin'  'TMP_DIR=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  'OUTPUT=./NA12878_GGCTAC_L001_R1_001.D1375ACXX.bam'  'VALIDATION_STRINGENCY=SILENT'  'SO=coordinate'  'MAX_RECORDS_IN_RAM=4000000'  'CREATE_INDEX=true'  "\
"""

  expected_groups = (str(hours), str(mins), str(secs), str(msecs), edgeType, body)
  expected_step = 'SortSam'

  groups = gatk_log_parser.patt.match(sample_log_line).groups()
  assert groups[:-1] == expected_groups[:-1]
  assert gatk_log_parser.find_steps(groups[-1]) == expected_step

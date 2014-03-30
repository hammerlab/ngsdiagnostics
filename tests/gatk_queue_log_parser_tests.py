from nose.tools import *
from scripts.gatk_queue_log_parser import *
from datetime import datetime as dt, timedelta as td

SAMPLE_LOG_LINE = """\
INFO  14:34:51,180 FunctionEdge - Starting:  'bash'  '-c'  "  'set'  '-o' 'pipefail'  &&  'bwa'  'mem'  '-M'  '-R' '@RG\tID:D1375ACXX.1.GGCTAC\tSM:NA12878\tLB:L01WE\tPL:illumina\tPU:amee'  '-v' '1'  '-t' '16'  '/projects/ngs/resources/gatk/2.3/ucsc.hg19.female.fasta'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R1_001.D1375ACXX.fastq.gz'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R2_001.D1375ACXX.fastq.gz'  |  'java'  '-Xmx10240m'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'net.sf.picard.sam.SortSam'  'INPUT=/dev/stdin'  'TMP_DIR=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  'OUTPUT=./NA12878_GGCTAC_L001_R1_001.D1375ACXX.bam'  'VALIDATION_STRINGENCY=SILENT'  'SO=coordinate'  'MAX_RECORDS_IN_RAM=4000000'  'CREATE_INDEX=true'  " """
BODY = """\
'bash'  '-c'  "  'set'  '-o' 'pipefail'  &&  'bwa'  'mem'  '-M'  '-R' '@RGID:D1375ACXX.1.GGCTACSM:NA12878LB:L01WEPL:illuminaPU:amee'  '-v' '1'  '-t' '16'  '/projects/ngs/resources/gatk/2.3/ucsc.hg19.female.fasta'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R1_001.D1375ACXX.fastq.gz'  '/projects/ngs/validation/exome/NA12878/data/r1-1-1/NA12878_GGCTAC_L001_R2_001.D1375ACXX.fastq.gz'  |  'java'  '-Xmx10240m'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'net.sf.picard.sam.SortSam'  'INPUT=/dev/stdin'  'TMP_DIR=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  'OUTPUT=./NA12878_GGCTAC_L001_R1_001.D1375ACXX.bam'  'VALIDATION_STRINGENCY=SILENT'  'SO=coordinate'  'MAX_RECORDS_IN_RAM=4000000'  'CREATE_INDEX=true'  " """

def function_edge_re_test():
    h = 14
    m = 34
    s = 51
    ms = 180
    edge_type = 'Starting'
    expected_groups = (str(h), str(m), str(s), str(ms), edge_type, BODY)

    groups = FUNCTION_EDGE_RE.match(SAMPLE_LOG_LINE).groups()
    assert groups[:-1] == expected_groups[:-1]


SAMPLE_RUN_TIMES = {
    'steps': {
        'test_step_name': [
            {'run_time': 10},
            {'run_time': 20},
        ]
    }
}
def get_avg_step_times_test():
    assert get_avg_step_times(SAMPLE_RUN_TIMES) == {'test_step_name': 15}


def make_dict_of_lists_test():
    sample_list_of_pairs = [('key', 1), ('key', 2)]
    assert make_dict_of_lists(sample_list_of_pairs) == {'key': [1, 2]}


SAMPLE_BQSR_LOG_LINE = """\
INFO  08:51:53,013 FunctionEdge - Starting:  'java'  '-Xmx4096m'  '-XX:+UseParallelOldGC'  '-XX:ParallelGCThreads=4'  '-XX:GCTimeLimit=50'  '-XX:GCHeapFreeLimit=10'  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL'  '-XX:+PerfDisableSharedMem'  '-cp' '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'  'org.broadinstitute.sting.gatk.CommandLineGATK'  '-T' 'BaseRecalibrator'  '-I' '/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/r1-1-1.NA12878.clean.dedup.bam'  '-et' 'NO_ET'  '-K' '/packages/gatk/1.5-21-g979a84a/src/eugene.fluder_mssm.edu.key'  '-L' '/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queueScatterGather/.qlog/r1-1-1.NA12878.pre_recal.gatkreport.covariates-sg/temp_01_of_20/scatter.intervals'  '-R' '/projects/ngs/resources/gatk/2.3/ucsc.hg19.fasta'  '-knownSites' '/projects/ngs/resources/gatk/2.3/dbsnp_137.hg19.vcf' '-knownSites' '/projects/ngs/resources/gatk/2.3/Mills_and_1000G_gold_standard.indels.hg19.vcf'  '-o' '/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queueScatterGather/.qlog/r1-1-1.NA12878.pre_recal.gatkreport.covariates-sg/temp_01_of_20/r1-1-1.NA12878.pre_recal.gatkreport'  '-cov' 'ReadGroupCovariate' '-cov' 'QualityScoreCovariate' '-cov' 'CycleCovariate' '-cov' 'ContextCovariate' """
SAMPLE_JAVA_ARGS = [
  '-Xmx4096m',
  '-XX:+UseParallelOldGC',
  '-XX:ParallelGCThreads=4',
  '-XX:GCTimeLimit=50',
  '-XX:GCHeapFreeLimit=10',
  '-Djava.io.tmpdir=/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queue.bcxofqXZsL',
  '-XX:+PerfDisableSharedMem',
  '-cp',
  '/hpc/users/lindem03/packages/gatk-mssm/2.7.0/dist/Queue.jar'
]
SAMPLE_GATK_ARGS_DICT = {
  'I': ['/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/r1-1-1.NA12878.clean.dedup.bam'],
  'K': ['/packages/gatk/1.5-21-g979a84a/src/eugene.fluder_mssm.edu.key'],
  'L': ['/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queueScatterGather/.qlog/r1-1-1.NA12878.pre_recal.gatkreport.covariates-sg/temp_01_of_20/scatter.intervals'],
  'R': ['/projects/ngs/resources/gatk/2.3/ucsc.hg19.fasta'],
  'T': ['BaseRecalibrator'],
  'cov': ['ReadGroupCovariate', 'QualityScoreCovariate', 'CycleCovariate', 'ContextCovariate'],
  'et': ['NO_ET'],
  'knownSites': ['/projects/ngs/resources/gatk/2.3/dbsnp_137.hg19.vcf',
                 '/projects/ngs/resources/gatk/2.3/Mills_and_1000G_gold_standard.indels.hg19.vcf'],
  'o': ['/gs01/projects/ngs/validation/exome/NA12878/2.7/r1-1-1/.queueScatterGather/.qlog/r1-1-1.NA12878.pre_recal.gatkreport.covariates-sg/temp_01_of_20/r1-1-1.NA12878.pre_recal.gatkreport']
}

def parse_gatk_command_line_test():
    parsed_gatk_command_line = {
        'java_args': SAMPLE_JAVA_ARGS,
        'gatk_args': SAMPLE_GATK_ARGS_DICT
    }
    assert parse_gatk_command_line(SAMPLE_BQSR_LOG_LINE) == parsed_gatk_command_line


NOW = dt.now()
SAMPLE_RUN_INFO = {
    'steps': {
        'test_step_name': [
            ('8f38c37c39087784951c5d5a858dc17f',
             'Starting',
             NOW,
             'kthxbye'),
            ('8f38c37c39087784951c5d5a858dc17f',
             'Done',
             NOW + td(seconds = 10),
             'kthxbye'),
            ('c268120ce3918b1264fe2c05143b5c4b',
             'Starting',
             NOW,
             'wut'),
            ('c268120ce3918b1264fe2c05143b5c4b',
             'Done',
             NOW + td(seconds = 20),
             'wut')
        ]
    }
}
SAMPLE_PAIRED_STEPS = {
    'steps': {
        'test_step_name': [
            {
                'body_hash': '8f38c37c39087784951c5d5a858dc17f',
                'start_time': NOW,
                'end_time': NOW + td(seconds = 10),
                'run_time': 10,
                'body': 'kthxbye'
            },
            {
                'body_hash': 'c268120ce3918b1264fe2c05143b5c4b',
                'start_time': NOW,
                'end_time': NOW + td(seconds = 20),
                'run_time': 20,
                'body': 'wut'
            }
        ]
    }
}
def pair_steps_test():
    run_info = SAMPLE_RUN_INFO
    pair_steps(run_info)
    assert run_info == SAMPLE_PAIRED_STEPS

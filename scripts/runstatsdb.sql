drop table run_timing_metadata;
drop table perf_steps;
drop table perf_measurements;
drop table log_file_paths;

CREATE TABLE run_timing_metadata (run_args text, run_timestamp integer, sample text, primary key(run_args, run_timestamp, sample));
CREATE TABLE perf_steps (id integer primary key autoincrement, name text);
create table perf_measurements(stepid integer, run_id integer, step_time integer, foreign key(stepid) references perf_steps(id), foreign key(run_id) references run_timing_metadata(rowid));
create table log_file_paths (pathname text, run_timestamp);

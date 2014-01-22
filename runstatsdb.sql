drop table run_timing_metadata;
drop table perf_steps;
drop table perf_measurements;
CREATE TABLE run_timing_metadata (run_args text, run_timestamp integer, primary key(run_args, run_timestamp));
CREATE TABLE perf_steps (id integer primary key autoincrement, name text);
create table perf_measurements(stepid integer, run_id integer, step_time integer, foreign key(stepid) references perf_steps(id), foreign key(run_id) references run_timing_metadata(rowid));

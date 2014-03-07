function initialize(logfile_names) {
    $("#searchbox").autocomplete({
	source: logfile_names
    });
}

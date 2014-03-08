function initialize(logfile_names) {
    $("#searchbox").autocomplete({
        source: logfile_names,
        focus: function( event, ui ) {
            $( "#searchbox" ).val( ui.item.label );
            return false;
        },
        select: function( event, ui ) {
            $( "#searchbox" ).val( ui.item.label );
            $( "#searchbox-id" ).val( ui.item.value );
            $( "#searchbox-description" ).html( ui.item.desc );
            return false;
        }
    });
}

$("#searchbox").focus();

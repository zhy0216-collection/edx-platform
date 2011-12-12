$(function() {
    $('#check_${ id }').click(function() {
      var submit_data={};
      $.each($("[id^=input_${ id }_]"), function(index,value){
        submit_data[value.id]=value.value;
      });

      if($('#check_${ id }').attr('value') == 'Check') { 
        $.getJSON('/modx/problem/${ id }/problem_check',
           submit_data,
           function(json) {
             for(p in json) {
               if(json[p]=='correct')
                  $("#status_"+p).attr("class", "ui-icon ui-icon-check");
               if(json[p]=='incorrect')
                  $("#status_"+p).attr("class", "ui-icon ui-icon-close");
                  $('#check_${ id }').attr("value", "Reset");
             }
        });
      } else /* if 'Reset' */ {
        // Possible cleanup: Move from getJSON to just load
        $.getJSON('/modx/problem/${ id }/problem_reset', {'id':'${ id }'}, function(json) {
           $('#main_${ id }').html(json);
        });
      }
    });
});

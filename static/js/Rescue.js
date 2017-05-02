$(function(){
  $("#job_rescue").click(function(){
      $.ajax({
          type:"POST",
          url:"api/plugin/rescue",
          data:'{"command":"command1"}',
          contentType: "application/json",
          dataType: 'json'});
  });
});

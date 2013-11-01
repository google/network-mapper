define(['domReady', 'jquery'], function (domReady, $) {

    domReady(function () {
        var box = $(".id_spreadsheet_id_0 .controls");
        var spreadsheet_link = $(".id_spreadsheet_link");
        html = box.html();
        box.html('<div class="alert alert-info">Loading ...</div>' + html);
        $('.id_spreadsheet_id_0 ul').load('/graph/api/spreadsheets/', function(response, status, xhr){
            if (status == "error") {
                box.html('<div class="alert alert-error">Something went wrong. Paste a spreadsheet URL into the field below.</div>');
            } else {
                box.find(".alert").hide();
            }
        });

        $(".id_spreadsheet_link input").change(function(){
            if ($(this).val() === '') {
                $(".id_spreadsheet_id_0 input").prop('disabled', false);
            }
            else {
                $(".id_spreadsheet_id_0 input").prop('disabled', true);
            }
        });
    });
});

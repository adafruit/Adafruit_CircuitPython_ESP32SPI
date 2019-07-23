console.log("initializing color picker")
var colorPicker = $('input#colorPicker');
colorPicker.minicolors({
    format: "rgb",
    changeDelay: 200,
    change: function (value, opacity) {
        rgbObject = colorPicker.minicolors("rgbObject");
        console.log(rgbObject);
        $.ajax({
            type: "POST",
            url: "/ajax/ledcolor",
            data: JSON.stringify(rgbObject),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data){
                console.log("success!");
            },
            failure: function(errMsg) {
                console.log("error! " + errMsg);
            }
        });
    }
});
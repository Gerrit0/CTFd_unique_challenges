$('#unique_challenges_config_form').submit(function(event) {
    event.preventDefault()
    const form = event.target
    const data = new FormData(form)
    $.post({
        url: CTFd.config.urlRoot + "/api/unique/config",
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        success: function(result) {
            $('#config_form_submit').text('Saved!').addClass('btn-success')
            setTimeout(function() {
                $('#config_form_submit').text('Save').removeClass('btn-success')
            }, 1000)
        }
    })
})

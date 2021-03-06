CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = CTFd.lib.markdown();


CTFd._internal.challenge.preRender = function () { }

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown)
}


CTFd._internal.challenge.postRender = function () {
    if (CTFd._internal.challenge.data.state === 'missing-requirements') {
        CTFd.lib.$('#submission-input').attr('disabled', true)
        CTFd.lib.$('#submit-key').attr('disabled', true)
    }

    const challenge = $('#challenge-id').val();
    $.ajax({
        url: CTFd.config.urlRoot + "/api/unique/files/" + challenge,
        success: function(response) {
            for (const { name, id } of response.data) {
                const template = $($('#file-download-template')[0].content).clone();
                template.find('a').attr('href', "/api/unique/files/" + challenge + "/" + id);
                template.find('small').text(name);
                $('.challenge-files').append(template);
            }
        }
    });
    $.ajax({
        url: CTFd.config.urlRoot + "/api/unique/generated-files/" + challenge,
        success: function(response) {
            for (const { name, id } of response.data) {
                const template = $($('#file-download-template')[0].content).clone();
                template.find('a').attr('href', "/api/unique/generated-files/" + challenge + "/" + id + "/download?cache=" + Math.random());
                template.find('small').text(name);
                $('.challenge-files').append(template);
            }
        }
    });
}


CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var submission = CTFd.lib.$('#submission-input').val()

    var body = {
        'challenge_id': challenge_id,
        'submission': submission,
    }
    var params = {}
    if (preview) {
        params['preview'] = true
    }

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response
        }
        return response
    })
};

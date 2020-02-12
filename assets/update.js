

$('#challenge-properties').append('<a class="nav-item nav-link" data-toggle="tab" href="#unique_files" role="tab">Unique Files</a>');
$('#nav-tabContent').append(`
<div class="tab-pane fade" id="unique_files" role="tabpanel">
    <div class="row">
        <div class="col-md-12">
            <h3 class="text-center py-3 d-block">Unique Files</h3>
            <table id="unique_filesboard" class="table table-striped">
                <thead>
                    <tr>
                        <td class="text-center"><b>File</b></td>
                        <td class="text-center"><b>Settings</b></td>
                    </tr>
                </thead>
                <tbody>
                    <!-- TODO: Include file infos -->
                </tbody>
            </table>
            <div class="col-md-12 mt-3">
                <form id="unique-file-add-form" method="POST">
                    <div class="form-group">
                        <input class="form-control-file" type="file" name="file" multiple="multiple">
                        <sub>Attach multiple files using Control+Click or Cmd+Click</sub><br>
                        <sub>
                            Files uploaded here will have the same placeholders replaced as in the challenge description in their text.
                            These files will not be uploaded to S3, so they should be small enough to be kept in the database.
                        </sub>
                    </div>
                    <div class="form-group">
                        <button class="btn btn-success float-right" id="submit-unique-files">Upload</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>`);

(function () {
    // Derived from core/assets/js/helpers.js upload
    function upload(form, extra, cb) {
        const data = new FormData(form);
        // Very important: without this we get 403 errors.
        data.append("nonce", CTFd.config.csrfNonce);
        for (const [key, val] of Object.entries(extra)) {
            data.append(key, val);
        }

        $.ajax({
            url: CTFd.config.urlRoot + "/api/unique/files",
            data: data,
            type: "POST",
            cache: false,
            contentType: false,
            processData: false,
            success: function(data) {
                form.reset();
                if (cb) cb(data);
            }
        })
    }

    function addFile(name, id) {
        const template = $($('#unique-files-file-row')[0].content).clone();
        template.find('a').text(name)
            .attr('href', '/api/unique/files/' + CHALLENGE_ID + '/' + id);
        template.find('i').attr('file-id', id);
        $('#unique_filesboard tbody').append(template);
    }

    $('#unique-file-add-form').submit(function(event) {
        event.preventDefault();
        const form = event.target;

        upload(form, {
            challenge: CHALLENGE_ID
        }, function(response) {
            for (const { name, id } of response.data) {
                addFile(name, id);
            }
        });
    });

    // Load existing files
    $.ajax({
        url: CTFd.config.urlRoot + "/api/unique/files/" + CHALLENGE_ID,
        success: function(response) {
            for (const { name, id } of response.data) {
                addFile(name, id);
            }
        }
    });

    // Allow deleting files
    $('#unique_filesboard tbody').click(function (event) {
        const target = $(event.target);
        const id = target.attr('file-id');
        if (id) {
            $.ajax({
                url: CTFd.config.urlRoot + "/api/unique/files/" + CHALLENGE_ID + "/" + id,
                type: 'DELETE',
                data: { nonce: CTFd.config.csrfNonce },
                success: function(response) {
                    target.parent().parent().remove()
                }
            });
        }
    })
}())



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

$('#challenge-properties').append('<a class="nav-item nav-link" data-toggle="tab" href="#unique_scripts" role="tab">Script Files</a>');
$('#nav-tabContent').append(`
<div class="tab-pane fade" id="unique_scripts" role="tabpanel">
    <div class="row">
        <div class="col-md-12">
            <h3 class="text-center py-3 d-block">Script Files</h3>
            <table id="script_filesboard" class="table table-striped">
                <thead>
                    <tr>
                        <td class="text-center"><b>File</b></td>
                        <td class="text-center"><b>Settings</b></td>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>
            <div class="col-md-12 mt-3">
                <form id="script-file-add-form" method="POST">
                    <div class="form-group">
                        <label>
                            File name:
                            <input class="form-control" name="name" id="script-file-name">
                        </label>
                    </div>
                    <div class="form-group">
                        <div id="script-editor"></div>
                        <sub>
                            The code you provide will be run with Python3. PLACEHOLDERS will be a dict
                            with the keys <code>flag_8</code>, <code>flag_16</code>, <code>flag_32</code>, and <code>name</code>.
                            Output to standard out will be presented to the user as a file.
                        </sub>
                    </div>
                    <div class="form-group">
                        <button class="btn btn-success float-right" id="submit-script-files">Create</button>
                        <input type="hidden" name="id" id="script-file-id">
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>`);

$('#challenge-properties').append('<a class="nav-item nav-link" data-toggle="tab" href="#advanced_requirements" role="tab">Advanced Requirements</a>');
$('#nav-tabContent').append(`
<div class="tab-pane fade" id="advanced_requirements" role="tabpanel">
    <div class="row">
        <div class="col-md-12">
            <h3 class="text-center py-3 d-block">Advanced Requirements</h3>
            <div class="col-md-12 mt-3">
                <form id="advanced-requirements-form" method="POST">
                    <div class="form-group">
                        <div id="requirements-editor"></div>
                        <sub>
                            You may enter a LispIsh expression here, which will be evaluated to determine
                            if participants may view the challenge. For information about the available functions
                            view <a href="https://github.com/Gerrit0/CTFd_unique_challenges/wiki/LispIsh-Documentation" target="_blank">
                            the wiki page.</a>
                        </sub>
                    </div>
                    <div class="form-group">
                        <button class="btn btn-success float-right" id="submit-advanced-requirements">Save</button>
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
        const template = $($('#file-row-template')[0].content).clone();
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

    /// Script editor ///
    const editor = ace.edit("script-editor");
    editor.session.setMode("ace/mode/python");

    function clearSelectedScript() {
        $('.highlight[gf-id]').removeClass('highlight')
        editor.setValue('', 1)
        $('#script-file-id').val('')
        $('#script-file-name').val('')
        $('#submit-script-files').text('Create')
    }

    function addScriptFile(name, id) {
        const template = $($('#file-row-template')[0].content).clone();
        template.find('tr').attr('gf-id', id)
        template.find('a').text(name).click(function(event) {
            event.preventDefault()
            const row = $('[gf-id=' + id + ']')
            if (row.hasClass('highlight')) {
                clearSelectedScript()
            } else {
                clearSelectedScript()
                row.addClass('highlight')
                $.ajax({
                    url: CTFd.config.urlRoot + "/api/unique/generated-files/" + CHALLENGE_ID + "/" + id,
                    data: { nonce: CTFd.config.csrfNonce },
                    success: function(response) {
                        if (!row.hasClass('highlight')) return;
                        editor.setValue(response.script || '', 1)
                        $('#script-file-name').val(response.name)
                        $('#script-file-id').attr('value', response.id)
                        $('#submit-script-files').text('Update')
                    }
                })
            }

        });
        template.find('i').attr('file-id', id);
        $('#script_filesboard tbody').append(template);
    }

    // Load existing files
    $.ajax({
        url: CTFd.config.urlRoot + "/api/unique/generated-files/" + CHALLENGE_ID,
        success: function(response) {
            for (const { name, id } of response.data) {
                addScriptFile(name, id);
            }
        }
    });

    // Creating / updating script files
    $('#script-file-add-form').submit(function(event) {
        event.preventDefault();
        const form = event.target;

        $.ajax({
            url: CTFd.config.urlRoot + "/api/unique/generated-files",
            type: 'POST',
            data: {
                nonce: CTFd.config.csrfNonce,
                challenge: CHALLENGE_ID,
                id: $('#script-file-id').val(),
                name: $('#script-file-name').val(),
                script: editor.getValue()
            },
            success: function(response) {
                if (response.created) {
                    addScriptFile(response.name, response.id)
                } else {
                    $('[gf-id=' + response.id + '] a').text(response.name)
                }
            }
        })
    });

    // Deleting script files
    $('#script_filesboard tbody').click(function (event) {
        const target = $(event.target);
        const id = target.attr('file-id');
        if (id) {
            $.ajax({
                url: CTFd.config.urlRoot + "/api/unique/generated-files/" + CHALLENGE_ID + "/" + id,
                type: 'DELETE',
                data: { nonce: CTFd.config.csrfNonce },
                success: function(response) {
                    if ($('#script-file-id').val() == id) {
                        clearSelectedScript()
                    }
                    target.parent().parent().remove()
                }
            });
        }
    })

    /// Advanced Requirements
    const reqEditor = ace.edit("requirements-editor");
    reqEditor.session.setMode("ace/mode/lisp");

    $.ajax({
        url: CTFd.config.urlRoot + "/api/unique/requirements/" + CHALLENGE_ID,
        success: function(response) {
            reqEditor.setValue(response.script, 1)
        }
    })

    $('#advanced-requirements-form').submit(function(event) {
        event.preventDefault();

        $.ajax({
            url: CTFd.config.urlRoot + "/api/unique/requirements/" + CHALLENGE_ID,
            type: 'POST',
            data: {
                nonce: CTFd.config.csrfNonce,
                script: reqEditor.getValue()
            },
            success: function(response) {
                if (response.status == 'ok') {
                    reqEditor.setValue(response.script, 1)
                } else {
                    alert(response.error)
                }
            }
        })
    });
}())

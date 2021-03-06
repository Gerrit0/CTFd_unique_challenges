/// <reference path="./globals.d.ts" />
/// <reference path="./lispish.js" />
//@ts-check

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
            <label>
                <input type="checkbox" data-toggle="code"> Show Code
            </label>

            <div class="col-md-12 mt-3" data-show="code:checked">
                <div id="requirements-editor"></div>
                <sub>
                    You may enter a LispIsh expression here, which will be evaluated to determine
                    if participants may view the challenge. For information about the available functions
                    view <a href="https://github.com/Gerrit0/CTFd_unique_challenges/wiki/LispIsh-Documentation" target="_blank">
                    the wiki page.</a>
                </sub>
            </div>

            <div class="col-md-12 mt-3" data-show="code:unchecked">
                <div id="advanced_requirements_gui">
                    <button class="remove">remove</button>
                </div>
                <sub>
                    For information about what each block does view
                    <a href="https://github.com/Gerrit0/CTFd_unique_challenges/wiki/Advanced-Requirements" target="_blank">
                    the wiki page.</a>
                </sub>
            </div>

            <div class="col-md-12 mt-3">
                <button class="btn btn-success float-right" id="submit-advanced-requirements">Save</button>
            </div>
        </div>
    </div>
</div>`)

;(function () {
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

    const reqEditor = ace.edit("requirements-editor");
    reqEditor.session.setMode("ace/mode/lisp");

    $('#submit-advanced-requirements').click(function(event) {
        const toggle = /** @type {HTMLInputElement} */ (document.querySelector('#advanced_requirements [data-toggle="code"]'))
        if (!toggle.checked) {
            copyToEditor()
        }

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

    const guiRoot = $('#advanced_requirements_gui')

    // Load challenges for autocomplete
    // http://localhost:4000/api/v1/challenges
    Promise.all([
        // Load cohorts for autocomplete
        $.ajax({
            url: CTFd.config.urlRoot + "/api/unique/cohorts",
            success: function(response) {
                const datalist = document.querySelector('#cohort_autocomplete')
                if (response.status === 'ok') {
                    for (const { name, id } of response.cohorts) {
                        const option = datalist.appendChild(document.createElement('option'))
                        option.value = name
                        option.dataset.id = id
                    }
                } else {
                    alert('Failed to fetch cohorts. Refresh page.')
                    throw 'fail'
                }
            }
        }),
        $.ajax({
            url: CTFd.config.urlRoot + "/api/v1/challenges",
            success: function(response) {
                const datalist = document.querySelector('#challenges_autocomplete')
                if (response.success) {
                    for (const { name, id } of response.data) {
                        const option = datalist.appendChild(document.createElement('option'))
                        option.value = name
                        option.dataset.id = id
                    }

                } else {
                    alert('Failed to fetch challenges. Refresh page.')
                    throw 'fail'
                }
            }
        })
    ]).then(() => {
        $.ajax({
            url: CTFd.config.urlRoot + "/api/unique/requirements/" + CHALLENGE_ID,
            success: function(response) {
                reqEditor.setValue(response.script, 1)
                buildGui(response.script)
            }
        })
    })


    $('#advanced_requirements [data-toggle]').each(function() {
        const checked = (/** @type {HTMLInputElement} */ (this)).checked ? 'unchecked' : 'checked'
        $(`#advanced_requirements [data-show="${this.dataset.toggle}:${checked}"]`).attr('hidden', 'hidden')
    })

    $('#advanced_requirements [data-toggle]').change(ev => {
        const checked = (/** @type {HTMLInputElement} */ (ev.target)).checked
        $(`#advanced_requirements [data-show="${ev.target.dataset.toggle}:${checked ? 'checked' : 'unchecked'}"]`).removeAttr('hidden')
        $(`#advanced_requirements [data-show="${ev.target.dataset.toggle}:${checked ? 'unchecked' : 'checked'}"]`).attr('hidden', 'hidden')

        if (checked) {
            copyToEditor()
        } else {
            pickers.forEach(picker => picker.destroy())
            pickers.length = 0
            const root = guiRoot[0].querySelector('.block')
            if (root) root.remove()
            buildGui(reqEditor.getValue())
        }
    })

    /** @type {WeakMap<HTMLElement, LispIshValue>} */
    const LISPISH_VALUE_CACHE = new WeakMap()
    /** @type {HTMLDataListElement} */
    const challengeAutocomplete = document.querySelector('#challenges_autocomplete')
    const cohortAutocomplete = document.querySelector('#cohort_autocomplete')

    const pickers = []
    let removing = false

    guiRoot.find('.remove').click(function () {
        removing = !removing
        guiRoot.find('.remove').toggleClass('active')
        document.body.classList.toggle('removing')
    })

    guiRoot.change(function(event) {
        const target = event.target
        if (target instanceof HTMLSelectElement) {
            const parent = getParentBlock(target.parentElement)
            const grandparentValue = getValue(parent.parentElement)
            let value = getValue(parent)
            const orig = value
            if (!value) {
                throw new Error('Failed to get a value from LISPISH_VALUE_CACHE')
            }
            if (value instanceof LispIshMethod && target.value !== 'string' && target.value !== 'number') {
                value.rename(target.value)
            } else {
                if (target.value === 'string') {
                    value = new LispIshString(value instanceof LispIshMethod ? '' : (/** @type {LispIshString} */(value)).value.toString())
                } else if (target.value === 'number') {
                    value = new LispIshNumber(+value.emit(0) || 0)
                } else {
                    value = new LispIshMethod(target.value, [value])
                }
            }
            if (grandparentValue instanceof LispIshMethod && orig !== value) {
                grandparentValue.args = grandparentValue.args.filter(arg => arg !== orig)
                grandparentValue.args.push(value)
            }
            const replace = buildFromValue(value)
            parent.replaceWith(replace)
            updateBlockSizeFromChildren(getParentBlock(replace.parentElement))
        }

        if (target instanceof HTMLInputElement) {
            let parent = getParentBlock(target.parentElement)
            if (!parent) return

            const value = LISPISH_VALUE_CACHE.get(parent)
            if (!value) {
                throw new Error('Failed to get a value from LISPISH_VALUE_CACHE.')
            }

            if (value instanceof LispIshString) {
                value.value = target.value
            } else if (value instanceof LispIshNumber) {
                value.value = +target.value || 0
            } else if (value instanceof LispIshMethod && value.canonical_name === 'COMPLETED') {
                // Prefer IDs if they exist, otherwise use strings.
                value.args = Array.from(parent.querySelectorAll('input')).map(el => el.value)
                    .map(name => {
                        const autoEl = Array.from(challengeAutocomplete.children)
                            .find(el => el.getAttribute('value') === name)
                        if (autoEl) {
                            return new LispIshNumber(+(/** @type {HTMLInputElement} */(autoEl)).dataset.id)
                        }
                        return new LispIshString(name)
                    })
            } else if (value instanceof LispIshMethod && value.canonical_name === 'COHORT') {
                // Prefer IDs if they exist, otherwise use strings.
                value.args = Array.from(parent.querySelectorAll('input')).map(el => el.value)
                    .map(name => {
                        const autoEl = Array.from(cohortAutocomplete.children)
                            .find(el => el.getAttribute('value') === name)
                        if (autoEl) {
                            return new LispIshNumber(+(/** @type {HTMLInputElement} */(autoEl)).dataset.id)
                        }
                        return new LispIshString(name)
                    })
            } else if (value instanceof LispIshMethod && ['BEFORE', 'AFTER'].includes(value.canonical_name)) {
                value.args = [new LispIshString(parent.querySelector('input').value)]
            }
        }
    })

    guiRoot.click(ev => {
        if (!ev.target) return

        // Removal
        if (removing && ev.target.classList.contains('removing')) {
            const value = LISPISH_VALUE_CACHE.get(ev.target)
            const parent = getParentBlock(ev.target.parentElement)
            const parentValue = getValue(parent)
            if (parentValue instanceof LispIshMethod) { // Should always pass.
                parentValue.args = parentValue.args.filter(v => v !== value)
            }
            parent.replaceWith(buildFromValue(parentValue))
        }

        // Addition
        if (ev.target.classList.contains('add')) {
            const parent = getParentBlock(ev.target.parentElement)
            const parentValue = getValue(parent)
            if (parentValue instanceof LispIshMethod) { // Should always pass
                parentValue.args.push(new LispIshString(""))
            }
            parent.replaceWith(buildFromValue(parentValue))
        }

        // Collapsing
        if (!ev.target.classList.contains('big')) return
        if (ev.offsetX < 18 && ev.offsetY < 18) {
            ev.target.classList.toggle('collapsed')
        }
    })

    /** @type {Element | undefined | null} */
    let prev
    guiRoot[0].addEventListener('mousemove', ev => {
        if (!removing) return
        let el = getParentBlock(/** @type {HTMLElement} */ (document.elementFromPoint(ev.clientX, ev.clientY)))

        if (prev === el) return

        if (prev) prev.classList.remove('removing')
        prev = null

        if (el && el.classList.contains('block') && el.parentElement !== guiRoot[0]) {
          prev = el
          el.classList.add('removing')
        }
    }, { passive: true })

    // Advanced requirements GUI
    /** @type {[string, string][]} */
    const TYPES = [
        ['number', 'Number'],
        ['string', 'String'],
        ['=', '='],
        ['/=', '&ne;'],
        ['and', 'and'],
        ['or', 'or'],
        ['not', 'not'],
        ['user-email', 'User email'],
        ['user-name', 'User name'],
        ['user-id', 'User ID'],
        ['user-score', 'User score'],
        ['completed', 'Completed challenges'],
        ['cohort', 'Cohorts'],
        ['before', 'Before'],
        ['after', 'After'],
        ['+', '+'],
        ['-', '-'],
        ['max', 'max'],
        ['min', 'min'],
        ['>', '>'],
        ['>=', '&ge;'],
        ['<', '&lt;'],
        ['<=', '&le;'],
    ]

    // Rules:
    // A block can be tiny only if it has one or two children
    // A block can be small only if all of its children are tiny
    // A block is big if it is neither tiny nor small
    // Big blocks may not have tiny children
    /** @type {(children: HTMLElement[]) => string} */
    function getSizeClass(children) {
        if (children.length <= 2) {
            return children.every(child => child.classList.contains('tiny')) ? 'small' : 'big'
        }
        return 'big'
    }

    /** @type {(parentClass: string, children: HTMLElement[]) => void} */
    function updateBlockClass(parentClass, children) {
        if (parentClass === 'big') {
            children.forEach(child => {
                if (child.classList.contains('tiny')) {
                    child.classList.remove('tiny')
                    child.classList.add('small')
                }
            })
        }
    }

    /** @type {(block: HTMLElement) => void} */
    function updateBlockSizeFromChildren(block) {
        if (!block) return; // Edited the root node

        // We need to traverse the tree, but not go within elements with .block.
        /** @type {HTMLElement[]} */
        const children = []
        // Kind of hacky... I can't simply consume the iterator because whenever I want to
        // accept a node, I want to reject all descendants.
        const iter = document.createTreeWalker(block, NodeFilter.SHOW_ELEMENT, {
            acceptNode(node) {
                if (node instanceof HTMLElement) {
                    if (node.classList.contains('block')) {
                        children.push(node)
                        return NodeFilter.FILTER_REJECT
                    }
                    return NodeFilter.FILTER_SKIP
                }
                return NodeFilter.FILTER_SKIP
            }
        })
        while (iter.nextNode()) {}

        const size = getSizeClass(children)
        block.classList.remove('big', 'small', 'tiny')
        block.classList.add(size)
        updateBlockClass(size, children)
    }

    function makeTypeDropdown() {
        const parent = document.createElement('select');
        for (const [ val, display ] of TYPES) {
            const option = document.createElement('option')
            option.value = val
            option.innerHTML = display
            parent.appendChild(option)
        }
        return parent
    }

    /** @type {(children: HTMLElement[], method: string, display?: string) => HTMLElement} */
    function makeInfixBlock(children, method, display = method) {
        const parent = document.createElement('div')
        parent.classList.add('block')
        parent.appendChild(children[0])
        parent.appendChild(makeTypeDropdown()).value = method
        if (children[1]) {
            parent.appendChild(children[1])
        }
        for (const child of children.slice(2)) {
            const joiner = document.createElement('span')
            joiner.classList.add('secondary')
            joiner.innerHTML = display
            parent.appendChild(joiner)
            parent.appendChild(child)
        }

        const addButton = document.createElement('button')
        addButton.classList.add('add')
        addButton.innerHTML = display
        parent.appendChild(addButton)

        updateBlockSizeFromChildren(parent)
        return parent
    }

    function makeMinMaxBlock(children, method) {
        const sizeClass = getSizeClass(children)
        updateBlockClass(sizeClass, children)

        const parent = document.createElement('div')
        parent.classList.add('block', sizeClass)
        parent.appendChild(makeTypeDropdown()).value = method

        const list = document.createElement('ul')
        for (const child of children) {
            const li = list.appendChild(document.createElement('li'))
            li.appendChild(child)
        }
        parent.appendChild(list)

        const addButton = document.createElement('button')
        addButton.classList.add('add')
        addButton.innerHTML = 'value'
        parent.appendChild(addButton)

        return parent
    }

    /** @type {(method: string, when: string | number) => HTMLElement} */
    function makeBeforeAfterBlock(method, when) {
        const block = document.createElement('div')
        block.appendChild(makeTypeDropdown()).value = method
        block.classList.add('block', 'small')

        const input = block.appendChild(document.createElement('input'))
        input.value = when.toString()
        pickers.push(flatpickr(input, {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            altInput: true,
            altFormat: "F j, Y, h:i K"
        }))

        return block;
    }

    // We know a bit more about what is allowed for LispIsh than the language itself lets on
    // https://github.com/Gerrit0/CTFd_unique_challenges/wiki/LispIsh-Documentation
    // Method => (min, max?), inclusive.
    /** @type {Record<string, (children: HTMLElement[], value?: LispIshValue) => HTMLElement>} */
    const FACTORIES = {
        number: function(_, value = new LispIshNumber(1)) { // [0, 0]
            const parent = document.createElement('div')
            parent.classList.add('block', 'tiny')
            parent.appendChild(makeTypeDropdown()).value = 'number'

            const input = document.createElement('input')
            input.type = 'number'
            input.value = value.emit(0) // Don't need to cast as it isn't wrapped in quotes.
            parent.appendChild(input)
            return parent
        },
        string: function(_, value = new LispIshString("")) { // [0, 0]
            const parent = document.createElement('div')
            parent.classList.add('block', 'tiny')
            parent.appendChild(makeTypeDropdown()).value = 'string'

            const input = document.createElement('input')
            input.value = /** @type {LispIshString} */(value).value
            parent.appendChild(input)
            return parent
        },

        '=': function(children) { // [2, inf)
            while (children.length < 2) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '=')
        },
        '/=': function(children) { // [2, inf)
            while (children.length < 2) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '/=', '&ne;')
        },
        'and': function(children) { // [0, inf)
            return makeInfixBlock(children, 'and')
        },
        'or': function(children) { // [0, inf)
            return makeInfixBlock(children, 'or')
        },
        '+': function(children) { // [0, inf)
            return makeInfixBlock(children, '+')
        },
        '-': function(children) { // [1, inf)
            if (children.length < 1) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '-')
        },
        'max': function(children) { // [1, inf)
            if (children.length < 1) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeMinMaxBlock(children, 'max')
        },
        'min': function(children) { // [1, inf)
            if (children.length < 1) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeMinMaxBlock(children, 'min')
        },
        '>': function(children) { // [2, inf)
            while (children.length < 2) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '>')
        },
        '>=': function(children) { // [2, inf)
            while (children.length < 2) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '>=', '&ge;')
        },
        '<': function(children) { // [2, inf)
            while (children.length < 2) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '<', '&lt;')
        },
        '<=': function(children) { // [2, inf)
            while (children.length < 2) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }
            return makeInfixBlock(children, '<=', '&le;')
        },
        'user-email': function() {
            const block = document.createElement('div')
            block.classList.add('block', 'tiny')
            block.appendChild(makeTypeDropdown()).value = 'user-email'
            return block
        },
        'user-name': function() {
            const block = document.createElement('div')
            block.classList.add('block', 'tiny')
            block.appendChild(makeTypeDropdown()).value = 'user-name'
            return block
        },
        'user-id': function() {
            const block = document.createElement('div')
            block.classList.add('block', 'tiny')
            block.appendChild(makeTypeDropdown()).value = 'user-id'
            return block
        },
        'user-score': function() {
            const block = document.createElement('div')
            block.classList.add('block', 'tiny')
            block.appendChild(makeTypeDropdown()).value = 'user-score'
            return block
        },
        'not': function(children) { // [1, 1]
            if (children.length < 1) {
                children.push(buildFromValue(new LispIshNumber(1)))
            }

            const block = document.createElement('div')
            block.appendChild(makeTypeDropdown()).value = 'not'
            block.classList.add('block', children[0].classList.contains('tiny') ? 'small' : 'big')
            block.appendChild(children[0])

            return block;
        },
        // Completed is special, arguments can be either strings or values.
        'completed': function (_, value) { // [0, inf)
            if (!(value instanceof LispIshMethod)) {
                throw new Error('Bad factory call.')
            }
            const parent = document.createElement('div')
            parent.classList.add('block', 'big')
            parent.appendChild(makeTypeDropdown()).value = 'completed'

            const list = document.createElement('ul')
            for (const arg of value.args) {
                const input = list.appendChild(document.createElement('input'))
                input.setAttribute('list', 'challenges_autocomplete')
                if (arg instanceof LispIshNumber) {
                    // Lookup in autocomplete
                    const option = document.querySelector(`#challenges_autocomplete [data-id="${arg.value}"]`)
                    if (option) {
                        input.value = (/** @type {HTMLOptionElement} */ (option)).value;
                    }
                } else if (arg instanceof LispIshString) {
                    input.value = arg.value
                }

                const li = list.appendChild(document.createElement('li'))
                li.appendChild(input)
            }
            parent.appendChild(list)

            const addButton = document.createElement('button')
            addButton.classList.add('add')
            addButton.innerHTML = 'challenge'
            parent.appendChild(addButton)

            return parent
        },
        // Cohort is just as special as completed, just a different set of values.
        'cohort': function (_, value) { // [0, inf)
            if (!(value instanceof LispIshMethod)) {
                throw new Error('Bad factory call.')
            }
            const parent = document.createElement('div')
            parent.classList.add('block', 'big')
            parent.appendChild(makeTypeDropdown()).value = 'cohort'

            const list = document.createElement('ul')
            for (const arg of value.args) {
                const input = list.appendChild(document.createElement('input'))
                input.setAttribute('list', 'cohort_autocomplete')
                if (arg instanceof LispIshNumber) {
                    // Lookup in autocomplete
                    const option = document.querySelector(`#cohort_autocomplete [data-id="${arg.value}"]`)
                    if (option) {
                        input.value = (/** @type {HTMLOptionElement} */ (option)).value;
                    }
                } else if (arg instanceof LispIshString) {
                    input.value = arg.value
                }

                const li = list.appendChild(document.createElement('li'))
                li.appendChild(input)
            }
            parent.appendChild(list)

            const addButton = document.createElement('button')
            addButton.classList.add('add')
            addButton.innerHTML = 'cohort'
            parent.appendChild(addButton)

            return parent
        },
        'before': function(_, value) { // [1, 1]
            if (!(value instanceof LispIshMethod)) {
                throw new Error('Bad factory call.')
            }
            if (value.args.length < 1) {
                value.args.push(new LispIshString('today'))
            }
            const arg = value.args[0]
            if (arg instanceof LispIshNumber || arg instanceof LispIshString) {
                return makeBeforeAfterBlock('before', arg.value)
            }
            throw new Error('before accepts either a string or number as its argument.')
        },
        'after': function(_, value) { // [1, 1]
            if (!(value instanceof LispIshMethod)) {
                throw new Error('Bad factory call.')
            }
            if (value.args.length < 1) {
                value.args.push(new LispIshString('today'))
            }
            const arg = value.args[0]
            if (arg instanceof LispIshNumber || arg instanceof LispIshString) {
                return makeBeforeAfterBlock('after', arg.value)
            }
            throw new Error('after accepts either a string or number as its argument.')
        }
    }

    /** @param {string} script */
    function buildGui(script) {
        const lisp = new LispIsh()
        try {
            const method = lisp.parse(script || '(= 1 1)')
            guiRoot.append(buildFromValue(method))
        } catch (error) {
            const errBlock = guiRoot[0].appendChild(document.createElement('div'))
            errBlock.classList.add('block', 'big')
            errBlock.style.whiteSpace = 'pre-wrap'
            errBlock.textContent += 'Error parsing script: ' + error
            errBlock.textContent += '\nCheck the show code box and fix errors.'
        }
    }

    function copyToEditor() {
        const root = /** @type {HTMLElement} */ (guiRoot[0].querySelector('.block'))
        const value = LISPISH_VALUE_CACHE.get(root)
        if (value) {
            reqEditor.setValue(value.emit(0), 1)
        }
    }

    /** @type {(value: LispIshValue) => HTMLElement} */
    function buildFromValue(value) {
        /** @type {HTMLElement} */
        let el;
        if (value instanceof LispIshMethod) {
            const key = value.name.toLowerCase()
            const factory = FACTORIES[value.name.toLowerCase()]
            if (!factory || key === 'number' || key === 'string') {
                throw new Error(`Tried to create GUI for an unknown method: '${key}'`)
            }
            el = factory(value.args.map(buildFromValue), value)
        } else if (value instanceof LispIshNumber) {
            el = FACTORIES.number([], value)
        } else if (value instanceof LispIshString) {
            el = FACTORIES.string([], value)
        }
        LISPISH_VALUE_CACHE.set(el, value)
        return el
    }

    /** @param {HTMLElement} el */
    function getParentBlock(el) {
        while (el && !el.classList.contains('block')) {
            el = el.parentElement
        }

        return el
    }

    /** @param {HTMLElement} el */
    function getValue(el) {
        return LISPISH_VALUE_CACHE.get(getParentBlock(el) || document.createElement('div'))
    }
}())

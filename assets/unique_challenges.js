// @ts-check

$('#unique_challenges_config_form').submit(function(event) {
    event.preventDefault()
    const form = event.target
    const data = new FormData(/** @type {any} */ (form))
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

/**
 * @typedef {object} Suspect
 * @property {number} challenge_id
 * @property {string} challenge_name
 * @property {number | null} team_id
 * @property {number} user_id
 * @property {number | null} source_user
 * @property {number | null} source_team
 */

/** @type {Suspect[]} */
let suspects = []
/** @type {Map<number, string>} */
const users = new Map()
/** @type {Map<number, string>} */
const teams = new Map()

$.ajax({
    url: CTFd.config.urlRoot + "/api/unique/audit",
    success: function (data) {
        suspects = data.suspect
        for (const user of data.users) {
            users.set(user.id, user.name)
        }
        for (const team of data.teams) {
            teams.set(team.id, team.name)
        }
        rebuildAudit()
    }
})

/**
 * @template T
 * @typedef Sorter
 * @property {(a: T, b: T) => number} run
 * @property {(fn: (a: T, b: T) => boolean) => Sorter<T>} thenBy
 */

/**
 * Simple sort helper because I find sort predicates that return a boolean easier to reason about.
 * @template T
 * @param {(a: T, b: T) => boolean} fn
 * @returns {Sorter<T>}
 */
function sort(fn) {
    return {
        run: function(a, b) {
            if (fn(a, b)) {
                return -1
            }
            if (fn(b, a)) {
                return 1
            }
            return 0
        },
        thenBy: function(next) {
            return sort(function (a, b) {
                if (fn(a, b)) {
                    return true
                }
                if (fn(b, a)) {
                    return false
                }
                return next(a, b)
            })
        }
    }
}

/** @type {Record<string, Sorter<Suspect>>} */
const sorters = {
    challenge: sort(function (a, b) {
        return a.challenge_name < b.challenge_name
    }).thenBy(function (a, b) {
        return users.get(a.user_id) < users.get(b.user_id)
    }),
    submit: sort(function(a, b) {
        if (a.team_id != null) {
            return teams.get(a.team_id) < teams.get(b.team_id)
        }
        return users.get(a.user_id) < users.get(b.user_id)
    }).thenBy(function(a, b) {
        return a.challenge_name < b.challenge_name
    }),
    copied: sort(function(a, b) {
        if (a.source_team != null) {
            return teams.get(a.source_team) < teams.get(b.source_team)
        }
        return false // Sort by users
    }).thenBy(function(a, b) {
        return users.get(a.source_user) < users.get(b.source_user)
    })
}

const template = $(/** @type {HTMLTemplateElement} */($('#suspect-info')[0]).content)

$('#audit-grouping').change(rebuildAudit)
function rebuildAudit() {
    const sorter = /** @type {string} */ ($('#audit-grouping').val())
    suspects.sort(sorters[sorter].run)

    $('#auditing tbody').children().remove()
    for (const suspect of suspects) {
        const sTempl = template.clone()
        sTempl.find('[data-text="chal"]')
            .attr('href', '/admin/challenges/' + suspect.challenge_id)
            .text(suspect.challenge_name)
        sTempl.find('[data-text="user"]')
            .attr('href', '/admin/users/' + suspect.user_id)
            .text(users.get(suspect.user_id))
        sTempl.find('[data-text="team"]')
            .attr('href', '/admin/teams/' + suspect.team_id)
            .text(teams.get(suspect.team_id))
        sTempl.find('[data-text="copy_user"]')
            .attr('href', '/admin/users/' + suspect.source_user)
            .text(users.get(suspect.source_user))
        sTempl.find('[data-text="copy_team"]')
            .attr('href', '/admin/teams/' + suspect.source_team)
            .text(teams.get(suspect.source_team))
        $('#auditing tbody').append(sTempl)
    }
    if (!suspects.length) {
        $('#auditing tbody').append('No audit events found.')
    }
}

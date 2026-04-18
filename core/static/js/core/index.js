$(function () {

    const deleteModal = $('#crudDeleteModal form')

    $('table tr .crud-delete-button').click(function (e) {
        const target = $(this)
        console.log(target)
        const delete_url = target.data('delete-url')
        deleteModal.attr('action', delete_url)
    })

    $('#logout').click(function () {
        $(this).parent('form:first').submit()
    })


    newSelectr($('select:enabled'))


    newDatePicker($('.datepicker-input'))
})

function newSelectr(selector) {
    const select = $(selector)
    if (select.length > 0) select.each(function (index, item) {
        new Selectr(item)
    })
}

function newDatePicker(selector) {
    const select = $(selector)
    if (select.length > 0) select.each(function (index, item) {
        new Datepicker(item)
    })
}


const global_loading_spinner = $(`<div class="d-flex justify-content-center w-100">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>`)
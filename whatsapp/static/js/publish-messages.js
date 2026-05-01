$(document).ready(function () {
    $('tbody tr').click(function () {
        const checkbox = $(this).find('input[type="checkbox"]')
        checkbox.attr('checked', !checkbox.attr('checked'))
        updateSubmitButton()
    })
})

function updateSubmitButton() {
    const form = $('form[method="post"]')
    const submit_btn = form.find('input[type="submit"]')

    if (form.find('input[checked]').length === 0)
        submit_btn.addClass('disabled').prop('disabled', true)
    else submit_btn.removeClass('disabled').prop('disabled', false)
}
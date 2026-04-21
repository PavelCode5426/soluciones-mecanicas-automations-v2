// sort-messages.js
var tbody = document.querySelector('#sortable-table tbody');
if (tbody) {
    new Sortable(tbody, {animation: 150, handle: '.handler'});
}
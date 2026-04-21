// sort-messages.js
var tbody = document.querySelector('#sortable-table tbody');
if (tbody) {
    new Sortable(tbody, {
        animation: 150,
        multiDrag: true,
        selectedClass: 'bg-secondary',
        fallbackTolerance: 3,
    });
}
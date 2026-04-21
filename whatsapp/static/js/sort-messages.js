// sort-messages.js
var group = document.querySelector('#sortable-list');
if (group) {
    new Sortable(group, {
        animation: 150, multiDrag: true, selectedClass: 'active'
    });
}
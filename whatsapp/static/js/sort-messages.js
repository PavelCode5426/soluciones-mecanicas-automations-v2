var group = document.querySelector('#sortable-list');
if (group) {
    new Sortable(group, {
        animation: 150, multiDrag: true, selectedClass: 'active', onEnd: function () {
            var items = group.children;
            for (var i = 0; i < items.length; i++) {
                var input = items[i].querySelector('input[name$="-ORDER"]');
                if (input) {
                    input.value = i; // or i+1 for 1-indexed
                }
            }
        }
    });
}
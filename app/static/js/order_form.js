
function addItemRow() {
  const container = document.getElementById('order-items');
  const template = document.getElementById('item-template');
  const clone = template.content.cloneNode(true);
  container.appendChild(clone);
}
function removeItemRow(btn) {
  btn.closest('.item-row').remove();
}
window.addEventListener('DOMContentLoaded', () => {
  const addBtn = document.getElementById('add-item');
  if (addBtn) addBtn.addEventListener('click', addItemRow);
});

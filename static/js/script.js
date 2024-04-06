// JavaScript code to toggle the visibility of the edit links
const linkItems = document.querySelectorAll('.link-item');
const itemList = document.getElementById('itemList');

linkItems.forEach(linkItem => {
    const mainLink = linkItem.querySelector('.main-link');
    const editLinks = linkItem.querySelector('.edit-links');

    mainLink.addEventListener('contextmenu', function(event) {
        event.preventDefault(); // Prevent default right-click behavior
         // Toggle the visibility of edit links
        editLinks.style.display = 'block';
    });
    // Hide link list on click outside
document.addEventListener('click', function(event) {
    if (event.target !== mainLink) {
        editLinks.style.display = 'none';
    }
});
});
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

// Checkbox javascript to change color of task text
// Get the checkbox and text element
const taskTexts = document.querySelectorAll('.taskText');
const checkboxes = document.querySelectorAll('.check');

checkboxes.forEach((checkbox, id) => {
    // Add event listener to the checkbox
    checkbox.addEventListener('change', function() {
        // Toggle the 'checked' class on the corresponding anchor element
        taskTexts[id].classList.toggle('checked', checkbox.checked);
    });
});


// JavaScript functions to show/hide the pop-up form
function openForm() {
    document.getElementById("loginForm").style.display = "block";
}

function closeForm() {
    document.getElementById("loginForm").style.display = "none";
}
// ajax_inv.js
// Pulled from 437 ajax_todolist/todo.js
// See 437 hw2 for impl details

// Sends a new request to update the to-do list
function getList() {
    $.ajax({
        url: "/get-list",
        dataType : "json",
        success: updateList,
        error: updateError
    });
}


function updateError(xhr) {
    // Normal operation
    if (xhr.status == 200) {
        let response = JSON.parse(xhr.responseText)
        updateList(response)
        return
    }
    // Error cases
    if (xhr.status == 0) {
        displayError("Cannot connect to server")
        return
    }
    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }
    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }
    displayError(response)
}

function displayError(message) {
    $("#error").html(message);
}
function updateList(items) {

    console.log("items: " + items)

    // Removes the old to-do list items
    let list = document.getElementById("inv-list")
    console.log(list)
    while (list.hasChildNodes()) {
        list.removeChild(list.firstChild)
    }

    // Adds each new todo-list item to the list
    for (let i = 0; i < items.length; i++) {
        let item = items[i]
        let type = item.type

        // Builds a new HTML list item for the todo-list
        let deleteButton
        if (item.user == myUserName) {
            deleteButton = "<button onclick='deleteItem(" + item.id + ")'>X</button> "
        } else {
            deleteButton = "<button style='visibility: hidden'>X</button> "
        }

        let element = document.createElement("li")
        element.innerHTML = deleteButton +
                            sanitize(type.name) +
                            ' <span class="details">' +
                            "(id=" + type.id 
                            + ", location=" + item.location.name
                            + ", type=" + item.type.name
                            + ", thumbnail=" + item.thumbnail
                            + ")"
                            + '</span>'

        // Adds the todo-list item to the HTML list
        list.appendChild(element)
    }
}

function sanitize(s) {
    // Be sure to replace ampersand first
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
}

function addItem() {
    let itemTextElement = document.getElementById("item")
    let itemTextValue   = itemTextElement.value

    // Clear input box and old error message (if any)
    itemTextElement.value = ''
    displayError('')

    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState != 4) return
        console.log('addItem asdfasdf')
        updatePage(xhr)
    }

    xhr.open("POST", addItemURL, true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send("item="+itemTextValue+"&csrfmiddlewaretoken="+getCSRFToken());
}

function deleteItem(id) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState != 4) return
        updatePage(xhr)
    }

    xhr.open("POST", deleteItemURL(id), true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send("csrfmiddlewaretoken="+getCSRFToken())
}

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}


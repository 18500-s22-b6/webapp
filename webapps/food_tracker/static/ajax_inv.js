// ajax_inv.js
// Pulled from 437 jquery_todolist/todo.js
// See 437 hw2 for impl details

// Sends a new request to update the to-do list
function getList(id) {
    $.ajax({
        url: "/get-list/"+id,
        dataType : "json",
        success: updateList,
        error: updateError
    });
}


function updateError(xhr) {
    if (xhr.status == 0) {
        displayError("Cannot connect to server")
        return
    }
    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    console.log("17: " + xhr);
    console.log(typeof(xhr))
    // console.log("25: " + xhr.responseText)
    // console.log("26: " + xhr.responseJSON)
    // let response = JSON.parse(xhr.responseText)
    // if (response.hasOwnProperty('error')) {
    //     displayError(response.error)
    //     return
    // }
    displayError(response)
}

function displayError(message) {
    console.log("35 message: " + message);
    $("#error").html(message);
}

function updateList(items) {

    console.log("items: " + items)

    // Removes the old to-do list items
    // let list = document.getElementById("inv-list")
    // console.log(list)
    // while (list.hasChildNodes()) {
    //     list.removeChild(list.firstChild)
    // }

    // Removes items from todolist if they not in items
    $("li").each(function() {
        let my_id = parseInt(this.id.substring("id_item_".length))
        let id_in_items = false
        $(items).each(function() {
            if (this.id == my_id) id_in_items = true
        })
        if (!id_in_items) this.remove()
    })

    console.log($("li").each())
    // Adds each new todolist item to the list (only if it's not already here)
    $(items).each(function() {
        let my_id = "id_item_" + this.id
        if (document.getElementById(my_id) == null) {

            // Builds a new HTML list item for the todo-list
            let deleteButton = "<button onclick='deleteItem(" + this.id + ")'>X</button> "

            console.log("72" + this)
            $("#inv-list").append(
                '<li id="id_item_' + this.id + '">' +
                sanitize(this.type.name) + " " + 
                deleteButton +
                ' <span class="details">' +
                "(id=" + this.type.id 
                + ", location=" + this.location.name
                + ", type=" + this.type.name
                + ", thumbnail=" + this.thumbnail
                + ")"
                + '</span>'
                + '</li>'
                )
        }    
    })
}

function sanitize(s) {
    // Be sure to replace ampersand first
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
}

function addItem(id) {
    let itemTextElement = document.getElementById("item-box")
    let itemTextValue   = itemTextElement.value

    // Clear input box and old error message (if any)
    itemTextElement.value = ''
    displayError('')

    $.ajax({
        url: addItemURL,
        type: "POST",
        data: "item="+itemTextValue+"&id="+id+"&csrfmiddlewaretoken="+getCSRFToken(),
        dataType : "json",
        success: updateList,
        error: updateError
    });
}

function deleteItem(id) {
    console.log("118 " + id)
    console.log("119 " + addItemURL)
    let url = deleteItemURL(id)
    console.log("121 " + url)

    $.ajax({
        url: url,
        type: "POST",
        data: "csrfmiddlewaretoken="+getCSRFToken(),
        dataType : "json",
        success: updateList,
        error: null
    });
    console.log("131 " + this)
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


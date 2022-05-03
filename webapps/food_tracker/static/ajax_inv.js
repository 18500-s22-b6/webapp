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


// TODO: COMPLETELY BROKEN FN
function updateError(xhr) {
    if (xhr.status == 0) {
        displayError("Cannot connect to server")
        return
    }
    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    // let response = JSON.parse(xhr.responseText)
    // if (response.hasOwnProperty('error')) {
    //     displayError(response.error)
    //     return
    // }
    try {displayError(response)}
    finally {displayError("generic error")}
}

function displayError(message) {
    $("#error").html(message);
}

function updateList(items) {
    items.sort(item => sanitize(item.type))
    $("#inv-list").empty()
    $("#unknown-list").empty()
    let types = {}
    items.forEach(item => {
        let type = sanitize(item.type)
        if (type != "UNKNOWN ITEM") {
            types[type] = (types[type] | 0) + 1
        } else {
            $("#unknown-list").append(
                `<li class="list-group-item">
                    <span>${type}</span>
                    <a class="btn btn-primary btn-sm float-end" href=${get_id_unknown_url(item.id)}>Identify</a>
                </li>`
            )
        }
    })

    for (let [type, quantity] of Object.entries(types)) {
        $("#inv-list").append(
            `<li class="list-group-item">
                <span>${type}</span>
                <span class="badge rounded-pill bg-primary float-end">${quantity}</span>
            </li>`
        )
    }

    if ($('#inv-list li').length == 0) {
        $('#inv-list').append(
            `<div class="h5 my-2 text-muted">This cabinet is empty</div>`
        )
    }

    if ($('#unknown-list li').length == 0) {
        $('#unidentified-items')[0].classList.add('d-none')
    } else {
        $('#unidentified-items')[0].classList.remove('d-none')
    }
    
    // $("#inv-list li").each(function() {
    //     let my_id = parseInt(this.id.substring("id_item_".length))
    //     if (!items.find(item => item.id == my_id)) {
    //         this.remove()
    //     }
    // })

    // // Adds each new item to the list (only if it's not already here)
    // $(items).each(function() {
    //     let my_id = "id_item_" + this.id

    //     if (document.getElementById(my_id) == null) {
    //         $("#inv-list").append(
    //             `<li id="id_item_${this.id}" class="list-group-item">
    //                 ${sanitize(this.type)}
    //             </li>`
    //         )
    //     }    
    // })
}

function sanitize(s) {
    // Be sure to replace ampersand first
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
}

// TODO: unclear how relevant this will be in the final deployment, post-debug
function addItem(id) {
    let itemTextElement = document.getElementById("item-box")
    let itemTextValue   = itemTextElement.value

    // Clear input box and old error message (if any)
    itemTextElement.value = ''
    displayError('')
    if(itemTextValue == '') {
        displayError('Enter an item to add.')
        return
    }

    console.log("iTV: " + itemTextValue)
    $.ajax({
        url: addItemURL,
        type: "POST",
        data: "item="+itemTextValue+"&id="+id+"&csrfmiddlewaretoken="+getCSRFToken(),
        dataType : "json",
        success: updateList,
        error: updateError
    });
}

// Ditto
function deleteItem(id) {
    let url = deleteItemURL(id)
    console.log(url)
    $.ajax({
        url: url,
        type: "POST",
        data: "csrfmiddlewaretoken="+getCSRFToken(),
        dataType : "json",
        success: updateList,
        error: updateError
    });
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


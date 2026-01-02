//JAVASCRIPT FILE//
// SIDE NAV FUNCTIONALITY
const menuOpenBtn = document.querySelector('.menu-open');
const menuCloseBtn = document.querySelector('.menu-close');
const nav = document.querySelector('.nav');

menuOpenBtn.addEventListener('click', () => {
    nav.classList.add('active');
    menuOpenBtn.style.display = 'none';
    menuCloseBtn.style.display = 'flex';
});

menuCloseBtn.addEventListener('click', () => {
    nav.classList.remove('active');
    menuCloseBtn.style.display = 'none';
    menuOpenBtn.style.display = 'flex';
});

//-----------------------


//duo window side bar functionality

const newChatBtn = document.querySelector('.new-chat-btn'); //new chat button
const chatList = document.querySelector('.chat-list'); //ul that holds chat items (add new chats)
const mainText = document.getElementById('main_text1'); //update main chat box text
//const textarea = document.querySelector('.chat-input textarea'); //message input clear
const cInput = document.querySelector('.chat-input textarea');

function addSpacing(text) {
    return text
        .replace(/(\*\*Syntax Analysis\*\*)/g, "\n\n$1")
        .replace(/(\*\*Security Analysis\*\*)/g, "\n\n$1")
        .replace(/(\*\*Style Analysis\*\*)/g, "\n\n$1")
        .replace(/(\*\*Performance Analysis\*\*)/g, "\n\n$1")
        .replace(/(\*\*AI Code Review Summary\*\*)/g, "\n\n$1");
}


function selectChat(chatItem){
    //clear the styles in active
    for (let item of chatList.children){
        item.classList.remove('active-chat');
    }

    //set chat to active (switcing through chats)
    chatItem.classList.add('active-chat');

    //update the default text inside of main chat area
    mainText.innerHTML = `<span><br>${chatItem.textContent}</span>`;
    cInput.value = "";
}

newChatBtn.addEventListener('click', () => {
    const count = chatList.children.length + 1;
    const chat = document.createElement('li'); //make new li
    chat.textContent = `Chat ${count}`;

    chat.addEventListener('click', () => selectChat(chat));//clickable

    //add to side bar list
    chatList.appendChild(chat);
    selectChat(chat); //select
});


//Allow textbox to expand and scroll

cInput.addEventListener('input', () =>{
    cInput.style.height = 'auto';
    cInput.style.height = cInput.scrollHeight + 'px';

});


//-----------API integration----------------

//-API send and recieve messages

const sendChatBtn = document.createElement("button");
sendChatBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
sendChatBtn.classList.add("send-btn");
document.querySelector(".chat-input").appendChild(sendChatBtn);

const mainContainer = document.querySelector(".main-container");




//chat message bublle
const createChat = (text, type) => {
    const msgEl = document.createElement("li");
    msgEl.classList.add("chat", type);
    const pre = document.createElement("pre");
    pre.textContent = text;    
    msgEl.appendChild(pre);
    return msgEl;
};


//calling backend

const generateResponse = (userMessage, incomingMsgEl) => {
    const messageElement = incomingMsgEl.querySelector("pre");

    fetch("http://localhost:8000/run-review", { //connects properly to backend (run-review)
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_code: userMessage })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`Server responded with ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        const llmFeedback = data.llm_feedback || "No feedback returned.";

        //for display purposes
        messageElement.innerHTML = `
            <div style="font-size: 0.95rem; line-height: 1.5; white-space:  pre-wrap">
                <strong style="font-size: 1rem;">AI Code Review Summary</strong>
                <br><br>

                ${addSpacing(llmFeedback)}


                <br><br>
                <em style="color: #888; font-size: 0.8rem;">
                    (Full technical results hidden for readability)
                </em>
            </div>
        `;
    }) //error catching default
    .catch(error => {
        messageElement.classList.add("error");
        messageElement.innerHTML = `
            <strong>Error:</strong> Could not reach backend.<br>
            Make sure the <code>backend</code> and <code>LLM Feedback Service</code> are running.
        `;
    })
    .finally(() => {
        mainContainer.scrollTo(0, mainContainer.scrollHeight);
    });
};



//chat send
const handleChat = () => {
    const userMessage = cInput.value;
    if (!userMessage) return;


    //create + display user message
    const userMsgEl = createChat(userMessage, "chat-outgoing");

    mainContainer.appendChild(userMsgEl);
    mainContainer.scrollTo(0, mainContainer.scrollHeight);

    //bot reply placeholder
    const botMsgEl = createChat("...", "chat-incoming");
    mainContainer.appendChild(botMsgEl);
    mainContainer.scrollTo(0, mainContainer.scrollHeight);

    //send to backend
    generateResponse(userMessage, botMsgEl);

    //clear input
    cInput.value = "";

};

sendChatBtn.addEventListener("click", handleChat);


// --- Send on Enter key (without Shift) ---
cInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleChat();
    }
});
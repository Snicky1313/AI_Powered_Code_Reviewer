//JAVASCRIPT FILE//


// NAV FUNCTIONALITY
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


//duo window side bar functionality

const newChatBtn = document.querySelector('.new-chat-btn'); //new chat button
const chatList = document.querySelector('.chat-list'); //ul that holds chat items (add new chats)
const mainText = document.getElementById('main_text1'); //update main chat box text
//const textarea = document.querySelector('.chat-input textarea'); //message input clear
const cInput = document.querySelector('.chat-input textarea');


function selectChat(chatItem){
    //clear the styles in active
    for (let item of chatList.children){
        item.classList.remove('active-chat');
    }

    //set chat to active
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

//const cInput = document.querySelector('.chat-input textarea');

cInput.addEventListener('input', () =>{
    cInput.style.height = 'auto';
    cInput.style.height = cInput.scrollHeight + 'px';

});


//---------------API integration------------

//-API send and recieve messages




const sendChatBtn = document.createElement("button");
sendChatBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
sendChatBtn.classList.add("send-btn");
document.querySelector(".chat-input").appendChild(sendChatBtn);

const mainContainer = document.querySelector(".main-container");

//sendChatBtn.addEventListener("click", handleChat);


//chat message bublle
const createChat = (text, type) => {
    const msgEl = document.createElement("li");
    msgEl.classList.add("chat", type);
    msgEl.innerHTML = `<p>${text}</p>`;
    return msgEl;
};


//calling backend

const generateResponse = (userMessage, incomingMsgEl) => {
    const messageElement = incomingMsgEl.querySelector("p");

    fetch("http://127.0.0.1:5003/generate_feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ combined_report: { code: userMessage } })
    })
    .then(res => {
        if (!res.ok) throw new Error("Server error");
        return res.json();
    })
    .then(data => {
        messageElement.textContent = data.llm_feedback ?? data.feedback ?? "No feedback received.";
    })
    .catch(error => {
        //error message line if server not connected
        messageElement.classList.add("error");
        messageElement.textContent = "Hello :)! Send your python code anytime and I will scan it for feedback!";
        //messageElement.textContent = "Oops! Something went wrong: " + error.message;
    })
    .finally(() => {
        mainContainer.scrollTo(0, mainContainer.scrollHeight);
    });
};




//chat send
const handleChat = () => {
    const userMessage = cInput.value.trim();
    if (!userMessage) return;


    //const mainContainer = document.querySelector(".main-container");

    //create / display user message
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


//-chat history (keep record of the chat
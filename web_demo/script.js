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
const textarea = document.querySelector('.chat-input textarea'); //message input clear


function selectChat(chatItem){
    //clear the styles in active
    for (let item of chatList.children){
        item.classList.remove('active-chat');
    }

    //set chat to active
    chatItem.classList.add('active-chat');

    //update the default text inside of main chat area

    mainText.innerHTML = `<span><br>${chatItem.textContent}</span>`;
    textarea.value = "";
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

//API integration TODO soon.
//-API send and recieve messages
//-chat history (keep record of the chat)


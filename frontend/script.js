const firebaseConfig = {
    // Your Firebase configuration here 
    // (e.g., apiKey, authDomain, projectId, etc.)
    // You wlll get this info from your Firebase project settings
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const spinner = document.getElementById('spinner');

    let uploadedFiles = [];

    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');

    loginBtn.addEventListener('click', () => {
        const provider = new firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(provider);
    });

    logoutBtn.addEventListener('click', () => {
        auth.signOut();
    });

    auth.onAuthStateChanged(async user => {
        if (user) {
            userInfo.style.display = 'block';
            userName.innerText = user.displayName;
            document.getElementById('UserName').innerText = "Hey " + user.displayName;
            try {
                const token = await user.getIdToken();
                const response = await fetch('/list-all-files', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                uploadedFiles = data.files.map(file => {
                    return { id: file.id, name: file.filename };
                });
                updateFileListUI(); 
            } catch (error) {
                console.error("Could not fetch user files:", error);
            }
            loginBtn.style.display = 'none';
        } else {
            userInfo.style.display = 'none';
            document.getElementById('UserName').innerText = "Hey {user}";
            uploadedFiles = [];
            updateFileListUI();
            loginBtn.style.display = 'block';
        }
    });
    
    const showSpinner = (show) => {
        spinner.style.display = show ? 'flex' : 'none';
    };

    const addMessage = (content, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.innerText = (sender === 'user') ? 'U' : 'S';

        const contentWrapper = document.createElement('div');
        contentWrapper.classList.add('message-content');

        if (sender === 'bot') {
            contentWrapper.innerHTML = content;
        } else {
            contentWrapper.innerText = content;
        }
        messageElement.appendChild(avatar);
        messageElement.appendChild(contentWrapper);
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageElement;
    };

    const updateFileListUI = () => {
        fileList.innerHTML = '';
        uploadedFiles.forEach(fileObject => {
            const fileItem = document.createElement('div');
            fileItem.classList.add('file-item');
            fileItem.innerHTML = `
                <span>${fileObject.name}</span>
                <button class="delete-btn" data-fileid="${fileObject.id}">&times;</button>`;
            fileList.appendChild(fileItem);
        });
    };

    // --- Core  Functions ---
    const uploadFile = async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const user = auth.currentUser;

        showSpinner(true);
        try {
            if (user) {
                const token = await user.getIdToken();
                
                const response = await fetch(`/upload`, {
                    method: 'POST',
                    headers: {'Authorization': `Bearer ${token}`},
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error('File upload failed.');
                }
                const result = await response.json(); // result contains { fileId: "...", filename: "..." }
                uploadedFiles.push({ id: result.fileId, name: result.filename });
                updateFileListUI();

            } else {
                addMessage("Please sign in to upload files.", 'bot');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            addMessage('There was an error uploading your file. Please try again.', 'bot');
        } finally {
            showSpinner(false);
        }
    };

    fileInput.addEventListener('change', (event) => {
        const files = event.target.files;
        if (files.length > 0) {
            const initialMessage = chatMessages.querySelector('.bot-message, .welcome-screen');
            if (initialMessage) {
                chatMessages.innerHTML = '';
            }
        }
        for (const file of files) {
            const isDuplicate = uploadedFiles.some(uploadedFile => uploadedFile.name === file.name);
            if (!isDuplicate) {
                uploadFile(file);
            } else {
                console.log(`Skipping duplicate file: ${file.name}`);
                addMessage(`You've already uploaded a file named "${file.name}".`, 'bot');
            }
        }
    });

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const question = userInput.value.trim();
        const user = auth.currentUser;
        if (!question) return;

        if (uploadedFiles.length === 0) {
            addMessage('Please upload a document before asking a question.', 'bot');
            return;
        }

        addMessage(question, 'user');
        userInput.value = '';
        showSpinner(true);

        try {
            const token = await user.getIdToken();
            const response = await fetch(`/chat`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                 },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error('Failed to get a response from the bot.');
            }

            const botMessageBubble = addMessage('', 'bot');
            const botContentWrapper = botMessageBubble.querySelector('.message-content');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                fullResponse += decoder.decode(value, {stream: true});
                botContentWrapper.innerHTML = marked.parse(fullResponse);
            }

        } catch (error) {
            console.error('Error during chat:', error);
            addMessage('Sorry, something went wrong. Please try again.', 'bot');
        } finally {
            showSpinner(false);
        }
    });
    
    fileList.addEventListener('click', async (event) => {
        if (event.target.classList.contains('delete-btn')) {
            const fileIdToDelete = event.target.dataset.fileid;
            const user = auth.currentUser;

            if (!user) {
                addMessage("Please sign in to delete files.", 'bot');
                return;
            }

            showSpinner(true);
            try {
                const token = await user.getIdToken();
                const response = await fetch(`/delete_files`, { 
                    method: 'DELETE', 
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ fileId: fileIdToDelete }) 
                });

                if (response.ok) {
                    uploadedFiles = uploadedFiles.filter(file => file.id !== fileIdToDelete);
                    updateFileListUI();
                    console.log(`Successfully deleted file with ID: ${fileIdToDelete}`);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Server failed to delete the file.");
                }
            } catch (error) {
                console.error('Error during file deletion:', error);
                addMessage(error.message, 'bot');
            } finally {
                showSpinner(false);
            }
        }
    });
});
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const spinner = document.getElementById('spinner');

    const uploadedFiles = new Set();
    
    const API_BASE_URL = 'http://127.0.0.1:8000';

    const showSpinner = (show) => {
        spinner.style.display = show ? 'flex' : 'none';
    };

    const addMessage = (content, sender) => {
        // 1. Create the main container (<div class="message user-message" or "bot-message">)
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        // 2. Create the avatar
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.innerText = (sender === 'user') ? 'U' : 'S';

        // 3. Create a dedicated WRAPPER for the text content
        const contentWrapper = document.createElement('div');
        contentWrapper.classList.add('message-content');

        if (sender === 'bot') {
            // For the bot, put the received HTML inside the wrapper
            contentWrapper.innerHTML = content;
        } else {
            // For the user, put plain text inside the wrapper for security
            contentWrapper.innerText = content;
        }

        // 4. Append the avatar and the content wrapper to the main container
        // Now the flexbox has only TWO children.
        messageElement.appendChild(avatar);
        messageElement.appendChild(contentWrapper);
        
        // 5. Add the complete message to the chat and scroll
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Return the main element
        return messageElement;
    };

    const updateFileListUI = () => {
        fileList.innerHTML = '';
        uploadedFiles.forEach(fileName => {
            const fileItem = document.createElement('div');
            fileItem.classList.add('file-item');
            fileItem.innerHTML = `
                <span>${fileName}</span>
                <button class="delete-btn" data-filename="${fileName}">&times;</button>
                `;
            fileList.appendChild(fileItem);
        });
    };

    // --- Core  Functions ---
    const uploadFile = async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        showSpinner(true);
        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('File upload failed.');
            }
            
            const result = await response.json();
            console.log('Upload successful:', result);
            uploadedFiles.add(file.name);
            updateFileListUI();
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
            const initialMessage = chatMessages.querySelector('.bot-message');
            if (initialMessage && initialMessage.innerText.includes("Please upload")) {
                chatMessages.innerHTML = '';
            }
        }
        for (const file of files) {
            if (!uploadedFiles.has(file.name)) {
                uploadFile(file);
            }
        }
    });

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const question = userInput.value.trim();

        if (!question) return;

        if (uploadedFiles.size === 0) {
            addMessage('Please upload a document before asking a question.', 'bot');
            return;
        }

        addMessage(question, 'user');
        userInput.value = '';
        showSpinner(true);

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error('Failed to get a response from the bot.');
            }

            // 1. Create the initial bubble (with avatar and empty content wrapper)
            const botMessageBubble = addMessage('', 'bot');
            // 2. Find the specific content area inside the bubble we just created
            const botContentWrapper = botMessageBubble.querySelector('.message-content');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                fullResponse += decoder.decode(value, {stream: true});
                
                // 3. Update the innerHTML of the content wrapper, NOT the whole bubble
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
            const fileName = event.target.dataset.filename;
            
            try {
                const response = await fetch(`${API_BASE_URL}/delete_files`, { 
                    method: 'DELETE', 
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ filename: fileName }) 
                });
                uploadedFiles.delete(fileName);
                updateFileListUI();
                console.log(`Deleted file: ${fileName}`);
            } catch (error) {
                console.error(`Error deleting file: ${fileName}`, error);
            } finally {
                showSpinner(false);
            }
        }
    });
});
<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="user-panel">
        <button v-if="!user" id="loginBtn" @click="handleLogin">
          <i class="fab fa-google"></i> Sign in with Google
        </button>
        <div v-else id="userInfo">
          <p id="userName">{{ user.displayName }}</p>
          <button id="logoutBtn" @click="handleLogout">Sign Out</button>
        </div>
      </div>

      <div class="sidebar-header">
        <h2>Document Summarizer</h2>
      </div>

      <div class="file-panel">
        <h3>Upload Documents</h3>
        <div class="drop-zone">
          <i class="fa-solid fa-file-arrow-up"></i>
          <p>Drag & drop files here, or</p>
          <label class="upload-button">
            Browse Files
            <input type="file" multiple hidden @change="handleFileUpload">
          </label>
        </div>
        
        <div class="file-list">
          <div v-for="file in uploadedFiles" :key="file.id" class="file-item">
            <span>{{ file.name }}</span>
            <button class="delete-btn" @click="deleteFile(file.id)">&times;</button>
          </div>
        </div>
      </div>
    </aside>

    <main class="chat-area">
      <div class="chat-messages" ref="chatContainer">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="logo">✨</div>
          <h2 class="UserName">Hey {{ user?.displayName || 'there' }}</h2>
          <p>Upload a document to begin analyzing and chatting.</p>
        </div>

        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role + '-message']">
          <div class="avatar">{{ msg.role === 'user' ? 'U' : 'S' }}</div>
          <div class="message-content" v-html="msg.content" v-copy-code></div>
        </div>
      </div>

      <div class="chat-input-container">
        <form class="chat-input-form" @submit.prevent="handleChatSubmit">
          <input 
            v-model="questionInput" 
            type="text" 
            placeholder="Ask a question..." 
            :disabled="isLoading"
          >
          <button type="submit">
            <i :class="isLoading ? 'fa-solid fa-stop' : 'fa-solid fa-paper-plane'"></i>
          </button>
        </form>
      </div>
    </main>

    <div v-if="isSpinnerVisible" class="spinner-overlay">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { auth, googleProvider } from './firebase';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import type { User } from 'firebase/auth';
import { Marked } from 'marked';
import { markedHighlight } from "marked-highlight";
import hljs from 'highlight.js';


// --- Variables ---
const user = ref<User | null>(null);
const uploadedFiles = ref<{id: string, name: string}[]>([]);
const messages = ref<{role: 'user' | 'bot', content: string}[]>([]);
const questionInput = ref('');
const isLoading = ref(false);
const isSpinnerVisible = ref(false);
const chatContainer = ref<HTMLElement | null>(null);
let abortController: AbortController | null = null;

// --- AUTHENTICATION ---
onMounted(() => {
  onAuthStateChanged(auth, async (currentUser) => {
    user.value = currentUser;
    if (currentUser) {
      await fetchFileList();
    } else {
      uploadedFiles.value = [];
      messages.value = [];
    }
  });
});

const handleLogin = async () => {
  try {
    await signInWithPopup(auth, googleProvider);
  } catch (e) {
    console.error(e);
  }
};

const handleLogout = async () => signOut(auth);

// --- FILE MANAGEMENT ---
const fetchFileList = async () => {
  if (!user.value) return;
  const token = await user.value.getIdToken();
  try {
    const res = await fetch('/list-all-files', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    uploadedFiles.value = data.files.map((f: any) => ({ id: f.id, name: f.filename }));
  } catch (e) {
    console.error("Fetch error", e);
  }
};

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files || !user.value) return;

  isSpinnerVisible.value = true;
  const token = await user.value.getIdToken();
  
  for (const file of target.files) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await fetch('/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
    } catch (e) {
      console.error(e);
    }
  }
  await fetchFileList();
  isSpinnerVisible.value = false;
};

const deleteFile = async (id: string) => {
  if (!user.value) return;
  const token = await user.value.getIdToken();
  await fetch('/delete_files', {
      method: 'DELETE',
      headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ fileId: id })
  });
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id);
};

// --- CHAT LOGIC ---
const vCopyCode = {
  updated(el: HTMLElement) {
    const preTags = el.querySelectorAll('pre');
    
    preTags.forEach((pre) => {
      if (pre.parentNode && (pre.parentNode as HTMLElement).classList.contains('code-wrapper')) return;

      const wrapper = document.createElement('div');
      wrapper.className = 'code-wrapper';
      
      if (pre.parentNode) {
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
      }
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
      btn.title = 'Copy to clipboard';
      
      btn.addEventListener('click', async () => {
        const code = pre.querySelector('code')?.innerText || pre.innerText;
        try {
          await navigator.clipboard.writeText(code);
          btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
          setTimeout(() => {
             btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
          }, 2000);
        } catch (err) {
          console.error('Copy failed', err);
        }
      });

      wrapper.appendChild(btn);
    });
  },
  mounted(el: HTMLElement) {
    vCopyCode.updated(el);
  }
};

const markedInstance = new Marked(
  markedHighlight({
    langPrefix: 'hljs language-',
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    }
  })
);

const handleChatSubmit = async () => {
  if (isLoading.value) {
    if (abortController) abortController.abort();
    isLoading.value = false;
    return;
  }

  if (!questionInput.value.trim() || !user.value) return;

  // Add User Message
  const q = questionInput.value;
  messages.value.push({ role: 'user', content: q });
  questionInput.value = '';
  
  // Create Placeholder for Bot Message
  messages.value.push({ role: 'bot', content: '' }); 
  const botMessageIndex = messages.value.length - 1;

  isLoading.value = true;
  abortController = new AbortController();

  try {
    const token = await user.value.getIdToken();
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question: q }),
        signal: abortController.signal
    });

    if (!response.body) throw new Error("No body");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let rawMarkdown = '';

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        rawMarkdown += chunk;
        if (messages.value[botMessageIndex]) {
             messages.value[botMessageIndex].content = await markedInstance.parse(rawMarkdown);
        }
        // Auto-scroll
        nextTick(() => {
          if (chatContainer.value) {
            chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
          }
        });
    }

  } catch (err: any) {
    if (err.name === 'AbortError') {
      if (messages.value[botMessageIndex]) {
          messages.value[botMessageIndex].content += " <br><i>[Stopped]</i>";
      }
    } else {
      console.error(err);
    }
  } finally {
    isLoading.value = false;
    abortController = null;
  }
};
</script>
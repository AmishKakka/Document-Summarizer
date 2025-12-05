/*
    Setup Firebase configuration and initialize Firebase app.
*/
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
    // Your Firebase configuration here 
    // (e.g., apiKey, authDomain, projectId, etc.)
    // You will get this info from your Firebase project settings
    apiKey: "AIzaSyDDiQZkiwDhDPY-JYfl7dPXeUq-sYmp0OI",
    authDomain: "document-summarizer-472019.firebaseapp.com",
    projectId: "document-summarizer-472019",
    storageBucket: "document-summarizer-472019.firebasestorage.app",
    messagingSenderId: "108871784288",
    appId: "1:108871784288:web:221ab6c5fffbff0e03f005",
    measurementId: "G-WYQY7YVP7N"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
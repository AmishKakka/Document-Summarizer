/*
    Setup Firebase configuration and initialize Firebase app.
*/
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
    // Your Firebase configuration here 
    // (e.g., apiKey, authDomain, projectId, etc.)
    // You will get this info from your Firebase project settings
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
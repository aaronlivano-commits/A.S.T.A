// Client-side Firebase SDK init.
// Values come from .env (copy .env.example -> .env and fill in your project).
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: "bedrock-8b03e.firebaseapp.com  ",
  projectId: "bedrock-8b03e",
  storageBucket: "bedrock-8b03e.firebasestorage.app",
  messagingSenderId: "550861317955",
  appId: "1:550861317955:web:41b11172856704c871b1f6",
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const db = getFirestore(app);
export const storage = getStorage(app);

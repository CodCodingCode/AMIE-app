import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyBXrD1PiR_p8lspftggU0sTJz-OuyPH0Bw",
  authDomain: "doctorweb-14489.firebaseapp.com",
  projectId: "doctorweb-14489",
  storageBucket: "doctorweb-14489.firebasestorage.app",
  messagingSenderId: "185520061986",
  appId: "1:185520061986:web:782e56afc103510dc9d47b",
  measurementId: "G-6BGMFJJ810"
};

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const db = getFirestore(app);

export { app, auth, provider, db };
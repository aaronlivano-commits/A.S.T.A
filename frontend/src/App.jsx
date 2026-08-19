import { useEffect, useState } from "react";
import { onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";
import { auth, googleProvider } from "@/firebase/config";
import { Button } from "@/components/ui/button";
import Dashboard from "@/components/Dashboard";
import LensScanner from "@/components/LensScanner";
import ChatWindow from "@/components/ChatWindow";
import TopicManager from "@/components/TopicManager";
import ModelTrainerModal from "@/components/ModelTrainerModal";
import { api } from "@/lib/api";

const TABS = [
  { id: "dashboard", code: "00", label: "Dashboard" },
  { id: "topics", code: "T0", label: "Topics" },
  { id: "vision", code: "02", label: "Visual Inquiry" },
  { id: "chat", code: "03", label: "Grounded Chat" },
  { id: "training", code: "04", label: "Model Training" },
];

function GoogleIcon() {
  return (
    <svg viewBox="0 0 18 18" className="w-[18px] h-[18px]" aria-hidden="true">
      <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.9c1.7-1.57 2.7-3.87 2.7-6.62z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.9-2.26c-.8.54-1.84.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.9v2.33A9 9 0 0 0 9 18z" />
      <path fill="#FBBC05" d="M3.95 10.7A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.17.28-1.7V4.97H.9A9 9 0 0 0 0 9c0 1.45.35 2.83.9 4.03l3.05-2.33z" />
      <path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .9 4.97l3.05 2.33C4.66 5.17 6.65 3.58 9 3.58z" />
    </svg>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setAuthLoading(false);
      // Ping the backend so we know Firebase auth is wired and surface server
      // config issues early instead of mid-action.
      if (u) {
        api.post("/auth/verify").catch((err) => {
          console.warn("/auth/verify failed:", err.message);
        });
      }
    });
    return unsubscribe;
  }, []);

  async function handleLogin() {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      console.error("Sign-in failed:", err);
    }
  }

  async function handleLogout() {
    try {
      await signOut(auth);
    } catch (err) {
      console.error("Sign-out failed:", err);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex flex-wrap items-center justify-between gap-4 px-6 md:px-8 py-4 bg-asta-panel border-b border-asta-line">
        <div className="flex items-baseline gap-3">
          <span className="font-display font-black text-xl text-asta-white">A.S.T.A</span>
          <span className="hidden sm:inline font-mono text-xs uppercase tracking-wide text-asta-whiteDim">
            Augmented Student Technological Assistance
          </span>
        </div>

        <div className="flex items-center gap-5">
          <div className="hidden sm:flex items-center gap-2 font-mono text-xs text-asta-blueBright">
            <span className="w-2 h-2 rounded-full bg-[#3FE07A] shadow-[0_0_8px_#3FE07A] animate-pulse-dot" />
            SYSTEM ONLINE
          </div>

          {authLoading ? null : user ? (
            <div className="flex items-center gap-3">
              {user.photoURL && (
                <img
                  src={user.photoURL}
                  alt={`${user.displayName ?? "User"}'s avatar`}
                  className="w-8 h-8 rounded-full border-2 border-asta-blueBright object-cover"
                />
              )}
              <span className="hidden sm:inline font-mono text-xs text-asta-white max-w-[140px] truncate">
                {user.displayName ?? user.email}
              </span>
              <Button variant="danger" chamfer="6px" onClick={handleLogout}>
                LOG OUT
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              chamfer="8px"
              onClick={handleLogin}
              className="!bg-asta-white !text-[#1a1a1a] !shadow-none hover:!shadow-none"
            >
              <GoogleIcon />
              SIGN IN WITH GOOGLE
            </Button>
          )}
        </div>
      </header>

      <div className="hazard-strip" />

      <nav className="sticky top-0 z-30 flex gap-0.5 overflow-x-auto bg-asta-panel border-b border-asta-line px-4 md:px-6 py-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-shrink-0 flex items-center gap-2 px-4 py-3 text-xs font-display font-bold whitespace-nowrap border-b-2 transition-colors ${
              activeTab === tab.id
                ? "bg-asta-blueDeep text-asta-white border-asta-yellow"
                : "bg-asta-panelAlt text-asta-whiteDim border-transparent hover:text-asta-white"
            }`}
          >
            <span className={`font-mono text-xs ${activeTab === tab.id ? "text-asta-yellow" : "text-asta-blueBright"}`}>
              {tab.code}
            </span>
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 md:px-6 py-10">
        {activeTab === "dashboard" && <Dashboard />}
        {activeTab === "topics" && <TopicManager />}
        {activeTab === "vision" && <LensScanner />}
        {activeTab === "chat" && <ChatWindow />}
        {activeTab === "training" && (
          <div className="flex flex-col items-start gap-4">
            <p className="text-asta-whiteDim max-w-[70ch]">
              Upload a dataset to fine-tune your own study assistant, or import a
              bundle someone else already trained.
            </p>
            <ModelTrainerModal />
          </div>
        )}
      </main>

      <div className="hazard-strip" />

      <footer className="flex flex-wrap items-center justify-between gap-2 px-6 md:px-8 py-5 bg-asta-panel font-mono text-xs text-asta-whiteDim">
        <span className="text-asta-red">A.S.T.A. // CONSOLE BUILD 3.7</span>
        <span>Augmented Student Technological Assistance — grounded, multimodal, portable.</span>
      </footer>
    </div>
  );
}

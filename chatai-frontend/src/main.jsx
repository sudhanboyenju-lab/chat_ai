import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import TopQuestions from './components/TopQuestions'   // ← add this line

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <App />
        <TopQuestions />                                    {/* ← and this line */}
    </React.StrictMode>
);

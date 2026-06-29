import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#0f1728",
            color: "#eaf2ff",
            border: "1px solid rgba(156,176,200,0.2)",
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);

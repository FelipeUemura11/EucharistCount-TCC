import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import CapturaDeErros from "./components/CapturaDeErros.tsx";
import { BrowserRouter } from "react-router";

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <CapturaDeErros>
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </CapturaDeErros>
    </React.StrictMode>,
);

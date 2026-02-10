import { Routes, Route, Navigate } from "react-router-dom";
import IntelligenceDashboard from "./pages/IntelligenceDashboard";
import Theory from "./pages/Theory";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<IntelligenceDashboard />} />
      <Route path="/theory" element={<Theory />} />
      <Route path="/intelligence-docs" element={<Theory />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

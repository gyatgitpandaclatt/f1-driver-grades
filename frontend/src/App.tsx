import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./layout/Layout";
import DriverGradesPage from "./pages/DriverGradesPage";
import QualifyingH2HPage from "./pages/QualifyingH2HPage";
import OverperformancePage from "./pages/OverperformancePage";
import GridImprovementPage from "./pages/GridImprovementPage";
import MethodologyPage from "./pages/MethodologyPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DriverGradesPage />} />
          <Route path="/qualifying-h2h" element={<QualifyingH2HPage />} />
          <Route path="/overperformance" element={<OverperformancePage />} />
          <Route path="/grid-improvement" element={<GridImprovementPage />} />
          <Route path="/methodology" element={<MethodologyPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

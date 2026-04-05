import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext.jsx";
import LoginPage from "./pages/Login.jsx";
import UploadPage from "./pages/Upload.jsx";
import ComplaintPage from "./pages/ComplaintPage.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import TopNav from "./components/TopNav.jsx";
import Gallery from "./pages/Gallery.jsx";
import Profile from "./pages/Profile.jsx";
import MyComplaints from "./pages/MyComplaints.jsx";

function RequireAuth({ children, role }) {
  const { token, role: userRole, loading } = useAuth();
  if (loading) return <div className="container">Loading...</div>;
  if (!token) return <Navigate to="/login" replace />;
  if (role && userRole !== role && userRole !== "admin") return <Navigate to="/" replace />;
  return (
    <div className="app-shell">
      <TopNav />
      <div className="app-body">{children}</div>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <UploadPage />
          </RequireAuth>
        }
      />
      <Route
        path="/complaints/:trackingId"
        element={
          <RequireAuth>
            <ComplaintPage />
          </RequireAuth>
        }
      />
      <Route
        path="/gallery"
        element={
          <RequireAuth>
            <Gallery />
          </RequireAuth>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <Profile />
          </RequireAuth>
        }
      />
      <Route
        path="/my-complaints"
        element={
          <RequireAuth>
            <MyComplaints />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth role="admin">
            <AdminDashboard />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}


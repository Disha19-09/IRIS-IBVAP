import { Navigate } from "react-router-dom";

import { getAuthToken } from "../api/api.js";

function ProtectedRoute({ children }) {
  const token = getAuthToken();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;

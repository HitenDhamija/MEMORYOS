"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}

function ProfileContent() {
  const { user, logout, updateProfile, deactivateAccount, isLoading } = useAuth();
  const [editMode, setEditMode] = useState(false);
  const [email, setEmail] = useState(user?.email || "");
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      const updateData: any = {};
      if (email !== user?.email) updateData.email = email;
      if (fullName !== user?.full_name) updateData.full_name = fullName;
      if (password) updateData.password = password;

      if (Object.keys(updateData).length === 0) {
        setMessage("No changes to save");
        return;
      }

      await updateProfile(updateData);
      setPassword("");
      setEditMode(false);
      setMessage("Profile updated successfully");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Update failed");
    }
  };

  const handleDeactivate = async () => {
    if (!confirm("Are you sure you want to deactivate your account? This action cannot be undone.")) {
      return;
    }

    try {
      await deactivateAccount();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Deactivation failed");
    }
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Profile</h1>

      {message && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
          {message}
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Account Information</h2>
          <button
            onClick={() => setEditMode(!editMode)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            {editMode ? "Cancel" : "Edit"}
          </button>
        </div>

        {editMode ? (
          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                New Password (leave blank to keep current)
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition"
            >
              {isLoading ? "Saving..." : "Save Changes"}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Username</p>
              <p className="font-medium">{user.username}</p>
            </div>
            {user.full_name && (
              <div>
                <p className="text-sm text-gray-600">Full Name</p>
                <p className="font-medium">{user.full_name}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p className={`font-medium ${user.is_active ? "text-green-600" : "text-red-600"}`}>
                {user.is_active ? "Active" : "Inactive"}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <button
          onClick={logout}
          className="px-6 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition"
        >
          Logout
        </button>

        <button
          onClick={handleDeactivate}
          className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
        >
          Deactivate Account
        </button>
      </div>
    </div>
  );
}

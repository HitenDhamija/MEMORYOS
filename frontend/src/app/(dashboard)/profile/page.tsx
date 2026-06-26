/**
 * Profile Page - Apple Design Language
 */

"use client";

import { useState, useRef } from "react";
import { useAuth } from "@/hooks/useAuth";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Camera, Loader2 } from "lucide-react";
import authService from "@/services/authService";

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
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api").replace("/api", "");
  
  const getAvatarUrl = (url: string | null | undefined) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    return `${API_BASE}${url}`;
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingAvatar(true);
    setError("");
    try {
      const updated = await authService.uploadAvatar(file);
      setAvatarUrl(getAvatarUrl(updated.avatar_url));
      setMessage("Profile picture updated");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload image");
    } finally {
      setUploadingAvatar(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const updateData: any = {};
      if (email !== user?.email) updateData.email = email;
      if (fullName !== user?.full_name) updateData.full_name = fullName;
      if (password) updateData.password = password;
      if (Object.keys(updateData).length === 0) { setMessage("No changes to save"); return; }
      await updateProfile(updateData);
      setPassword("");
      setEditMode(false);
      setMessage("Profile updated successfully");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Update failed");
    }
  };

  const handleDeactivate = async () => {
    if (!confirm("Are you sure you want to deactivate your account? This action cannot be undone.")) return;
    try { await deactivateAccount(); } catch (err: any) { setError(err.response?.data?.detail || "Deactivation failed"); }
  };

  if (!user) return <div className="apple-tile-light flex items-center justify-center min-h-[60vh]"><p className="text-apple-body text-apple-ink-48">Loading…</p></div>;

  const displayAvatarUrl = avatarUrl || getAvatarUrl((user as any).avatar_url);
  const initials = (user.full_name || user.username || "?").split(" ").map((w: string) => w[0]).join("").substring(0, 2).toUpperCase();

  return (
    <div className="min-h-screen">
      {/* Header - Light Tile */}
      <section className="apple-tile-light">
        <div className="max-w-[980px] mx-auto">
          <h1 className="text-apple-display-lg text-apple-ink">Profile</h1>
        </div>
      </section>

      {/* Content - Parchment Tile */}
      <section className="apple-tile-parchment">
        <div className="max-w-[600px] mx-auto">
          {message && <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-apple-sm text-green-700 text-apple-caption">{message}</div>}
          {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-apple-sm text-red-700 text-apple-caption">{error}</div>}

          {/* Avatar Section */}
          <div className="apple-utility-card mb-6">
            <div className="flex items-center gap-6">
              <div className="relative group">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingAvatar}
                  className="w-20 h-20 rounded-full overflow-hidden bg-gray-100 flex items-center justify-center border-2 border-gray-200 hover:border-blue-400 transition-colors cursor-pointer"
                >
                  {uploadingAvatar ? (
                    <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
                  ) : displayAvatarUrl ? (
                    <img src={displayAvatarUrl} alt="Profile" className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-2xl font-semibold text-gray-500">{initials}</span>
                  )}
                </button>
                <div className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity pointer-events-none">
                  <Camera className="w-5 h-5 text-white" />
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  onChange={handleAvatarUpload}
                  className="hidden"
                />
              </div>
              <div>
                <p className="text-apple-body-strong text-apple-ink">{user.full_name || user.username}</p>
                <p className="text-apple-caption text-apple-ink-48">{user.email}</p>
              </div>
            </div>
          </div>

          <div className="apple-utility-card mb-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-apple-body-strong text-apple-ink">Account Information</h2>
              <button onClick={() => setEditMode(!editMode)} className={editMode ? 'apple-btn-secondary' : 'apple-btn-dark'}>
                {editMode ? "Cancel" : "Edit"}
              </button>
            </div>

            {editMode ? (
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div>
                  <label className="block text-apple-caption-strong text-apple-ink mb-2">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="apple-search-input" disabled={isLoading} />
                </div>
                <div>
                  <label className="block text-apple-caption-strong text-apple-ink mb-2">Full Name</label>
                  <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className="apple-search-input" disabled={isLoading} />
                </div>
                <div>
                  <label className="block text-apple-caption-strong text-apple-ink mb-2">New Password <span className="text-apple-ink-48 font-normal">(leave blank to keep current)</span></label>
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} className="apple-search-input" placeholder="••••••••" disabled={isLoading} />
                </div>
                <button type="submit" disabled={isLoading} className="apple-btn-primary w-full disabled:opacity-50">
                  {isLoading ? "Saving…" : "Save Changes"}
                </button>
              </form>
            ) : (
              <div className="space-y-4">
                {[
                  { label: "Email", value: user.email },
                  { label: "Username", value: user.username },
                  ...(user.full_name ? [{ label: "Full Name", value: user.full_name }] : []),
                  { label: "Status", value: user.is_active ? "Active" : "Inactive" },
                ].map((field, i) => (
                  <div key={i}>
                    <p className="text-apple-caption text-apple-ink-48">{field.label}</p>
                    <p className="text-apple-body-strong text-apple-ink">{field.value}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-4">
            <button onClick={logout} className="apple-btn-secondary flex-1">Logout</button>
            <button onClick={handleDeactivate} className="apple-btn-secondary flex-1 text-red-600 border-red-300 hover:bg-red-50">Deactivate Account</button>
          </div>
        </div>
      </section>
    </div>
  );
}

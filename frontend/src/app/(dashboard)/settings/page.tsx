/**
 * Settings Page - Apple Design Language
 * Font size, accent color, notifications
 */

'use client';

import React, { useState } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useSettings } from '@/context/SettingsContext';
import { useAuth } from '@/hooks/useAuth';
import { Palette, Bell, BellOff, LogOut, Globe } from 'lucide-react';

type SettingsTab = 'appearance' | 'notifications' | 'about';

const ACCENT_COLORS = [
  { name: 'Blue', value: '#007AFF' },
  { name: 'Purple', value: '#AF52DE' },
  { name: 'Pink', value: '#FF2D55' },
  { name: 'Red', value: '#FF3B30' },
  { name: 'Orange', value: '#FF9500' },
  { name: 'Yellow', value: '#FFCC00' },
  { name: 'Green', value: '#34C759' },
  { name: 'Teal', value: '#30B0C7' },
  { name: 'Indigo', value: '#5856D6' },
  { name: 'Gray', value: '#8E8E93' },
];

export default function SettingsPage() {
  const { settings, updateSettings } = useSettings();
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('appearance');

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-sm text-gray-500 mt-1">Customize your experience</p>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl border border-gray-200 p-2 sticky top-24">
                <nav className="space-y-1">
                  {[
                    { id: 'appearance' as SettingsTab, label: 'Appearance', icon: Palette },
                    { id: 'notifications' as SettingsTab, label: 'Notifications', icon: Bell },
                    { id: 'about' as SettingsTab, label: 'About', icon: Globe },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium flex items-center gap-3 transition-colors ${
                          activeTab === tab.id
                            ? 'bg-blue-50 text-blue-600'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        <Icon size={18} />
                        {tab.label}
                      </button>
                    );
                  })}
                </nav>
                <hr className="my-3 border-gray-100" />
                <button onClick={logout} className="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors">
                  <LogOut size={18} />
                  Log Out
                </button>
              </div>
            </div>

            {/* Settings Panels */}
            <div className="lg:col-span-3 space-y-6">
              {/* Appearance Tab */}
              {activeTab === 'appearance' && (
                <>
                  {/* Font Size */}
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h2 className="text-base font-semibold text-gray-900 mb-4">Font Size</h2>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'small' as const, label: 'Small', size: '13px' },
                        { value: 'medium' as const, label: 'Medium', size: '15px' },
                        { value: 'large' as const, label: 'Large', size: '18px' },
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => updateSettings({ fontSize: option.value })}
                          className={`p-4 rounded-xl border-2 text-center transition-all ${
                            settings.fontSize === option.value
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <span style={{ fontSize: option.size }} className="block font-semibold text-gray-900">Aa</span>
                          <p className="text-sm font-medium text-gray-900 mt-2">{option.label}</p>
                          <p className="text-xs text-gray-500">{option.size}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Accent Color */}
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h2 className="text-base font-semibold text-gray-900 mb-4">Accent Color</h2>
                    <div className="flex flex-wrap gap-3">
                      {ACCENT_COLORS.map((color) => (
                        <button
                          key={color.value}
                          onClick={() => updateSettings({ accentColor: color.value })}
                          className={`w-10 h-10 rounded-full transition-all ${
                            settings.accentColor === color.value
                              ? 'ring-2 ring-offset-2 ring-blue-500 scale-110'
                              : 'hover:scale-105'
                          }`}
                          style={{ backgroundColor: color.value }}
                          title={color.name}
                        />
                      ))}
                    </div>
                    <p className="text-xs text-gray-400 mt-3">Changes the color of buttons and highlights throughout the app</p>
                  </div>
                </>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h2 className="text-base font-semibold text-gray-900 mb-4">Notifications</h2>
                  <div className="space-y-4">
                    {[
                      { key: 'reviews' as const, label: 'Review Reminders', desc: 'Get reminded to review memories before you forget' },
                      { key: 'milestones' as const, label: 'Milestones', desc: 'Celebrate when you upload, organize, and learn' },
                      { key: 'discoveries' as const, label: 'Discoveries', desc: 'Notify when AI finds connections between memories' },
                      { key: 'email' as const, label: 'Email Notifications', desc: 'Receive weekly summaries and important updates' },
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-4 rounded-xl border border-gray-100 hover:bg-gray-50 transition-colors">
                        <div className="flex items-center gap-3">
                          {settings.notifications[item.key] ? (
                            <Bell className="w-5 h-5 text-blue-600" />
                          ) : (
                            <BellOff className="w-5 h-5 text-gray-400" />
                          )}
                          <div>
                            <p className="text-sm font-medium text-gray-900">{item.label}</p>
                            <p className="text-xs text-gray-500">{item.desc}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => updateSettings({
                            notifications: { ...settings.notifications, [item.key]: !settings.notifications[item.key] }
                          })}
                          className={`relative w-12 h-7 rounded-full transition-colors ${
                            settings.notifications[item.key] ? 'bg-blue-600' : 'bg-gray-300'
                          }`}
                        >
                          <span className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${
                            settings.notifications[item.key] ? 'translate-x-5' : ''
                          }`} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* About Tab */}
              {activeTab === 'about' && (
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h2 className="text-base font-semibold text-gray-900 mb-4">About MemoryOS</h2>
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-xl">
                      <p className="text-sm text-blue-700 font-medium">AI-Powered Knowledge Operating System</p>
                      <p className="text-xs text-blue-600 mt-1">Upload, organize, and discover knowledge with semantic search and intelligent insights.</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-gray-500">Version</p>
                        <p className="font-medium text-gray-900">1.0.0</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-gray-500">Engine</p>
                        <p className="font-medium text-gray-900">v4.0</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

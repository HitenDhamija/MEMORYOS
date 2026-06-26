/**
 * Settings Context - Manages font size, accent color, notifications
 * Persists to localStorage and applies changes globally
 */

'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface Settings {
  fontSize: 'small' | 'medium' | 'large';
  accentColor: string;
  notifications: {
    reviews: boolean;
    milestones: boolean;
    discoveries: boolean;
    email: boolean;
  };
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (partial: Partial<Settings>) => void;
}

const SETTINGS_KEY = 'memoryos_settings';

const DEFAULTS: Settings = {
  fontSize: 'medium',
  accentColor: '#007AFF',
  notifications: { reviews: true, milestones: true, discoveries: true, email: false },
};

function loadSettings(): Settings {
  if (typeof window === 'undefined') return DEFAULTS;
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) return { ...DEFAULTS, ...JSON.parse(stored) };
  } catch {}
  return DEFAULTS;
}

function applyFontSize(size: Settings['fontSize']) {
  const root = document.documentElement;
  const sizes = { small: '14px', medium: '16px', large: '18px' };
  root.style.fontSize = sizes[size];
}

function applyAccentColor(color: string) {
  const root = document.documentElement;
  root.style.setProperty('--accent-color', color);
}

const SettingsContext = createContext<SettingsContextType>({
  settings: DEFAULTS,
  updateSettings: () => {},
});

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<Settings>(DEFAULTS);

  useEffect(() => {
    setSettings(loadSettings());
  }, []);

  useEffect(() => {
    applyFontSize(settings.fontSize);
    applyAccentColor(settings.accentColor);
  }, [settings.fontSize, settings.accentColor]);

  const updateSettings = useCallback((partial: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...partial };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return (
    <SettingsContext.Provider value={{ settings, updateSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export const useSettings = () => useContext(SettingsContext);

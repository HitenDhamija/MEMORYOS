/**
 * Notification Center Component
 * 
 * Beautiful notification panel with multiple notification types and actions.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { X, Bell, AlertCircle, CheckCircle, Zap, Bookmark } from 'lucide-react';
import { insightsService } from '@/services/insightsService';

export type NotificationType = 'review_reminder' | 'milestone' | 'discovery' | 'collection' | 'streak';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: 'high' | 'medium' | 'low';
  timestamp?: Date;
  read?: boolean;
  actionUrl?: string;
  actionLabel?: string;
}

const notificationConfig: { [key in NotificationType]: { icon: React.ReactNode; bgColor: string; accentColor: string } } = {
  review_reminder: {
    icon: <AlertCircle size={20} />,
    bgColor: 'bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800',
    accentColor: 'text-orange-600 dark:text-orange-400',
  },
  milestone: {
    icon: <Zap size={20} />,
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/30 border-yellow-200 dark:border-yellow-800',
    accentColor: 'text-yellow-600 dark:text-yellow-400',
  },
  discovery: {
    icon: <CheckCircle size={20} />,
    bgColor: 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800',
    accentColor: 'text-green-600 dark:text-green-400',
  },
  collection: {
    icon: <Bookmark size={20} />,
    bgColor: 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800',
    accentColor: 'text-blue-600 dark:text-blue-400',
  },
  streak: {
    icon: <Zap size={20} />,
    bgColor: 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800',
    accentColor: 'text-red-600 dark:text-red-400',
  },
};

export const NotificationItem: React.FC<{
  notification: Notification;
  onDismiss: (id: string) => void;
}> = ({ notification, onDismiss }) => {
  const config = notificationConfig[notification.type];

  return (
    <div className={`border rounded-lg p-4 ${config.bgColor} animate-slideIn`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 ${config.accentColor} mt-0.5`}>
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
            {notification.title}
          </h3>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
            {notification.message}
          </p>
          {notification.actionUrl && (
            <a
              href={notification.actionUrl}
              className={`text-sm font-semibold ${config.accentColor} hover:underline`}
            >
              {notification.actionLabel || 'View'}
            </a>
          )}
        </div>
        <button
          onClick={() => onDismiss(notification.id)}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          aria-label="Dismiss notification"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
};

export const NotificationCenter: React.FC<{
  isOpen: boolean;
  onClose: () => void;
}> = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const data = await insightsService.getNotifications();
      setNotifications(data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Notification panel */}
      <div
        className={`
          fixed right-0 top-0 h-screen w-full max-w-md bg-white dark:bg-gray-900
          shadow-2xl z-50 transition-transform duration-300 overflow-hidden flex flex-col
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Notifications
            {unreadCount > 0 && (
              <span className="ml-2 inline-block px-3 py-1 bg-red-500 text-white text-sm rounded-full font-bold">
                {unreadCount}
              </span>
            )}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
            aria-label="Close notifications"
          >
            <X size={24} className="text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-6 text-center">
              <div className="animate-spin inline-block">
                <Bell className="w-8 h-8 text-blue-600" />
              </div>
              <p className="text-gray-600 dark:text-gray-400 mt-2">Loading notifications...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-6 text-center">
              <Bell className="w-12 h-12 text-gray-400 mx-auto mb-4 opacity-50" />
              <p className="text-gray-600 dark:text-gray-400">No notifications yet</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                You're all caught up!
              </p>
            </div>
          ) : (
            <div className="p-6 space-y-4">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onDismiss={handleDismiss}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-800">
            <button
              onClick={() => {
                setNotifications([]);
                onClose();
              }}
              className="w-full py-2 px-4 bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-semibold rounded-lg transition"
            >
              Clear All
            </button>
          </div>
        )}
      </div>
    </>
  );
};

/**
 * Notification Bell Icon Button (for header)
 */
export const NotificationBell: React.FC<{
  onClick: () => void;
  unreadCount?: number;
}> = ({ onClick, unreadCount = 0 }) => (
  <button
    onClick={onClick}
    className="relative p-3 rounded-lg bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition shadow-sm"
    aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
  >
    <Bell size={20} className="text-gray-600 dark:text-gray-400" />
    {unreadCount > 0 && (
      <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
        {unreadCount > 9 ? '9+' : unreadCount}
      </span>
    )}
  </button>
);

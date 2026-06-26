/**
 * Dialog - Apple Design Language
 */

'use client';

import React, { useEffect, useState } from 'react';
import clsx from 'clsx';
import { X } from 'lucide-react';

interface DialogProps {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  const [isOpen, setIsOpen] = useState(open);
  useEffect(() => { setIsOpen(open); }, [open]);
  const handleClose = () => { setIsOpen(false); onOpenChange?.(false); };

  return (
    <DialogContext.Provider value={{ isOpen, onClose: handleClose }}>
      {isOpen && (
        <>
          <button className="fixed inset-0 z-40 bg-black/50 transition-opacity" onClick={handleClose} aria-label="Close dialog" tabIndex={-1} />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">{children}</div>
        </>
      )}
    </DialogContext.Provider>
  );
};

const DialogContext = React.createContext<{ isOpen: boolean; onClose: () => void } | null>(null);

export const useDialog = () => {
  const context = React.useContext(DialogContext);
  if (!context) throw new Error('useDialog must be used within Dialog');
  return context;
};

interface DialogContentProps { children: React.ReactNode; className?: string; }

export const DialogContent: React.FC<DialogContentProps> = ({ children, className }) => {
  const { onClose } = useDialog();
  return (
    <div role="dialog" aria-modal="true" className={clsx('bg-white rounded-apple-lg shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto', className)} onClick={(e) => e.stopPropagation()}>
      <div className="relative">
        <button onClick={onClose} className="absolute right-4 top-4 p-1 hover:bg-apple-parchment rounded-apple-sm transition-colors" aria-label="close dialog">
          <X className="w-5 h-5 text-apple-ink-48" />
        </button>
        {children}
      </div>
    </div>
  );
};

interface DialogHeaderProps { children: React.ReactNode; className?: string; }
export const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className }) => (
  <div className={clsx('px-6 pt-6 pb-4', className)}>{children}</div>
);

interface DialogTitleProps { children: React.ReactNode; className?: string; }
export const DialogTitle: React.FC<DialogTitleProps> = ({ children, className }) => (
  <h2 className={clsx('text-apple-display-md text-apple-ink', className)}>{children}</h2>
);

interface DialogDescriptionProps { children: React.ReactNode; className?: string; }
export const DialogDescription: React.FC<DialogDescriptionProps> = ({ children, className }) => (
  <p className={clsx('text-apple-caption text-apple-ink-48 mt-1', className)}>{children}</p>
);

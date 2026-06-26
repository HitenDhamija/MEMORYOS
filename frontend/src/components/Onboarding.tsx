/**
 * Onboarding Components - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import { X, ArrowRight, CheckCircle, Zap, Brain, BarChart3 } from 'lucide-react';

interface OnboardingStep {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  tips: string[];
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: 1,
    title: 'Upload Your Knowledge',
    description: 'Start by uploading PDFs, documents, notes, or images. MemoryOS will process and organize everything for you.',
    icon: <ArrowRight className="w-10 h-10 text-apple-blue" />,
    tips: ['Upload any file type - PDFs, Word docs, images, and more', 'Supported formats: PDF, DOCX, TXT, PNG, JPG', 'Drag and drop to upload quickly'],
  },
  {
    id: 2,
    title: 'Search Semantically',
    description: 'Use natural language to search. Ask questions instead of keywords - MemoryOS understands meaning.',
    icon: <Brain className="w-10 h-10 text-apple-blue" />,
    tips: ['Try natural language queries', 'Search across all your memories instantly', 'Discover connections you didn\'t know existed'],
  },
  {
    id: 3,
    title: 'Organize with Collections',
    description: 'Create collections to group related memories. Track progress and stay organized.',
    icon: <BarChart3 className="w-10 h-10 text-apple-blue" />,
    tips: ['Create custom collections for different subjects', 'Add memories to multiple collections', 'Track your learning progress'],
  },
  {
    id: 4,
    title: 'Get AI Insights',
    description: 'MemoryOS analyzes your learning patterns and provides personalized recommendations.',
    icon: <Zap className="w-10 h-10 text-apple-blue" />,
    tips: ['Check your dashboard for weekly insights', 'See trending topics and learning patterns', 'Get reminders to review forgotten memories'],
  },
];

export interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

export function OnboardingModal({ isOpen, onClose, onComplete }: OnboardingModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  if (!isOpen) return null;
  const step = onboardingSteps[currentStep];
  const isLastStep = currentStep === onboardingSteps.length - 1;

  const handleNext = () => {
    if (isLastStep) { onComplete(); onClose(); } else { setCurrentStep(currentStep + 1); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div role="dialog" aria-modal="true" aria-label="Onboarding" className="bg-white rounded-apple-lg shadow-2xl max-w-lg w-full overflow-hidden">
        <div className="flex items-center justify-between px-8 py-5 border-b border-apple-hairline">
          <h2 className="text-apple-display-md text-apple-ink">Welcome to MemoryOS</h2>
          <button onClick={onClose} className="text-apple-ink-48 hover:text-apple-ink" aria-label="Close onboarding"><X size={24} /></button>
        </div>
        <div className="px-8 py-8">
          <div className="text-center mb-6">
            <div className="flex justify-center mb-4">{step.icon}</div>
            <h3 className="text-apple-display-md text-apple-ink mb-2">{step.title}</h3>
            <p className="text-apple-body text-apple-ink-48">{step.description}</p>
          </div>
          <div className="bg-apple-parchment rounded-apple-sm p-5 space-y-3 mb-6">
            {step.tips.map((tip, index) => (
              <div key={index} className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-apple-blue flex-shrink-0 mt-0.5" />
                <p className="text-apple-caption text-apple-ink">{tip}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 justify-center mb-4">
            {onboardingSteps.map((_, index) => (
              <div key={index} className={`h-1.5 rounded-full ${index <= currentStep ? 'bg-apple-blue' : 'bg-apple-hairline'}`} style={{ width: '40px' }} />
            ))}
          </div>
          <p className="text-center text-apple-fine-print text-apple-ink-48">Step {currentStep + 1} of {onboardingSteps.length}</p>
        </div>
        <div className="px-8 py-5 border-t border-apple-hairline flex items-center justify-between">
          <button onClick={() => currentStep > 0 && setCurrentStep(currentStep - 1)} disabled={currentStep === 0} className="text-apple-body text-apple-ink-48 hover:text-apple-ink disabled:opacity-50">Previous</button>
          <div className="flex gap-3">
            <button onClick={onClose} className="apple-btn-secondary">Skip</button>
            <button onClick={handleNext} className="apple-btn-primary flex items-center gap-2">
              {isLastStep ? 'Get Started' : 'Next'} <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function useOnboarding() {
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [hasShownModal, setHasShownModal] = useState(false);
  useEffect(() => {
    const stored = localStorage.getItem('onboarding_completed');
    setIsOnboarded(!!stored);
  }, []);
  const completeOnboarding = () => { localStorage.setItem('onboarding_completed', 'true'); setIsOnboarded(true); };
  const showModal = () => { setHasShownModal(true); };
  return { isOnboarded, hasShownModal, completeOnboarding, showModal };
}

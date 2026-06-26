/**
 * MemoryOS Landing Page - Apple Design Language
 *
 * Edge-to-edge product tiles, alternating light/dark canvases,
 * single blue accent, pill CTAs, no decorative gradients.
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Brain, Search, Zap, Lock, TrendingUp, BarChart3 } from 'lucide-react';

const features = [
  {
    icon: <Search className="w-7 h-7" />,
    title: 'Semantic Search',
    description: 'Find memories using natural language. No keyword matching needed.',
  },
  {
    icon: <Brain className="w-7 h-7" />,
    title: 'AI Insights',
    description: 'Get intelligent suggestions about your knowledge and learning patterns.',
  },
  {
    icon: <Zap className="w-7 h-7" />,
    title: 'Learning Streaks',
    description: 'Track your daily learning activity and celebrate milestones.',
  },
  {
    icon: <TrendingUp className="w-7 h-7" />,
    title: 'Knowledge Evolution',
    description: 'Watch your expertise grow and visualize learning over time.',
  },
  {
    icon: <Lock className="w-7 h-7" />,
    title: 'Privacy First',
    description: 'Your data is encrypted and never shared with third parties.',
  },
  {
    icon: <BarChart3 className="w-7 h-7" />,
    title: 'Collections',
    description: 'Organize memories into smart collections with progress tracking.',
  },
];

const steps = [
  { number: '1', title: 'Upload', description: 'Add PDFs, documents, images, and notes. MemoryOS extracts and processes everything.', icon: '📤' },
  { number: '2', title: 'Process', description: 'AI analyzes content, extracts topics, and creates embeddings for semantic search.', icon: '⚙️' },
  { number: '3', title: 'Discover', description: 'Find related memories instantly. Uncover connections you never knew existed.', icon: '🔍' },
  { number: '4', title: 'Track', description: 'Monitor your learning journey with streaks, milestones, and insights.', icon: '📊' },
];

export default function LandingPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleCTA = (href: string) => {
    setIsLoading(true);
    setTimeout(() => {
      window.location.href = href;
    }, 200);
  };

  return (
    <div className="min-h-screen">
      {/* Global Nav - Apple style black bar */}
      <nav className="apple-global-nav sticky top-0 z-50">
        <div className="max-w-[1440px] w-full mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-apple-body-dark" />
              <span className="text-[14px] font-semibold text-apple-body-dark tracking-tight">
                MemoryOS
              </span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-apple-body-dark/80 hover:text-apple-body-dark transition-colors text-[12px]">
                Features
              </a>
              <a href="#how-it-works" className="text-apple-body-dark/80 hover:text-apple-body-dark transition-colors text-[12px]">
                How It Works
              </a>
              <a href="#pricing" className="text-apple-body-dark/80 hover:text-apple-body-dark transition-colors text-[12px]">
                Pricing
              </a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-apple-body-dark/80 hover:text-apple-body-dark transition-colors text-[12px] hidden md:block">
              Sign In
            </Link>
            <button
              onClick={() => handleCTA('/register')}
              disabled={isLoading}
              className="apple-btn-primary text-[12px] px-4 py-1.5 disabled:opacity-50"
            >
              Get Started Free
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Tile - Light */}
      <section className="apple-tile-light text-center">
        <div className="max-w-[980px] mx-auto">
          <h1 className="text-apple-hero text-apple-ink mb-4">
            Your Second Brain,
            <br />
            Powered by AI
          </h1>
          <p className="text-apple-lead text-apple-ink-48 mb-8 max-w-[600px] mx-auto">
            Upload, organize, and discover knowledge using semantic search and AI-powered insights. Never lose important information again.
          </p>
          <div className="flex items-center justify-center gap-4 mb-6">
            <button
              onClick={() => handleCTA('/register')}
              disabled={isLoading}
              className="apple-btn-primary text-apple-btn-lg px-7 py-3.5 disabled:opacity-50"
            >
              Start Free Trial
            </button>
            <Link href="/demo" className="apple-btn-secondary text-apple-btn-lg px-7 py-3.5">
              Try Demo
            </Link>
          </div>
          <p className="text-apple-fine-print text-apple-ink-48">
            Free to start · No credit card needed · 100GB storage included
          </p>
        </div>
      </section>

      {/* Features Tile - Parchment */}
      <section id="features" className="apple-tile-parchment">
        <div className="max-w-[980px] mx-auto text-center">
          <h2 className="text-apple-display-lg text-apple-ink mb-4">
            Powerful Features
          </h2>
          <p className="text-apple-lead text-apple-ink-48 mb-16">
            Everything you need to manage and discover knowledge
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="apple-utility-card text-left"
              >
                <div className="text-apple-blue mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-apple-body-strong text-apple-ink mb-2">
                  {feature.title}
                </h3>
                <p className="text-apple-body text-apple-ink-48">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Tile - Light */}
      <section id="how-it-works" className="apple-tile-light">
        <div className="max-w-[980px] mx-auto">
          <h2 className="text-apple-display-lg text-apple-ink text-center mb-16">
            How MemoryOS Works
          </h2>

          <div className="space-y-16">
            {steps.map((step, index) => (
              <div key={index} className="flex gap-12 items-start">
                <div className="flex-shrink-0">
                  <div className="text-4xl mb-2">{step.icon}</div>
                  <div className="text-apple-fine-print text-apple-ink-48 text-center">
                    Step {step.number}
                  </div>
                </div>
                <div>
                  <h3 className="text-apple-display-md text-apple-ink mb-2">
                    {step.title}
                  </h3>
                  <p className="text-apple-body text-apple-ink-48 max-w-[600px]">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Capabilities Tile - Dark */}
      <section className="apple-tile-dark text-center">
        <div className="max-w-[980px] mx-auto">
          <h2 className="text-apple-display-lg text-apple-body-dark mb-4">
            Powered by Advanced AI
          </h2>
          <p className="text-apple-lead text-apple-muted mb-16 max-w-[600px] mx-auto">
            State-of-the-art embeddings and semantic search to understand your knowledge, not just keywords.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { label: 'Semantic Search', desc: 'Understand meaning, not just words', icon: '🧠' },
              { label: 'Smart Topics', desc: 'Automatically categorize your knowledge', icon: '📊' },
              { label: 'Learning Insights', desc: 'Personalized recommendations', icon: '💡' },
            ].map((item, index) => (
              <div
                key={index}
                className="p-apple-xl text-left"
              >
                <div className="text-3xl mb-4">{item.icon}</div>
                <h3 className="text-apple-body-strong text-apple-body-dark mb-2">
                  {item.label}
                </h3>
                <p className="text-apple-body text-apple-muted">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Tile - Parchment */}
      <section id="pricing" className="apple-tile-parchment">
        <div className="max-w-[980px] mx-auto text-center">
          <h2 className="text-apple-display-lg text-apple-ink mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-apple-lead text-apple-ink-48 mb-16">
            Start free, scale as you grow
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                name: 'Starter',
                price: 'Free',
                desc: 'Perfect to get started',
                features: ['5GB storage', '100 memories', 'Semantic search', 'Basic insights'],
                featured: false,
              },
              {
                name: 'Professional',
                price: '$9',
                period: '/month',
                desc: 'For serious learners',
                features: ['100GB storage', 'Unlimited memories', 'Advanced insights', 'Collections', 'Learning streaks', 'Email support'],
                featured: true,
              },
              {
                name: 'Enterprise',
                price: 'Custom',
                desc: 'For teams',
                features: ['Unlimited storage', 'Team collaboration', 'Advanced analytics', 'Custom integrations', 'Priority support'],
                featured: false,
              },
            ].map((plan, index) => (
              <div
                key={index}
                className={`apple-utility-card text-left ${
                  plan.featured ? 'border-apple-blue border-2' : ''
                }`}
              >
                {plan.featured && (
                  <div className="text-apple-caption-strong text-apple-blue mb-2">
                    MOST POPULAR
                  </div>
                )}
                <h3 className="text-apple-display-md text-apple-ink mb-1">
                  {plan.name}
                </h3>
                <div className="mb-4">
                  <span className="text-apple-hero text-apple-ink">{plan.price}</span>
                  {plan.period && (
                    <span className="text-apple-body text-apple-ink-48">{plan.period}</span>
                  )}
                </div>
                <p className="text-apple-body text-apple-ink-48 mb-6">{plan.desc}</p>
                <button
                  onClick={() => handleCTA('/register')}
                  className={`w-full mb-6 ${
                    plan.featured ? 'apple-btn-primary' : 'apple-btn-secondary'
                  }`}
                >
                  Get Started
                </button>
                <ul className="space-y-3">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="text-apple-caption text-apple-ink-48 flex items-center gap-2">
                      <span className="text-apple-blue">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Tile - Dark */}
      <section className="apple-tile-dark-2 text-center">
        <div className="max-w-[600px] mx-auto">
          <h2 className="text-apple-display-lg text-apple-body-dark mb-4">
            Ready to Transform Your Knowledge?
          </h2>
          <p className="text-apple-lead text-apple-muted mb-8">
            Join thousands of learners who never lose important information again.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => handleCTA('/register')}
              disabled={isLoading}
              className="apple-btn-primary text-apple-btn-lg px-7 py-3.5 disabled:opacity-50"
            >
              Start Free Trial
            </button>
            <Link href="/demo" className="apple-btn-secondary text-apple-btn-lg px-7 py-3.5">
              Try Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer - Apple style */}
      <footer className="apple-footer">
        <div className="max-w-[980px] mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div>
              <h4 className="apple-footer-heading">Product</h4>
              <div>
                <a href="#features" className="apple-footer-link">Features</a>
                <a href="#pricing" className="apple-footer-link">Pricing</a>
                <a href="/demo" className="apple-footer-link">Demo</a>
              </div>
            </div>
            <div>
              <h4 className="apple-footer-heading">Company</h4>
              <div>
                <a href="#" className="apple-footer-link">About</a>
                <a href="#" className="apple-footer-link">Blog</a>
                <a href="#" className="apple-footer-link">Contact</a>
              </div>
            </div>
            <div>
              <h4 className="apple-footer-heading">Legal</h4>
              <div>
                <a href="#" className="apple-footer-link">Privacy</a>
                <a href="#" className="apple-footer-link">Terms</a>
              </div>
            </div>
            <div>
              <h4 className="apple-footer-heading">Follow</h4>
              <div>
                <a href="#" className="apple-footer-link">Twitter</a>
                <a href="#" className="apple-footer-link">GitHub</a>
              </div>
            </div>
          </div>
          <div className="border-t border-apple-hairline pt-6">
            <p className="text-apple-fine-print text-apple-ink-48 text-center">
              Copyright © 2026 MemoryOS. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

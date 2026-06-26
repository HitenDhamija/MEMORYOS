/**
 * Button - Apple Design Language
 */

import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading = false, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-apple-pill transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-apple-blue';

    const variants: Record<string, string> = {
      primary: 'apple-btn-primary',
      secondary: 'apple-btn-secondary',
      outline: 'apple-btn-secondary',
      ghost: 'text-apple-ink hover:bg-apple-parchment focus:ring-apple-blue',
    };

    const sizes: Record<string, string> = {
      sm: 'px-[14px] py-[6px] text-[14px]',
      md: 'px-[22px] py-[11px] text-[17px]',
      lg: 'px-[30px] py-[14px] text-[18px]',
    };

    return (
      <button ref={ref} disabled={disabled || isLoading} className={clsx(baseStyles, variants[variant], sizes[size], disabled || isLoading ? 'opacity-50 cursor-not-allowed' : '', className)} {...props}>
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading…
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;

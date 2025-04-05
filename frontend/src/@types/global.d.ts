import React from 'react';

declare global {
  // Extend the Window interface
  interface Window {
    // Add any global window properties if needed
  }

  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

// Fix module declaration errors
declare module 'react' {
  interface ReactNode {}
  export = React;
}

declare module 'next/link';
declare module 'next/font/google';
declare module 'next';
declare module 'next-themes';
declare module 'next-themes/dist/types';
declare module 'lucide-react';
declare module '@radix-ui/react-slot';
declare module 'class-variance-authority';
declare module 'clsx';
declare module 'tailwind-merge';

// Make TypeScript treat this as a module
export {}; 
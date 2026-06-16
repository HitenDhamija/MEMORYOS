# MemoryOS - Frontend

AI-powered personal knowledge operating system. Built with Next.js, TypeScript, Tailwind CSS, and Shadcn.

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: Shadcn/UI
- **State Management**: Zustand
- **Form Handling**: React Hook Form + Zod
- **HTTP Client**: Axios

## Project Structure

```
src/
├── app/                  # Next.js app directory
│   ├── (auth)/          # Auth routes group (login, register)
│   ├── (dashboard)/     # Protected routes group
│   │   ├── dashboard    # Main dashboard
│   │   ├── upload       # Upload interface
│   │   ├── search       # Search interface
│   │   └── profile      # User profile
│   └── api/             # Next.js API routes (optional)
├── components/          # Reusable components
│   ├── ui/              # Shadcn UI components
│   ├── layout/          # Layout components
│   └── forms/           # Form components
├── services/            # API services
│   ├── apiClient.ts     # Axios instance with interceptors
│   ├── authService.ts   # Auth API calls
│   └── memoryService.ts # Memory API calls
├── hooks/               # Custom React hooks
│   └── useAuth.ts       # Authentication hook
├── context/             # State management
│   └── authStore.ts     # Zustand auth store
├── types/               # TypeScript types
├── lib/                 # Utilities and helpers
├── middleware.ts        # Next.js middleware
└── public/              # Static assets
```

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Update with your API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Development

```bash
npm run dev
```

Visit http://localhost:3000

### Build

```bash
npm run build
npm start
```

## Key Features

### Authentication Flow

1. User registers via `/register`
2. User logs in via `/login`
3. JWT token stored in cookies
4. Protected routes via middleware
5. Automatic redirect on 401 responses

### API Integration

- Centralized API client with interceptors
- Automatic token injection in requests
- Error handling and token refresh logic
- Service layer for each domain (auth, memory, etc.)

### State Management

- Zustand for authentication state
- Hooks for component-level state
- Custom hooks for authentication logic

## Component Structure

- **Page Components**: Route-specific components in `app/`
- **Layout Components**: Navigation, sidebars in `components/layout/`
- **UI Components**: Reusable Shadcn components in `components/ui/`
- **Form Components**: Specialized form components in `components/forms/`

## Next Steps

1. Install Shadcn components as needed
2. Implement form components with validation
3. Add search functionality
4. Implement file upload
5. Add memory management UI

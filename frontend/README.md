# HedgeFundAI Frontend

Modern UI for HedgeFundAI - algorithmic trading platform with AI-powered analytics.

## Features

- **Dashboard** with portfolio metrics and analytics
- **Asset Universe Table** with all available tickers and scoring
- **Portfolio Management** with current and target allocation comparison
- **AI Reasoning** for investment theses on specific tickers
- **Rebalancing** capabilities with history tracking

## Tech Stack

- **React** with Next.js framework
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Recharts** for data visualization

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start
```

### Environment Variables

Create a `.env.local` file in the root directory with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── app/            # Next.js app router pages
│   ├── components/     # React components
│   │   ├── ui/         # shadcn UI components
│   │   └── ...         # App-specific components
│   ├── lib/            # Utility functions
│   ├── @types/         # TypeScript type definitions
│   ├── styles/         # Global styles
│   └── ...
├── package.json
└── ...
```

## Connecting to Backend

The frontend connects to the HedgeFundAI backend API for:
- Fetching market data
- Portfolio management
- AI reasoning and analytics
- Executing trades through Alpaca

## Screenshots

![Dashboard](https://example.com/dashboard.png)
![Portfolio](https://example.com/portfolio.png)

## Design Principles

- Clean, modern interface with focus on data visibility
- Light theme with subtle shadows and rounded corners
- Responsive design for all screen sizes
- Consistent spacing and typographic hierarchy

## License

This project is proprietary. All rights reserved. 
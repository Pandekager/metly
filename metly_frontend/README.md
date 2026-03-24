# Metly Frontend

A modern, sleek web application built with Nuxt 4 and Tailwind CSS, inspired by clean design aesthetics with Metly's brand colors.

## Features

- **Modern UI/UX**: Clean, modern interface inspired by Tiptap.dev
- **Landing Page**: Hero section, features, about, and contact sections
- **Authentication**: JWT-based login system with cookie storage
- **Dashboard**: Data visualization with Chart.js
- **AI Insights**: Display AI-generated business recommendations
- **Responsive Design**: Fully responsive across all devices

## Tech Stack

- **Framework**: Nuxt 4 (Vue 3)
- **Styling**: Tailwind CSS
- **State Management**: Pinia
- **Charts**: Chart.js + vue-chartjs
- **Icons**: Heroicons
- **Fonts**: Google Fonts (Montserrat, Leckerli One)
- **Markdown**: marked (for AI responses)

## Getting Started

### Prerequisites

- Node.js ^18.0.0
- pnpm package manager

### Installation

1. Clone the repository and navigate to the project:

```bash
cd Work/metly_frontend
```

2. Install dependencies:

```bash
pnpm install
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Configure your environment variables in `.env`:

```
JWT_SECRET=your-secret-key-change-this
API_BASE=http://localhost:8000/api
NODE_ENV=development
```

### Development

Run the development server:

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
pnpm build
```

Preview the production build:

```bash
pnpm preview
```

## Project Structure

```
metly_frontend/
├── app/                    # Nuxt 4 app directory
├── assets/                 # Static assets (CSS, images)
│   └── css/
│       └── main.css
├── components/             # Vue components
│   ├── charts/            # Chart components
│   ├── layout/            # Layout components (Navbar, Footer)
│   └── sections/         # Page sections (Hero, Features, etc.)
├── composables/           # Vue composables
├── layouts/              # Page layouts
├── middleware/           # Route middleware
├── pages/               # Application pages
│   ├── index.vue        # Landing page
│   ├── login.vue        # Login page
│   └── home.vue        # Dashboard
├── public/             # Static files
├── server/             # Server API routes
│   └── api/           # API endpoints
│       └── auth/       # Authentication endpoints
├── stores/             # Pinia stores
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── nuxt.config.ts      # Nuxt configuration
```

## Pages

### `/` - Landing Page
- Hero section with call-to-action
- Feature showcase
- About section with team info
- Contact section

### `/login` - Login Page
- Email/password authentication
- JWT token management
- Loading states and error handling

### `/home` - Dashboard
- Tabbed navigation (Ordrer, Kunder, Produkter)
- Order forecast chart
- AI business recommendations
- Protected route (requires authentication)

## Authentication

The app uses JWT-based authentication:

1. User submits credentials to `/api/auth/login`
2. Backend validates and returns user ID
3. Frontend generates JWT with user ID
4. JWT stored in httpOnly cookie
5. Protected routes check authentication via middleware
6. Logout clears the JWT cookie

## API Integration

The frontend integrates with the backend API:

- `/api/auth/login` - Authenticate user
- `/api/auth/logout` - Logout user
- `/api/forecasts` - Get order forecasts
- `/api/forecast_business_advice` - Get AI recommendations

Configure the backend URL via the `API_BASE` environment variable.

## Design System

### Colors

- **Metly Blue**: Primary color gradient (0ea5e9 → 0284c7)
- **Slate**: Neutral colors for text and backgrounds
- **Green**: Success states and positive indicators
- **Red**: Error states and logout actions

### Typography

- **Primary**: Montserrat (300, 400, 500, 600, 700)
- **Display**: Leckerli One

### Components

- **btn-primary**: Primary action button with Metly blue gradient
- **btn-secondary**: Secondary outline button
- **card**: White card with shadow and hover effect
- **input-field**: Form input with focus ring

## License

Private project.

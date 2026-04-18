# Django Applications

This directory contains all Django applications for the platform.

## Applications

### Core (`apps/core/`)
Main platform functionality including:
- Home page and landing
- User dashboard
- Profile management
- Global navigation
- API endpoints

### Accounts (`apps/accounts/`)
User management and authentication:
- Custom user model with gamification fields
- Registration and login
- Profile management
- Password reset functionality

### Gamification (`apps/gamification/`)
Gamification system features:
- Badge management and categories
- Point system and transactions
- Leaderboards (weekly, monthly, all-time)
- Achievement tracking
- User progress analytics

### Education (`apps/education/`)
Educational content management:
- Environmental topics organization
- Course creation and management
- Student enrollment tracking
- Progress monitoring
- Certificate generation

### Assessments (`apps/assessments/`)
Quiz and assessment engine:
- Quiz creation with multiple question types
- Competitive challenges and contests
- Performance tracking and analytics
- Adaptive assessment features

## Development Guidelines
- Each app follows Django best practices
- Models use proper relationships and constraints
- Views implement proper permissions and security
- Admin interfaces are customized for usability
- APIs follow RESTful conventions

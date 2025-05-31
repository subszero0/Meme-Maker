# Legal Compliance Documentation

## Overview

Meme Maker includes comprehensive legal compliance features to ensure proper user agreement to terms and privacy protection. This includes static legal pages and mandatory terms acceptance in the job creation flow.

## Legal Pages

### Terms of Use (`/terms`)
- **Location**: `frontend/public/terms.html`
- **Purpose**: Outlines user responsibilities, service limits, and legal disclaimers
- **Key Sections**:
  - Service description and supported platforms
  - User responsibilities and rights requirements
  - Service limits (3 min clips, rate limits)
  - DMCA and intellectual property protections
  - Privacy and data collection overview
  - Service disclaimers and liability limitations

### Privacy Policy (`/privacy`)
- **Location**: `frontend/public/privacy.html`
- **Purpose**: Details data collection, usage, and user privacy rights
- **Key Sections**:
  - Data collection table (IP, URLs, trim settings, metrics)
  - What we don't collect (no personal info, accounts, tracking)
  - Data usage purposes (service delivery, rate limiting, monitoring)
  - Data sharing policies (minimal, only service providers)
  - Security measures (HTTPS, automatic deletion)
  - User rights and contact information

## Link Structure

### Navigation Links
- **Footer**: Links to both `/terms` and `/privacy` on all pages
- **Rights Checkbox**: Terms of Use link in job creation flow
- **Cross-links**: Each legal page links to the other

### URL Routes
- `/terms` → `frontend/public/terms.html`
- `/privacy` → `frontend/public/privacy.html`
- Both pages link back to `/` (homepage)

## API Changes

### Backend Model Updates
- **Field**: Added `accepted_terms: bool` to `JobCreate` model
- **Validation**: Enforces `accepted_terms = true` before job creation
- **Error Response**: HTTP 400 with message "You must accept the Terms of Use to proceed."

### Frontend Interface Updates
- **API Interface**: Updated `JobRequest` to use:
  - `start: string` (hh:mm:ss format) instead of `in: number`
  - `end: string` (hh:mm:ss format) instead of `out: number`
  - `accepted_terms: boolean` instead of `rights: boolean`
- **Transformation**: `formatTimeForAPI()` converts seconds to hh:mm:ss format

## User Flow

1. **URL Input**: User pastes video URL
2. **Metadata Loading**: System fetches video information
3. **Trimming Interface**: User selects start/end times
4. **Terms Acceptance**: User must check "I confirm I have the right to download this content and agree to the Terms of Use"
5. **Job Creation**: API validates `accepted_terms = true` before proceeding
6. **Processing**: Job executes normally if terms accepted

## Implementation Details

### Frontend Components
- **Footer**: `frontend/src/components/Footer.tsx` - Links to legal pages
- **TrimPanel**: Updated checkbox text with Terms of Use link
- **API Client**: Transforms frontend data to backend format

### Backend Validation
- **Models**: `backend/app/models.py` - JobCreate with accepted_terms field
- **API**: `backend/app/api/jobs.py` - Validates terms acceptance before processing

### Static Files
- **Terms**: Self-contained HTML with inline CSS
- **Privacy**: Responsive design with data collection table
- **Versioning**: "Last updated" dates for policy tracking

## Testing Considerations

### Backend Tests
- Test job creation with `accepted_terms = false` → expect HTTP 400
- Test job creation with `accepted_terms = true` → expect success
- Validate error message format matches specification

### Frontend Tests
- Test checkbox disables submit button when unchecked
- Test Terms of Use link opens in new tab
- Test API transformation from frontend to backend format
- Test complete user flow from URL input to job creation

## Maintenance

### Policy Updates
- Update "Last updated" dates when making changes
- Maintain version numbers for tracking
- Consider storing policy markdown in `docs/` for legal team updates
- Ensure consistent styling across both legal pages

### API Compatibility
- Backend expects exact field names: `start`, `end`, `accepted_terms`
- Time format must be `hh:mm:ss` (no milliseconds)
- Any API changes require corresponding frontend updates 